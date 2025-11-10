from fastapi import APIRouter, Depends, HTTPException, status, Request
from models.friend import FriendAdd, FriendSummary
from models.user import TokenData
from utils.auth import get_current_user
from datetime import datetime
from typing import List
from bson import ObjectId

router = APIRouter()

@router.post("/add")
async def add_friend(
    friend_add: FriendAdd,
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """친구 코드로 친구 추가"""
    db = request.app.mongodb
    
    # 현재 사용자
    user = await db.users.find_one({"email": current_user.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    user_id = str(user["_id"])
    
    # 친구 찾기
    friend = await db.users.find_one({"user_code": friend_add.friend_code})
    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 코드의 사용자를 찾을 수 없습니다"
        )
    
    friend_id = str(friend["_id"])
    
    # 자기 자신 추가 방지
    if user_id == friend_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신을 친구로 추가할 수 없습니다"
        )
    
    # 이미 친구인지 확인
    existing = await db.friendships.find_one({
        "user_id": user_id,
        "friend_id": friend_id
    })
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 친구로 등록되어 있습니다"
        )
    
    # 양방향 친구 관계 생성
    await db.friendships.insert_one({
        "user_id": user_id,
        "friend_id": friend_id,
        "created_at": datetime.utcnow()
    })
    
    await db.friendships.insert_one({
        "user_id": friend_id,
        "friend_id": user_id,
        "created_at": datetime.utcnow()
    })
    
    return {"success": True, "message": "친구가 추가되었습니다"}

@router.get("/list", response_model=List[FriendSummary])
async def get_friends_list(
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """친구 목록 조회"""
    db = request.app.mongodb
    
    # 현재 사용자
    user = await db.users.find_one({"email": current_user.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    user_id = str(user["_id"])
    
    # 친구 관계 조회
    friends = []
    async for friendship in db.friendships.find({"user_id": user_id}):
        friend_id = friendship["friend_id"]
        
        # 친구 정보 조회
        try:
            friend_user = await db.users.find_one({"_id": ObjectId(friend_id)})
        except:
            continue
        
        if not friend_user:
            continue
        
        # 오늘 달성률 계산
        today_progress = await calculate_today_progress(db, friend_id)
        
        friends.append(FriendSummary(
            id=friend_id,
            name=friend_user["name"],
            photo_url=friend_user.get("photo_url"),
            today_rate=today_progress
        ))
    
    return friends

@router.get("/{friend_id}/progress")
async def get_friend_progress(
    friend_id: str,
    date: str,  # YYYY-MM-DD 형식
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """특정 날짜의 친구 학습 진행 상황 조회"""
    db = request.app.mongodb
    
    # 현재 사용자
    user = await db.users.find_one({"email": current_user.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    user_id = str(user["_id"])
    
    # 친구 관계 확인
    friendship = await db.friendships.find_one({
        "user_id": user_id,
        "friend_id": friend_id
    })
    
    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="친구가 아닙니다"
        )
    
    # 날짜 파싱
    from datetime import datetime
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 날짜 형식입니다 (YYYY-MM-DD)"
        )
    
    # 친구의 해당 날짜 작업 조회
    tasks = []
    async for plan in db.plans.find({"user_id": friend_id}):
        for task in plan.get("daily_tasks", []):
            task_date = task["date"].date() if isinstance(task["date"], datetime) else task["date"]
            if task_date == target_date:
                tasks.append({
                    "id": task["id"],
                    "title": task["title"],
                    "completed": task.get("completed", False)
                })
    
    return {
        "date": date,
        "tasks": tasks,
        "total": len(tasks),
        "completed": sum(1 for t in tasks if t["completed"])
    }

async def calculate_today_progress(db, user_id: str) -> int:
    """오늘 달성률 계산 (0-100)"""
    today = datetime.utcnow().date()
    
    total = 0
    completed = 0
    
    async for plan in db.plans.find({"user_id": user_id}):
        for task in plan.get("daily_tasks", []):
            task_date = task["date"].date() if isinstance(task["date"], datetime) else task["date"]
            if task_date == today:
                total += 1
                if task.get("completed", False):
                    completed += 1
    
    return round((completed / total * 100)) if total > 0 else 0