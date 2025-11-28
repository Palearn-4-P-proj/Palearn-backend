# Backend/routers/notifications.py
"""알림 관련 라우터"""

from fastapi import APIRouter, Depends
from typing import Dict

from ..services.store import store
from ..utils.logger import log_request, log_stage, log_success, log_navigation
from .auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def get_notifications(current_user: Dict = Depends(get_current_user)):
    log_request("GET /notifications", current_user['name'])
    log_stage(9, "알림 확인", current_user['name'])
    log_navigation(current_user['name'], "알림 화면")

    user_id = current_user['user_id']
    notifications = store.notifications.get(user_id, {'new': [], 'old': []})

    return {
        "new_alerts": notifications['new'],
        "old_alerts": notifications['old']
    }


@router.post("/read")
async def mark_notifications_read(current_user: Dict = Depends(get_current_user)):
    user_id = current_user['user_id']
    notifications = store.notifications.get(user_id, {'new': [], 'old': []})

    notifications['old'] = notifications['new'] + notifications['old']
    notifications['new'] = []

    log_success("알림 읽음 처리 완료")
    return {"success": True}
