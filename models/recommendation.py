from pydantic import BaseModel
from typing import List, Optional

class RecommendationRequest(BaseModel):
    skill: str
    level: str
    quiz_details: List[bool]

class Course(BaseModel):
    id: str
    title: str
    provider: str
    weeks: int
    free: bool
    summary: str
    syllabus: List[str]
    url: Optional[str] = None

class RecommendationResponse(BaseModel):
    courses: List[Course]
    reasoning: str