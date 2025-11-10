from fastapi import APIRouter, Depends, HTTPException, status, Request
from models.plan import PlanCreate, Plan, PlanResponse, DailyTask, WeeklyGoal, MonthlyMilestone, TodayProgress
from models.user import TokenData
from utils.auth import get_current_user
from services.llm_service import LLMService
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List

router = APIRouter()

@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_create: PlanCreate,
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """학습 계획 생성 (LLM 기반)"""
    db = request.app.mongodb
    
    # 사용자 찾기
    user = await db.users.find_one({"email": current_user.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    user_id = str(user["_id"])
    
    # LLM으로 학습 계획 생성
    llm_result = await LLMService.generate_learning_plan(
        skill=plan_create.skill,
        level=plan_create.level,
        hour_per_day=plan_create.hour_per_day,
        rest_days=plan_create.rest_days
    )
    
    # Daily Tasks 구성
    daily_tasks = []
    for i, task in enumerate(llm_result.get("daily_tasks", [])):
        task_date = plan_create.start_date + timedelta(days=i)
        daily_tasks.append(DailyTask(
            title=task["title"],
            description=task.get("description", ""),
            date=task_date,
            completed=False
        ))
    
    # Weekly Goals 구성
    weekly_goals = []
    for i, goal in enumerate(llm_result.get("weekly_goals", [])):
        weekly_goals.append(WeeklyGoal(
            title=goal["title"],
            description=goal.get("description", ""),
            week_number=i + 1,
            tasks=goal.get("tasks", [])
        ))
    
    # Monthly Milestones 구성
    monthly_milestones = []
    for i, milestone in enumerate(llm_result.get("monthly_milestones", [])):
        monthly_milestones.append(MonthlyMilestone(
            title=milestone["title"],
            description=milestone.get("description", ""),
            month=i + 1,
            goals=milestone.get("goals", [])
        ))
    
    # DB에 저장
    plan_data = {
        "user_id": user_id,
        "skill": plan_create.skill,
        "level": plan_create.level,
        "hour_per_day": plan_create.hour_per_day,
        "start_date": plan_create.start_date,
        "rest_days": plan_create.rest_days,
        "daily_tasks": [task.dict() for task in daily_tasks],
        "weekly_goals": [goal.dict() for goal in weekly_goals],
        "monthly_milestones": [milestone.dict() for milestone in monthly_milestones],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.plans.insert_one(plan_data)
    plan_data["_id"] = result.inserted_id
    
    return PlanResponse(
        id=str(result.inserted_id),
        user_id=user_id,
        skill=plan_create.skill,
        level=plan_create.level,
        hour_per_day=plan_create.hour_per_day,
        start_date=plan_create.start_date,
        rest_days=plan_create.rest_days,
        daily_tasks=daily_tasks,
        weekly_goals=weekly_goals,
        monthly_milestones=monthly_milestones,
        created_at=plan_data["created_at"],
        updated_at=plan_data["updated_at"]
    )

@router.get("/my", response_model=List[PlanResponse])
async def get_my_plans(
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """내 학습 계획 목록 조회"""
    db = request.app.mongodb
    
    user = await db.users.find_one({"email": current_user.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    user_id = str(user["_id"])
    
    plans = []
    async for plan in db.plans.find({"user_id": user_id}):
        plans.append(PlanResponse(
            id=str(plan["_id"]),
            user_id=plan["user_id"],
            skill=plan["skill"],
            level=plan["level"],
            hour_per_day=plan["hour_per_day"],
            start_date=plan["start_date"],
            rest_days=plan["rest_days"],
            daily_tasks=[DailyTask(**task) for task in plan.get("daily_tasks", [])],
            weekly_goals=[WeeklyGoal(**goal) for goal in plan.get("weekly_goals", [])],
            monthly_milestones=[MonthlyMilestone(**ms) for ms in plan.get("monthly_milestones", [])],
            created_at=plan["created_at"],
            updated_at=plan["updated_at"]
        ))
    
    return plans

@router.get("/today/progress", response_model=TodayProgress)
async def get_today_progress(
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """오늘의 학습 진행률 조회"""
    db = request.app.mongodb
    
    user = await db.users.find_one({"email": current_user.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    user_id = str(user["_id"])
    today = datetime.utcnow().date()
    
    # 모든 계획의 오늘 작업 가져오기
    total = 0
    completed = 0
    
    async for plan in db.plans.find({"user_id": user_id}):
        for task in plan.get("daily_tasks", []):
            task_date = task["date"].date() if isinstance(task["date"], datetime) else task["date"]
            if task_date == today:
                total += 1
                if task.get("completed", False):
                    completed += 1
    
    percentage = (completed / total * 100) if total > 0 else 0
    
    return TodayProgress(
        total=total,
        completed=completed,
        percentage=round(percentage, 1)
    )

@router.patch("/tasks/{task_id}/complete")
async def toggle_task_completion(
    task_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """작업 완료 상태 토글"""
    db = request.app.mongodb
    
    user = await db.users.find_one({"email": current_user.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    user_id = str(user["_id"])
    
    # 작업이 포함된 계획 찾기
    plan = await db.plans.find_one({
        "user_id": user_id,
        "daily_tasks.id": task_id
    })
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작업을 찾을 수 없습니다"
        )
    
    # 작업 상태 토글
    for task in plan["daily_tasks"]:
        if task["id"] == task_id:
            new_status = not task.get("completed", False)
            await db.plans.update_one(
                {"_id": plan["_id"], "daily_tasks.id": task_id},
                {"$set": {"daily_tasks.$.completed": new_status, "updated_at": datetime.utcnow()}}
            )
            return {"success": True, "completed": new_status}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="작업을 찾을 수 없습니다"
    )