import url_ai
from url_ai import apply_ai_verdict, check_urls, find_urls

TEXT = "[CJ대한통운] 주소 불일치로 배송 보류. 확인 http://cj-parcel.top/a1"
SAFE_RESULT = {
    "text": TEXT, "score": 10, "level": "safe", "category": "안전",
    "signals": [], "advice": [], "if_clicked": [],
}


def ai(verdict):
    url = "http://cj-parcel.top/a1"
    start = TEXT.index(url)
    return {"verdict": verdict, "reason": "택배사 공식 주소가 아니에요", "url": url,
            "start": start, "end": start + len(url)}


def test_find_urls_gives_position():
    found = find_urls(TEXT)
    assert found[0]["url"] == "http://cj-parcel.top/a1"
    assert TEXT[found[0]["start"]:found[0]["end"]] == found[0]["url"]


def test_check_urls_skips_without_key(monkeypatch):
    monkeypatch.setattr(url_ai, "_load_api_key", lambda: "")
    assert check_urls(TEXT) is None


def test_check_urls_skips_without_link(monkeypatch):
    monkeypatch.setattr(url_ai, "_load_api_key", lambda: "test-key")
    assert check_urls("오늘 저녁 같이 먹자") is None


def test_no_ai_result_keeps_model_result():
    assert apply_ai_verdict(SAFE_RESULT, None) is SAFE_RESULT


def test_malicious_raises_safe_to_caution_and_keeps_score():
    result = apply_ai_verdict(SAFE_RESULT, ai("malicious"))
    assert result["level"] == "caution"
    assert result["score"] == 10
    assert result["signals"][0]["rule_id"] == "ai_url"
    assert result["advice"] and result["if_clicked"]
    assert SAFE_RESULT["level"] == "safe"  # 원본은 바꾸지 않는다


def test_suspicious_adds_signal_without_raising_level():
    result = apply_ai_verdict(SAFE_RESULT, ai("suspicious"))
    assert result["level"] == "safe"
    assert result["signals"][0]["type"] == "AI 링크 분석: 확인 필요"


def test_safe_verdict_adds_no_signal():
    result = apply_ai_verdict(SAFE_RESULT, ai("safe"))
    assert result["signals"] == []
    assert result["ai_url"]["verdict"] == "safe"
