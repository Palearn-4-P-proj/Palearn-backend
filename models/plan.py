from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class PlanCreate(BaseModel):
    skill: str
    hour_per_day: str
    start_date: datetime
    rest_days: List[str] = []
    level: str  # '초급', '중급', '고급'

class DailyTask(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    title: str
    description: Optional[str] = None
    completed: bool = False
    date: datetime

class WeeklyGoal(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    title: str
    description: Optional[str] = None
    week_number: int
    tasks: List[str] = []

class MonthlyMilestone(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    title: str
    description: Optional[str] = None
    month: int
    goals: List[str] = []

class Plan(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    skill: str
    level: str
    hour_per_day: str
    start_date: datetime
    rest_days: List[str]
    
    daily_tasks: List[DailyTask] = []
    weekly_goals: List[WeeklyGoal] = []
    monthly_milestones: List[MonthlyMilestone] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class PlanResponse(BaseModel):
    id: str
    user_id: str
    skill: str
    level: str
    hour_per_day: str
    start_date: datetime
    rest_days: List[str]
    daily_tasks: List[DailyTask]
    weekly_goals: List[WeeklyGoal]
    monthly_milestones: List[MonthlyMilestone]
    created_at: datetime
    updated_at: datetime

class TodayProgress(BaseModel):
    total: int
    completed: int
    percentage: float