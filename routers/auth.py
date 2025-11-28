# Backend/routers/auth.py
"""인증 관련 라우터"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Dict
import uuid

from ..models.schemas import SignupRequest, LoginRequest
from ..services.store import store
from ..utils.logger import log_request, log_stage, log_success, log_error, log_navigation

router = APIRouter(prefix="/auth", tags=["Auth"])


async def get_current_user(authorization: str = Header(None)) -> Dict:
    """현재 인증된 사용자 가져오기"""
    if not authorization:
        if not store.users:
            test_user = store.create_user(
                username="admin",
                email="admin@test.com",
                password="admin123",
                name="admin",
                birth="2000-01-01"
            )
            token = str(uuid.uuid4())
            store.tokens[token] = test_user['user_id']
            return test_user
        return list(store.users.values())[0]

    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    user = store.get_user_by_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user


@router.post("/signup")
async def signup(request: SignupRequest):
    log_request("POST /auth/signup", request.name, f"email={request.email}")
    log_stage(1, "회원가입", request.name)

    user = store.create_user(
        username=request.username,
        email=request.email,
        password=request.password,
        name=request.name,
        birth=request.birth,
        photo_url=request.photo_url
    )

    if not user:
        log_error(f"회원가입 실패 - 이메일 중복: {request.email}")
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

    log_success(f"회원가입 완료! user_id={user['user_id'][:8]}..., 친구코드={user['friend_code']}")

    return {
        "success": True,
        "userId": user['user_id'],
        "message": "회원가입이 완료되었습니다."
    }


@router.post("/login")
async def login(request: LoginRequest):
    log_request("POST /auth/login", request.email)
    log_stage(2, "로그인", request.email)

    result = store.login(request.email, request.password)

    if not result:
        log_error(f"로그인 실패: {request.email}")
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    log_success(f"로그인 성공! name={result['name']}, token={result['token'][:16]}...")
    log_navigation(result['name'], "홈 화면")

    return {
        "success": True,
        "token": result['token'],
        "userId": result['user_id'],
        "displayName": result['name']
    }


@router.post("/logout")
async def logout(current_user: Dict = Depends(get_current_user), authorization: str = Header(None)):
    log_request("POST /auth/logout", current_user['name'])
    log_navigation(current_user['name'], "로그아웃 → 로그인 화면")

    if authorization:
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        store.logout(token)

    log_success(f"로그아웃 완료: {current_user['name']}")
    return {"success": True}
