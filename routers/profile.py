# Backend/routers/profile.py
"""프로필 관련 라우터"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
import hashlib

from ..models.schemas import ProfileUpdateRequest
from ..services.store import store
from ..utils.logger import log_request, log_stage, log_success, log_navigation
from .auth import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/me")
async def get_profile(current_user: Dict = Depends(get_current_user)):
    log_request("GET /profile/me", current_user['name'])
    log_stage(10, "프로필", current_user['name'])
    log_navigation(current_user['name'], "프로필 화면")

    return {
        "name": current_user['name'],
        "user_id": current_user['user_id'],
        "email": current_user['email'],
        "birth": current_user['birth'],
        "photo_url": current_user.get('photo_url'),
        "friend_code": current_user['friend_code']
    }


@router.post("/update")
async def update_profile(request: ProfileUpdateRequest, current_user: Dict = Depends(get_current_user)):
    log_request("POST /profile/update", current_user['name'])

    user = store.users.get(request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if request.email:
        user['email'] = request.email
    if request.name:
        user['name'] = request.name
    if request.birth:
        user['birth'] = request.birth
    if request.password:
        user['password'] = hashlib.sha256(request.password.encode()).hexdigest()

    log_success(f"프로필 업데이트 완료: {current_user['name']}")
    return {"success": True}
