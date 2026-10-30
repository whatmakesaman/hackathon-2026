"""D: 알림 문구 생성 — 스텁"""


def build_notification(result: dict, result_id: str) -> dict | None:
    """safe이면 None, 아니면 {"title","body","url"} 반환."""
    level = result.get("level", "safe")

    if level == "safe":
        return None

    if level == "danger":
        title = "⚠️ 스팸 의심 문자"
        category = result.get("category") or "스팸"
        signals = result.get("signals", [])
        top_signal = signals[0]["type"] if signals else "의심 표현 포함"
        body = f"{category} · {top_signal}. 링크를 누르지 마세요"
    else:  # caution
        title = "확인이 필요한 문자"
        body = "의심스러운 표현이 있어요. 눌러서 확인하기"

    return {
        "title": title,
        "body": body,
        "url": f"/result/{result_id}",
    }
