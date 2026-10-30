from analyzer import analyze, extract_features, train

SPAM = [
    "축하합니다 이벤트에 당첨되셨습니다 상품 수령은 http://bit.ly/3xYz12 클릭",
    "무료 대출 상담 즉시 승인 지금 전화주세요",
    "택배 주소 불일치로 배송이 보류되었습니다 주소 확인 http://kr-parcel.top/a1",
    "무료 상품권 증정 이벤트 지금 클릭하세요",
    "저금리 대출 당일 입금 보장 한도 조회 무료 http://loan-fast.shop/q",
    "카드 결제 승인 해외 결제 본인 아니면 즉시 확인 http://card-check.xyz/9",
]
HAM = [
    "안녕하세요 내일 회의 시간 3시로 변경됐어요 확인 부탁드려요",
    "엄마 오늘 저녁 뭐 먹어? 퇴근하고 들어갈게",
    "인증번호 482913을 입력해주세요 타인에게 알려주지 마세요",
    "오늘 점심 같이 먹을래? 12시 반에 1층에서 보자",
    "주문하신 상품이 출고되었습니다 배송 조회는 앱에서 확인하세요",
    "내일 수업 과제 제출 마감이 금요일이래 잊지 마",
]
WEIGHTS = train(SPAM, HAM)


def test_스팸_문자는_위험으로_판정한다():
    result = analyze("축하합니다 무료 상품권 당첨! 지금 클릭 http://bit.ly/abc", WEIGHTS)
    assert result["level"] == "위험"
    assert result["score"] >= 70


def test_일상_문자는_안전으로_판정한다():
    result = analyze("엄마 오늘 저녁 뭐 먹어?", WEIGHTS)
    assert result["level"] == "안전"
    assert result["score"] < 40


def test_점수는_0에서_100_사이_정수다():
    for text in ["", "무료 대출 클릭 http://a.top", "아무 말", "!!!"]:
        score = analyze(text, WEIGHTS)["score"]
        assert isinstance(score, int)
        assert 0 <= score <= 100


def test_학습에_없는_단어만_있으면_안전이다():
    result = analyze("zzz qqq 햄스터", WEIGHTS)
    assert result["level"] == "안전"
    assert result["reasons"] == []


def test_reasons는_문자에_적힌_단어_문자열_목록이다():
    result = analyze("무료로 대출 지금 클릭 http://loan.top/1", WEIGHTS)
    assert result["reasons"]
    assert all(isinstance(r, str) for r in result["reasons"])
    assert "무료로" in result["reasons"]


def test_링크는_링크_포함으로_표시한다():
    result = analyze("무료 대출 클릭 http://loan.top/1", WEIGHTS)
    assert "링크 포함" in result["reasons"]
    assert "<URL>" not in result["reasons"]


def test_안전이면_reasons는_비어_있다():
    assert analyze("내일 회의 3시에 하자", WEIGHTS)["reasons"] == []


def test_스팸에만_나오는_단어는_양수_정상에만_나오는_단어는_음수_가중치다():
    assert WEIGHTS["무료"] > 0
    assert WEIGHTS["회의"] < 0


def test_Web발신_표시는_분석에서_뺀다():
    assert extract_features("[Web발신] 무료 체험") == extract_features("무료 체험")


def test_한글_조사가_붙어도_같은_단어로_본다():
    assert "무료" in extract_features("무료로 드립니다")
    assert "무료" in extract_features("무료 체험")
