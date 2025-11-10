from fastapi import APIRouter, Depends, HTTPException, status, Request
from models.recommendation import RecommendationRequest, RecommendationResponse, Course
from models.user import TokenData
from utils.auth import get_current_user
from services.llm_service import LLMService
from typing import List
from datetime import datetime

router = APIRouter()

@router.post("/courses", response_model=RecommendationResponse)
async def recommend_courses(
    recommendation_request: RecommendationRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """강좌 추천 (LLM 기반)"""
    db = request.app.mongodb
    
    # 사용자 확인
    user = await db.users.find_one({"email": current_user.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # LLM으로 강좌 추천 생성
    result = await LLMService.recommend_courses(
        skill=recommendation_request.skill,
        level=recommendation_request.level,
        quiz_details=recommendation_request.quiz_details
    )
    
    # Course 객체로 변환
    courses = [Course(**course) for course in result.get("courses", [])]
    
    # 추천 기록 저장
    recommendation_data = {
        "user_id": str(user["_id"]),
        "skill": recommendation_request.skill,
        "level": recommendation_request.level,
        "courses": [course.dict() for course in courses],
        "reasoning": result.get("reasoning", ""),
        "created_at": datetime.utcnow()
    }
    
    await db.recommendations.insert_one(recommendation_data)
    
    return RecommendationResponse(
        courses=courses,
        reasoning=result.get("reasoning", "")
    )

@router.get("/history")
async def get_recommendation_history(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    limit: int = 10
):
    """추천 기록 조회"""
    db = request.app.mongodb
    
    user = await db.users.find_one({"email": current_user.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    user_id = str(user["_id"])
    
    history = []
    async for rec in db.recommendations.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(limit):
        history.append({
            "id": str(rec["_id"]),
            "skill": rec["skill"],
            "level": rec["level"],
            "courses": rec["courses"],
            "reasoning": rec.get("reasoning", ""),
            "created_at": rec["created_at"]
        })
    
    return {"history": history}