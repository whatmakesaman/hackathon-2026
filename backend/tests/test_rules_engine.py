from pathlib import Path

from analyzer import analyze_message, check_rules, load_rules, normalize

RULES_PATH = Path(__file__).resolve().parents[2] / "rules.yaml"
RULES, WARNINGS = load_rules(RULES_PATH)


def test_rules_yaml에_오류가_없다():
    assert WARNINGS == []
    assert check_rules(RULES_PATH) == 0


def test_택배_사칭_문자는_위험이고_유형이_나온다():
    result = analyze_message("[Web발신] 택배 주소 불일치 확인 http://bit.ly/xxxx", RULES)
    assert result["level"] == "danger"
    assert result["category"] == "택배·기관 사칭"
    assert result["advice"] and result["if_clicked"]
    # 알림 문구가 "유형 · 첫 신호"이므로 첫 신호는 유형 규칙이 아닌 공통 신호여야 한다.
    assert result["signals"][0]["rule_id"] in {"url", "short_url"}


def test_유형이_명세서_목록_값으로_나온다():
    allowed = {"지인 사칭", "택배·기관 사칭", "금융·코인 사칭", "지원금·대출", "원격앱 설치 유도", "기타 의심", "정상"}
    texts = ["엄마 나 폰 액정이 깨졌어 문화상품권 보내줘", "카지노 바카라 첫충 30% http://a.top", "OTP 알려줘 즉시 http://a.xyz", "안녕"]
    for text in texts:
        assert analyze_message(text, RULES)["category"] in allowed


def test_일상_문자는_안전이고_대응_안내가_없다():
    result = analyze_message("내일 저녁 7시에 강남역에서 보자", RULES)
    assert result["level"] == "safe"
    assert result["category"] == "정상"
    assert result["signals"] == [] and result["advice"] == [] and result["if_clicked"] == []


def test_점수는_0에서_100_사이다():
    for text in ["!!!", "카지노 바카라 텔레그램: abcd1234 http://a.top 즉시 OTP 앱 설치 문화상품권"]:
        assert 0 <= analyze_message(text, RULES)["score"] <= 100


def test_신호_위치는_원문_글자_기준이다():
    text = "😀😀 택배 확인 http://bit.ly/xxxx"
    for s in analyze_message(text, RULES)["signals"]:
        assert text[s["start"]:s["end"]] == s["detail"]


def test_한글_사이_구분자로_변형해도_잡는다():
    normalized, index = normalize("코-인-원")
    assert normalized == "코인원"
    signals = analyze_message("코-인-원 가입", RULES)["signals"]
    assert any(s["rule_id"] == "finance" and s["detail"] == "코-인-원" for s in signals)


def test_정상_안내_문구는_점수를_깎고_신호_목록에는_없다():
    result = analyze_message("인증번호 482913을 입력해주세요 타인에게 알려주지 마세요", RULES)
    assert all(s["rule_id"] != "otp_notice" for s in result["signals"])
    assert result["level"] == "safe"


def test_잘못된_규칙은_건너뛰고_경고한다(tmp_path):
    bad = tmp_path / "rules.yaml"
    bad.write_text(
        "signals:\n"
        "  - {id: ok, name: 정상, weight: 10, patterns: ['무료']}\n"
        "  - {id: broken, name: 깨짐, weight: 10, patterns: ['(']}\n"
        "  - {id: no_weight, name: 가중치없음, patterns: ['a']}\n",
        encoding="utf-8",
    )
    rules, warnings = load_rules(bad)
    assert [r["id"] for r in rules["signals"]] == ["ok"]
    assert len(warnings) == 2
