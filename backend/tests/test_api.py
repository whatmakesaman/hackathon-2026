from fastapi.testclient import TestClient

import store
from main import app

client = TestClient(app)
SPAM = "[Web발신] 택배 주소 불일치 확인 http://bit.ly/xxxx"


def test_문자_수신_후_결과를_조회할_수_있다():
    res = client.post("/simulate/incoming", json={"text": SPAM, "sender": "010-0000-0000"})
    assert res.status_code == 200
    body = res.json()
    assert body["level"] == "danger" and body["notified"] is True
    assert body["notification"]["url"] == f"/result/{body['result_id']}"
    # 잠금화면에 원문이 보이지 않도록 알림에는 문자 내용을 넣지 않는다.
    assert "bit.ly" not in body["notification"]["body"]

    result = client.get(f"/result/{body['result_id']}").json()
    assert result["text"] == SPAM and result["result_id"] == body["result_id"]
    assert {"score", "level", "category", "signals", "advice", "if_clicked", "expires_in"} <= result.keys()


def test_analyze는_저장하지_않고_결과만_돌려준다():
    body = client.post("/analyze", json={"text": SPAM}).json()
    assert body.keys() == {"level", "score", "category", "signals", "advice", "if_clicked"}


def test_안전한_문자는_알림을_보내지_않는다():
    body = client.post("/simulate/incoming", json={"text": "내일 7시에 보자"}).json()
    assert body["level"] == "safe" and body["category"] == "정상"
    assert body["notified"] is False and body["notification"] is None


def test_없거나_만료된_결과는_404다(monkeypatch):
    res = client.get("/result/없는id")
    assert res.status_code == 404 and res.json()["detail"] == "결과를 찾을 수 없거나 만료되었어요"
    result_id = client.post("/simulate/incoming", json={"text": SPAM}).json()["result_id"]
    monkeypatch.setattr(store.time, "monotonic", lambda: 10**12)
    assert client.get(f"/result/{result_id}").status_code == 404


def test_입력_검증_실패는_422다():
    assert client.post("/analyze", json={"text": "   "}).status_code == 422
    assert client.post("/analyze", json={"text": "가" * 2001}).status_code == 422


def test_기존_check_API는_한글_등급을_돌려준다():
    body = client.post("/api/check", json={"text": SPAM}).json()
    assert body["level"] == "위험" and body["reasons"]


def test_샘플과_푸시_라우터가_연결되어_있다():
    samples = client.get("/samples").json()
    assert samples and {"id", "label", "text"} <= samples[0].keys()
    assert client.get("/push/vapid-public-key").status_code == 200
