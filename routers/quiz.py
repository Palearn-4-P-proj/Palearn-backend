from fastapi import APIRouter, Depends, HTTPException, status, Request
from models.quiz import QuizCreate, QuizResponse, QuizAnswer, QuizResult, QuizSession, QuizItem
from models.user import TokenData
from utils.auth import get_current_user
from services.llm_service import LLMService
from datetime import datetime
from typing import List

router = APIRouter()

@router.post("/generate", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def generate_quiz(
    quiz_create: QuizCreate,
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """퀴즈 생성 (LLM 기반)"""
    db = request.app.mongodb
    
    # 사용자 찾기
    user = await db.users.find_one({"email": current_user.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    user_id = str(user["_id"])
    
    # LLM으로 퀴즈 생성
    questions = await LLMService.generate_quiz(
        skill=quiz_create.skill,
        level=quiz_create.level
    )
    
    # QuizItem 객체로 변환
    quiz_items = [QuizItem(**q) for q in questions]
    
    # DB에 세션 저장
    session_data = {
        "user_id": user_id,
        "skill": quiz_create.skill,
        "level": quiz_create.level,
        "items": [item.dict() for item in quiz_items],
        "created_at": datetime.utcnow()
    }
    
    result = await db.quiz_sessions.insert_one(session_data)
    
    # 클라이언트에는 정답을 제외하고 반환
    items_without_answers = []
    for item in quiz_items:
        item_dict = item.dict()
        item_dict.pop("answer_key", None)  # 정답 제거
        items_without_answers.append(QuizItem(**item_dict))
    
    return QuizResponse(
        session_id=str(result.inserted_id),
        items=items_without_answers
    )

@router.post("/{session_id}/submit", response_model=QuizResult)
async def submit_quiz(
    session_id: str,
    quiz_answer: QuizAnswer,
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """퀴즈 제출 및 채점"""
    db = request.app.mongodb
    
    # 사용자 확인
    user = await db.users.find_one({"email": current_user.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    user_id = str(user["_id"])
    
    # 세션 찾기
    from bson import ObjectId
    try:
        session = await db.quiz_sessions.find_one({
            "_id": ObjectId(session_id),
            "user_id": user_id
        })
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="잘못된 세션 ID입니다"
        )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="퀴즈 세션을 찾을 수 없습니다"
        )
    
    # 채점
    items = session["items"]
    user_answers = quiz_answer.answers
    
    if len(items) != len(user_answers):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="답안 개수가 일치하지 않습니다"
        )
    
    correct = 0
    details = []
    
    for item, user_answer in zip(items, user_answers):
        correct_answer = item.get("answer_key", "").strip()
        user_ans = (user_answer or "").strip()
        
        is_correct = correct_answer.lower() == user_ans.lower() if correct_answer else False
        details.append(is_correct)
        
        if is_correct:
            correct += 1
    
    total = len(items)
    rate = correct / total if total > 0 else 0
    
    # 수준 판정
    if rate >= 0.8:
        level = "고급"
    elif rate >= 0.5:
        level = "중급"
    else:
        level = "초급"
    
    # 결과 저장
    result_data = {
        "session_id": session_id,
        "user_id": user_id,
        "total": total,
        "correct": correct,
        "rate": rate,
        "level": level,
        "details": details,
        "created_at": datetime.utcnow()
    }
    
    await db.quiz_results.insert_one(result_data)
    
    return QuizResult(
        total=total,
        correct=correct,
        rate=rate,
        level=level,
        details=details
    )