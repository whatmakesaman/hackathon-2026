"""D: 웹 푸시 발송 — 스텁 (실제 발송은 VAPID 키 생성 후 구현)"""
import json
import logging

logger = logging.getLogger(__name__)

# 구독 정보 메모리 보관 (서버 재시작 시 초기화)
_subscriptions: list[dict] = []


def add_subscription(subscription: dict) -> None:
    """브라우저 PushSubscription을 등록."""
    endpoint = subscription.get("endpoint")
    # 중복 등록 방지
    for existing in _subscriptions:
        if existing.get("endpoint") == endpoint:
            return
    _subscriptions.append(subscription)


def send_to_all(payload: dict) -> None:
    """등록된 모든 구독자에게 푸시 발송. 실패해도 예외를 던지지 않음."""
    # TODO: VAPID 키 생성 후 아래 주석 해제
    # from pywebpush import webpush, WebPushException
    # import os
    # dead = []
    # for sub in list(_subscriptions):
    #     try:
    #         webpush(
    #             subscription_info=sub,
    #             data=json.dumps(payload),
    #             vapid_private_key=os.getenv("VAPID_PRIVATE_KEY"),
    #             vapid_claims={"sub": f"mailto:{os.getenv('VAPID_EMAIL', 'team@example.com')}"},
    #         )
    #     except WebPushException as e:
    #         if e.response and e.response.status_code == 410:
    #             dead.append(sub)
    #         else:
    #             logger.warning("푸시 발송 실패: %s", e)
    #     except Exception as e:
    #         logger.warning("푸시 발송 실패: %s", e)
    # for sub in dead:
    #     _subscriptions.remove(sub)

    # 스텁: 아무것도 하지 않음
    logger.info("send_to_all stub 호출됨 (구독자 %d명)", len(_subscriptions))
