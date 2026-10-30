import gzip
import json

import pytest
from fastapi.testclient import TestClient

import main
from analyzer import load_rules
from message_model import (
    MODEL_PATH, analyze_with_model, canonical_text, fit_model,
    load_model, normalization_hash, predict_score, raw_score,
)
from notification import build_notification

RULES, WARNINGS = load_rules(main.RULES_PATH)


def model_at(margin):
    return {
        "prior": margin, "weights": {}, "unknown_weight": 0.0,
        "caution_threshold": 0.0, "danger_threshold": 5.0,
    }


@pytest.mark.parametrize("margin, expected", [
    (-100, "safe"), (-0.01, "safe"), (0, "caution"),
    (4.99, "caution"), (5, "danger"), (100, "danger"),
])
def test_model_score_respects_existing_level_boundaries(margin, expected):
    score, level = predict_score("test", model_at(margin), RULES["levels"])
    assert level == expected and 0 <= score <= 100
    assert (score < 20) == (level == "safe")
    assert (score >= 60) == (level == "danger")


def test_fit_learns_character_counts_without_extra_packages():
    model = fit_model([
        ("내일 저녁 같이 먹자", 0), ("오늘 회의 시간 확인", 0),
        ("비밀번호 상품권 보내줘", 1), ("상품권 번호 보내줘", 1),
    ])
    assert raw_score("상품권 보내줘", model) > raw_score("오늘 회의 시간", model)
    assert canonical_text("인증 1234") == canonical_text("인증 9876")


def test_fit_requires_both_labels():
    with pytest.raises(ValueError):
        fit_model([("일반 문자만 있음", 0)])


def test_model_safe_does_not_inherit_rule_warning():
    result = analyze_with_model("택배 주소 확인 http://bit.ly/test", RULES, model_at(-100))
    assert result["level"] == "safe" and result["category"] == "정상"
    assert result["signals"] == result["advice"] == result["if_clicked"] == []
    assert build_notification(result, "test-id") is None


def test_model_only_warning_does_not_invent_word_highlights():
    result = analyze_with_model("안녕하세요", RULES, model_at(1))
    assert result["level"] == "caution" and result["category"] == "기타 의심"
    assert result["signals"][0]["rule_id"] == "model_pattern"
    assert result["signals"][0]["start"] is None and result["signals"][0]["end"] is None
    assert result["advice"] and result["if_clicked"]


def test_rule_explanations_keep_original_positions():
    text = "엄마 나 폰 고장났어 상품권 보내줘"
    result = analyze_with_model(text, RULES, model_at(10))
    assert result["category"] == "지인 사칭"
    references = result["signals"][1:]
    assert references
    for signal in references:
        assert text[signal["start"]:signal["end"]] == signal["detail"]
        assert signal["explain"].startswith("규칙 참고: ")


def test_missing_or_incompatible_model_reports_startup_problem(tmp_path):
    with pytest.raises(RuntimeError, match="--train"):
        load_model(tmp_path / "missing.json.gz")
    path = tmp_path / "wrong.json.gz"
    path.write_bytes(gzip.compress(json.dumps({"version": 0}).encode()))
    with pytest.raises(ValueError):
        load_model(path)


def test_saved_model_reloads_and_matches_normalizer():
    model = load_model(MODEL_PATH)
    assert model["normalization_hash"] == normalization_hash()
    assert model["training"]["test_metrics"]["spam_total"] > 0
    assert predict_score("상품권 번호 보내줘", model, RULES["levels"]) == predict_score(
        "상품권 번호 보내줘", main.MODEL, RULES["levels"],
    )


@pytest.mark.parametrize("text", ["내일 7시에 보자", "엄마 오늘 저녁 뭐 먹어?", "내일 저녁에 만나자"])
def test_short_normal_conversations_are_not_warned(text):
    result = analyze_with_model(text, RULES, main.MODEL)
    assert result["level"] == "safe"


def test_all_analysis_endpoints_use_the_loaded_model(monkeypatch):
    monkeypatch.setattr(main, "MODEL", model_at(10))
    monkeypatch.setattr(main, "send_to_all", lambda payload: None)
    with TestClient(main.app) as client:
        direct = client.post("/analyze", json={"text": "안녕하세요"})
        assert direct.status_code == 200 and direct.json()["level"] == "danger"
        assert set(direct.json()) == {"score", "level", "category", "signals", "advice", "if_clicked"}
        incoming = client.post("/simulate/incoming", json={"text": "안녕하세요"}).json()
        assert incoming["level"] == "danger" and incoming["notified"] is True
        stored = client.get(f"/result/{incoming['result_id']}").json()
        assert stored["score"] == direct.json()["score"] and stored["text"] == "안녕하세요"
        legacy = client.post("/api/check", json={"text": "안녕하세요"}).json()
        assert legacy["level"] == "위험" and legacy["reasons"]
