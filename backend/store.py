"""분석 결과 임시 저장소.

사용자가 붙여넣은 문자를 DB나 디스크에 남기지 않으려고 서버 메모리에만 10분 보관한다.
서버를 다시 켜면 모두 사라진다.
"""
import secrets
import threading
import time

TTL_SECONDS = 600

_lock = threading.Lock()
_results = {}  # result_id → (만료 시각, 결과)


def save(result):
    """결과를 보관하고 조회용 id를 돌려준다."""
    # 결과에 문자 원문이 들어 있으므로 다른 사람이 id를 짐작해 열어 보지 못하게 랜덤 값을 쓴다.
    result_id = secrets.token_urlsafe(12)
    now = time.monotonic()
    with _lock:
        _purge(now)
        _results[result_id] = (now + TTL_SECONDS, result)
    return result_id


def get(result_id):
    """보관 중인 결과에 남은 시간(expires_in, 초)을 붙여 돌려준다. 없거나 만료되었으면 None."""
    now = time.monotonic()
    with _lock:
        item = _results.get(result_id)
        if item is None or item[0] <= now:
            _results.pop(result_id, None)
            return None
        expires_at, result = item
    return {**result, "expires_in": int(expires_at - now)}


def _purge(now):
    for result_id in [rid for rid, (expires_at, _) in _results.items() if expires_at <= now]:
        del _results[result_id]
