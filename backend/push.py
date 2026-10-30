"""D: 웹 푸시 발송"""
import json
import logging
import os

from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)

_subscriptions: list[dict] = []


def _vapid_private_key() -> str:
    path = os.getenv("VAPID_PRIVATE_KEY_PATH", "private_key.pem")
    if os.path.exists(path):
        return path
    raise RuntimeError(f"VAPID 개인키 파일이 없습니다: {path}")


def add_subscription(subscription: dict) -> None:
    """브라우저 PushSubscription을 등록."""
    endpoint = subscription.get("endpoint")
    for existing in _subscriptions:
        if existing.get("endpoint") == endpoint:
            return
    _subscriptions.append(subscription)


def send_to_all(payload: dict) -> None:
    """등록된 모든 구독자에게 푸시 발송. 실패해도 예외를 던지지 않음."""
    if not _subscriptions:
        logger.info("send_to_all: 구독자 없음")
        return

    try:
        private_key = _vapid_private_key()
    except RuntimeError as e:
        logger.warning("VAPID 키 없음, 푸시 건너뜀: %s", e)
        return

    email = os.getenv("VAPID_EMAIL", "team@example.com")
    dead: list[dict] = []

    for sub in list(_subscriptions):
        try:
            webpush(
                subscription_info=sub,
                data=json.dumps(payload, ensure_ascii=False),
                vapid_private_key=private_key,
                vapid_claims={"sub": f"mailto:{email}"},
            )
        except WebPushException as e:
            if e.response is not None and e.response.status_code == 410:
                dead.append(sub)
            else:
                logger.warning("푸시 발송 실패: %s", e)
        except Exception as e:
            logger.warning("푸시 발송 실패: %s", e)

    for sub in dead:
        _subscriptions.remove(sub)
        logger.info("만료된 구독 제거: %s", sub.get("endpoint", "")[:40])
