from fastapi import APIRouter, Depends, HTTPException, status, Request
from models.user import UserCreate, UserLogin, Token, UserResponse, UserInDB
from utils.auth import verify_password, get_password_hash, create_access_token, generate_user_code
from datetime import timedelta, datetime  # ← datetime 추가!
from config.settings import settings

router = APIRouter()

@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, request: Request):
    """회원가입"""
    db = request.app.mongodb
    
    # 이메일 중복 체크
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다"
        )
    
    # 사용자 생성
    user_dict = user.dict()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    user_dict["created_at"] = datetime.utcnow()  # ← 추가!
    
    # 임시 ID로 user_code 생성
    from bson import ObjectId
    temp_id = str(ObjectId())
    user_dict["user_code"] = generate_user_code(temp_id)
    
    result = await db.users.insert_one(user_dict)
    
    # 실제 ID로 user_code 재생성
    actual_id = str(result.inserted_id)
    actual_code = generate_user_code(actual_id)
    await db.users.update_one(
        {"_id": result.inserted_id},
        {"$set": {"user_code": actual_code}}
    )
    
    # 생성된 사용자 조회
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    # JWT 토큰 생성
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    
    user_response = UserResponse(
        id=str(created_user["_id"]),
        email=created_user["email"],
        name=created_user["name"],
        birth=created_user.get("birth"),
        photo_url=created_user.get("photo_url"),
        user_code=created_user["user_code"],
        created_at=created_user["created_at"]
    )
    
    return Token(
        access_token=access_token,
        user=user_response
    )

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, request: Request):
    """로그인"""
    db = request.app.mongodb
    
    # 사용자 찾기
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다"
        )
    
    # 비밀번호 확인
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다"
        )
    
    # JWT 토큰 생성
    access_token = create_access_token(
        data={"sub": credentials.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    
    user_response = UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        name=user["name"],
        birth=user.get("birth"),
        photo_url=user.get("photo_url"),
        user_code=user["user_code"],
        created_at=user["created_at"]
    )
    
    return Token(
        access_token=access_token,
        user=user_response
    )