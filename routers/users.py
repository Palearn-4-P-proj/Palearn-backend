from fastapi import APIRouter, Depends, HTTPException, status, Request
from models.user import UserResponse, UserUpdate, TokenData
from utils.auth import get_current_user, get_password_hash
from bson import ObjectId

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """현재 로그인한 사용자 정보 조회"""
    db = request.app.mongodb
    
    user = await db.users.find_one({"email": current_user.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        name=user["name"],
        birth=user.get("birth"),
        photo_url=user.get("photo_url"),
        user_code=user["user_code"],
        created_at=user["created_at"]
    )

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """사용자 프로필 업데이트"""
    db = request.app.mongodb
    
    # 업데이트할 필드 추출
    update_data = {}
    if user_update.name is not None:
        update_data["name"] = user_update.name
    if user_update.birth is not None:
        update_data["birth"] = user_update.birth
    if user_update.photo_url is not None:
        update_data["photo_url"] = user_update.photo_url
    if user_update.password is not None:
        update_data["hashed_password"] = get_password_hash(user_update.password)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="업데이트할 내용이 없습니다"
        )
    
    # 사용자 업데이트
    result = await db.users.find_one_and_update(
        {"email": current_user.email},
        {"$set": update_data},
        return_document=True
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    return UserResponse(
        id=str(result["_id"]),
        email=result["email"],
        name=result["name"],
        birth=result.get("birth"),
        photo_url=result.get("photo_url"),
        user_code=result["user_code"],
        created_at=result["created_at"]
    )