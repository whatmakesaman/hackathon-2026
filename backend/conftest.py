import pytest

import url_ai


@pytest.fixture(autouse=True)
def no_real_ai(monkeypatch):
    # 테스트는 .env에 실제 키가 있어도 AI를 호출하지 않는다. (느리고 비용이 들며 결과가 매번 다르다)
    monkeypatch.setattr(url_ai, "_load_api_key", lambda: "")
