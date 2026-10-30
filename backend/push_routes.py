"""D: 푸시 관련 라우터 — B가 main.py에서 include_router()로 등록"""
import os
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from push import add_subscription

router = APIRouter(prefix="/push", tags=["push"])


class SubscriptionRequest(BaseModel):
    endpoint: str
    keys: dict
    # pydantic이 실행 중에 타입을 해석하므로 Python 3.9에서는 `float | None` 대신 Optional을 쓴다.
    expirationTime: Optional[float] = None


@router.get("/vapid-public-key")
def get_vapid_public_key():
    """VAPID 공개키 반환 (프론트가 구독 시 사용)."""
    key = os.getenv("VAPID_PUBLIC_KEY", "STUB_PUBLIC_KEY_REPLACE_AFTER_VAPID_GEN")
    return {"key": key}


@router.post("/subscribe")
def subscribe(body: SubscriptionRequest):
    """브라우저 PushSubscription 등록."""
    add_subscription(body.model_dump())
    return {"ok": True}
