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

class QuizItem(BaseModel):
    id: int
    type: str  # 'OX', 'MULTI', 'SHORT'
    question: str
    options: List[str] = []
    answer_key: Optional[str] = None

class QuizCreate(BaseModel):
    skill: str
    level: str

class QuizSession(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    skill: str
    level: str
    items: List[QuizItem]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class QuizAnswer(BaseModel):
    answers: List[Optional[str]]

class QuizResult(BaseModel):
    total: int
    correct: int
    rate: float
    level: str  # '초급', '중급', '고급'
    details: List[bool]

class QuizResponse(BaseModel):
    session_id: str
    items: List[QuizItem]