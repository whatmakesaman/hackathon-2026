"""D: 시연/리허설 스크립트 — GET /samples → POST /simulate/incoming 순서대로 전송."""
import time
import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"
INTERVAL = 5  # 샘플 간 대기 시간(초)


def get(path: str) -> object:
    url = BASE_URL + path
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode())


def post(path: str, body: dict) -> object:
    url = BASE_URL + path
    data = json.dumps(body, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def run():
    print(f"[demo] 서버: {BASE_URL}")
    print("[demo] GET /samples 호출 중...")

    try:
        samples = get("/samples")
    except Exception as e:
        print(f"[오류] /samples 호출 실패: {e}")
        print("서버가 실행 중인지 확인하세요: uvicorn main:app --reload")
        sys.exit(1)

    if not samples:
        print("[demo] 샘플이 없습니다. data/demo_samples.json을 확인하세요.")
        sys.exit(0)

    print(f"[demo] 샘플 {len(samples)}개 발견. {INTERVAL}초 간격으로 전송합니다.\n")

    for i, sample in enumerate(samples, 1):
        sid = sample.get("id", f"#{i}")
        label = sample.get("label", "")
        text = sample.get("text", "")
        sender = sample.get("sender", "")

        print(f"[{i}/{len(samples)}] {sid} — {label}")

        body: dict = {"text": text}
        if sender:
            body["sender"] = sender

        try:
            result = post("/simulate/incoming", body)
            level = result.get("level", "?")
            notified = result.get("notified", False)
            rid = result.get("result_id", "")
            notif_icon = "🔔" if notified else "  "
            print(f"  {notif_icon} level={level}  result_id={rid}  notified={notified}")
        except urllib.error.HTTPError as e:
            body_text = e.read().decode()
            print(f"  [오류] HTTP {e.code}: {body_text[:120]}")
        except Exception as e:
            print(f"  [오류] {e}")

        if i < len(samples):
            time.sleep(INTERVAL)

    print("\n[demo] 완료.")


if __name__ == "__main__":
    run()
