# Backend/routers/plan_apply.py
"""계획 적용 관련 라우터"""

from fastapi import APIRouter, Depends
from typing import Dict
import uuid

from ..models.schemas import ApplyRecommendationRequest
from ..services.store import store
from ..services.gpt_service import call_gpt, extract_json
from ..utils.logger import log_request, log_success, log_error, log_navigation
from .auth import get_current_user

router = APIRouter(prefix="/plan", tags=["Plan"])


@router.post("/apply_recommendation")
async def apply_recommendation(request: ApplyRecommendationRequest, current_user: Dict = Depends(get_current_user)):
    log_request("POST /plan/apply_recommendation", current_user['name'])

    user_id = current_user['user_id']
    course = request.selected_course
    syllabus = course.get('syllabus', [])

    prompt = f"""
선택된 강좌를 바탕으로 학습 계획을 만들어주세요.

조건:
- 선택 강좌: {course.get('title', 'Unknown')}
- 커리큘럼: {syllabus}
- 스킬: {request.skill}
- 하루 공부 시간: {request.hourPerDay}시간
- 시작 날짜: {request.startDate}
- 쉬는 요일: {', '.join(request.restDays) if request.restDays else '없음'}
- 학습자 수준: {request.quiz_level}

반드시 아래 JSON 형식으로만 응답해주세요:
```json
{{
  "plan_name": "계획 이름",
  "total_duration": "N주",
  "daily_schedule": [
    {{
      "date": "YYYY-MM-DD",
      "tasks": [
        {{
          "id": "uuid",
          "title": "학습 내용",
          "description": "설명",
          "duration": "시간",
          "completed": false
        }}
      ]
    }}
  ]
}}
```
"""

    response = call_gpt(prompt, use_search=False)
    data = extract_json(response)

    if data and 'daily_schedule' in data:
        for day in data['daily_schedule']:
            for task in day['tasks']:
                if 'id' not in task:
                    task['id'] = str(uuid.uuid4())
                if 'completed' not in task:
                    task['completed'] = False

        store.plans[user_id].append(data)
        log_success("추천 기반 계획 생성 완료")
        log_navigation(current_user['name'], "홈 화면")
        return {"success": True, "plan": data}

    log_error("계획 생성 실패")
    return {"success": False, "message": "계획 생성에 실패했습니다."}
