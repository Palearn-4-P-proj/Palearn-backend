# Backend/routers/friends.py
"""친구 관련 라우터"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
from datetime import date, datetime

from ..models.schemas import AddFriendRequest, CheckFriendPlanRequest
from ..services.store import store
from ..utils.logger import log_request, log_stage, log_success, log_error, log_navigation
from .auth import get_current_user

router = APIRouter(prefix="/friends", tags=["Friends"])


@router.get("")
async def get_friends(current_user: Dict = Depends(get_current_user)):
    log_request("GET /friends", current_user['name'])
    log_stage(8, "친구 목록", current_user['name'])
    log_navigation(current_user['name'], "친구 화면")

    user_id = current_user['user_id']
    friend_ids = store.friendships.get(user_id, [])

    friends = []
    for fid in friend_ids:
        friend = store.users.get(fid)
        if friend:
            today_rate = 0
            friend_plans = store.plans.get(fid, [])
            if friend_plans:
                current_plan = friend_plans[-1]
                today_str = date.today().isoformat()
                for day in current_plan.get('daily_schedule', []):
                    if day['date'] == today_str:
                        total = len(day['tasks'])
                        completed = sum(1 for t in day['tasks'] if t.get('completed', False))
                        today_rate = int((completed / total * 100) if total > 0 else 0)
                        break

            friends.append({
                "id": fid,
                "name": friend['name'],
                "avatarUrl": friend.get('photo_url'),
                "todayRate": today_rate
            })

    return friends


@router.post("/add")
async def add_friend(request: AddFriendRequest, current_user: Dict = Depends(get_current_user)):
    log_request("POST /friends/add", current_user['name'], f"code={request.code}")

    user_id = current_user['user_id']
    friend_code = request.code.upper()

    friend_id = store.friend_codes.get(friend_code)

    if not friend_id:
        log_error(f"친구 코드 없음: {friend_code}")
        raise HTTPException(status_code=404, detail="친구 코드를 찾을 수 없습니다.")

    if friend_id == user_id:
        raise HTTPException(status_code=400, detail="자기 자신은 친구로 추가할 수 없습니다.")

    if friend_id in store.friendships[user_id]:
        raise HTTPException(status_code=400, detail="이미 친구입니다.")

    store.friendships[user_id].append(friend_id)
    store.friendships[friend_id].append(user_id)

    friend = store.users.get(friend_id)
    store.notifications[friend_id]['new'].append(f"{current_user['name']}님이 친구로 추가했습니다.")

    log_success(f"친구 추가 완료: {friend['name']}")

    return {
        "success": True,
        "friend": {
            "id": friend_id,
            "name": friend['name'],
            "avatarUrl": friend.get('photo_url'),
            "todayRate": 0
        }
    }


@router.get("/{friend_id}/plans")
async def get_friend_plans(
    friend_id: str,
    date: str = None,
    current_user: Dict = Depends(get_current_user)
):
    user_id = current_user['user_id']

    if friend_id not in store.friendships.get(user_id, []):
        raise HTTPException(status_code=403, detail="친구가 아닙니다.")

    friend_plans = store.plans.get(friend_id, [])

    if not friend_plans:
        return []

    current_plan = friend_plans[-1]
    target_date = date or datetime.today().isoformat()

    for day in current_plan.get('daily_schedule', []):
        if day['date'] == target_date:
            return [
                {"id": task['id'], "title": task['title'], "done": task.get('completed', False)}
                for task in day['tasks']
            ]

    return []


@router.post("/{friend_id}/plans/check")
async def check_friend_plan(
    friend_id: str,
    request: CheckFriendPlanRequest,
    current_user: Dict = Depends(get_current_user)
):
    friend = store.users.get(friend_id)
    if friend:
        store.notifications[friend_id]['new'].append(
            f"{current_user['name']}님이 응원합니다! 💪"
        )
        log_success(f"{current_user['name']} → {friend['name']} 응원 전송")

    return {"success": True}
