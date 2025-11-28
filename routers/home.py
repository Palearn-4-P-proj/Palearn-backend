# Backend/routers/home.py
"""홈 관련 라우터"""

from fastapi import APIRouter, Depends
from typing import Dict
from datetime import date

from ..services.store import store
from ..utils.logger import log_request, log_stage, log_navigation
from .auth import get_current_user

router = APIRouter(prefix="/home", tags=["Home"])


@router.get("/header")
async def get_home_header(current_user: Dict = Depends(get_current_user)):
    log_request("GET /home/header", current_user['name'])
    log_stage(3, "홈 화면", current_user['name'])
    log_navigation(current_user['name'], "홈 화면")

    user_id = current_user['user_id']
    plans = store.plans.get(user_id, [])

    today_progress = 0
    if plans:
        current_plan = plans[-1]
        if 'daily_schedule' in current_plan:
            today_str = date.today().isoformat()
            for day in current_plan['daily_schedule']:
                if day['date'] == today_str:
                    total = len(day['tasks'])
                    completed = sum(1 for t in day['tasks'] if t.get('completed', False))
                    today_progress = int((completed / total * 100) if total > 0 else 0)
                    break

    return {
        "name": current_user['name'],
        "todayProgress": today_progress
    }
