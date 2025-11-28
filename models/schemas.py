# Backend/models/schemas.py
"""Pydantic 모델 정의"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class SignupRequest(BaseModel):
    username: str
    email: str
    password: str
    name: str
    birth: str
    photo_url: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ProfileUpdateRequest(BaseModel):
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    birth: Optional[str] = None
    password: Optional[str] = None


class QuizAnswer(BaseModel):
    id: int
    userAnswer: str


class QuizSubmitRequest(BaseModel):
    answers: List[QuizAnswer]


class PlanGenerateRequest(BaseModel):
    skill: str
    hourPerDay: float
    startDate: str
    restDays: List[str]
    selfLevel: str


class AddFriendRequest(BaseModel):
    code: str


class CheckFriendPlanRequest(BaseModel):
    planId: str
    done: bool


class SelectCourseRequest(BaseModel):
    user_id: str
    course_id: str


class ApplyRecommendationRequest(BaseModel):
    selected_course: Dict[str, Any]
    quiz_level: str
    quiz_details: Optional[Dict] = None
    skill: str
    hourPerDay: float
    startDate: str
    restDays: List[str]
