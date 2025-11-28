# Backend/routers/plans.py
"""학습 계획 관련 라우터"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
from datetime import datetime, date, timedelta
import uuid

from ..models.schemas import PlanGenerateRequest, ApplyRecommendationRequest
from ..services.store import store
from ..services.gpt_service import call_gpt, extract_json
from ..services.web_search import search_materials_for_topic
from ..utils.logger import log_request, log_stage, log_success, log_navigation, log_info
from .auth import get_current_user

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.get("/all")
async def get_all_plans(current_user: Dict = Depends(get_current_user)):
    """사용자의 모든 학습 계획 목록 조회"""
    log_request("GET /plans/all", current_user['name'])

    user_id = current_user['user_id']
    plans = store.plans.get(user_id, [])

    return plans


@router.get("/related_materials")
async def get_related_materials(topic: str, current_user: Dict = Depends(get_current_user)):
    """특정 학습 주제에 대한 연관 자료 검색"""
    log_request("GET /plans/related_materials", current_user['name'], f"topic={topic}")

    prompt = f"""
📖 **'{topic}' 주제에 대한 보충 학습 자료를 찾아주세요.**

🚨🚨🚨 **절대 금지 사항** 🚨🚨🚨
- example.com, example.org 등 EXAMPLE이 들어간 모든 URL 절대 사용 금지
- 존재하지 않는 가상의 자료 생성 금지
- 반드시 실제 접근 가능한 URL만 제공

📚 **검색 대상**:
- 유튜브 강의 영상 (한국어 또는 영어)
- 기술 블로그 (velog, tistory, medium 등)
- 공식 문서
- 온라인 강좌

⚠️ **필수 출력 형식** (JSON):
```json
{{
  "materials": [
    {{
      "title": "자료 제목",
      "type": "유튜브",
      "url": "https://실제URL",
      "description": "이 자료가 학습에 도움이 되는 이유"
    }},
    {{
      "title": "자료 제목",
      "type": "블로그",
      "url": "https://실제URL",
      "description": "이 자료가 학습에 도움이 되는 이유"
    }}
  ]
}}
```

📌 **요청사항**:
- 총 3-4개의 학습 자료 추천
- 다양한 타입의 자료 포함 (유튜브, 블로그, 공식문서 등)
- 반드시 한국어 또는 영어로 된 실제 자료
"""

    response = call_gpt(prompt, use_search=True)
    data = extract_json(response)

    if data and 'materials' in data:
        valid_materials = [m for m in data['materials'] if 'example' not in m.get('url', '').lower()]
        if valid_materials:
            log_success(f"연관 자료 {len(valid_materials)}개 찾기 완료")
            return {"materials": valid_materials[:4]}

    # 기본 검색 링크
    search_query = topic.replace(' ', '+')
    log_info("GPT 응답 실패, 기본 검색 링크 반환")
    return {
        "materials": [
            {"title": f"{topic} - 유튜브 검색", "type": "유튜브", "url": f"https://www.youtube.com/results?search_query={search_query}", "description": "유튜브에서 관련 영상을 검색합니다."},
            {"title": f"{topic} - 구글 검색", "type": "기타", "url": f"https://www.google.com/search?q={search_query}+강의", "description": "구글에서 관련 강의를 검색합니다."},
        ]
    }


@router.get("")
async def get_plans(scope: str = "daily", current_user: Dict = Depends(get_current_user)):
    log_request("GET /plans", current_user['name'], f"scope={scope}")

    user_id = current_user['user_id']
    plans = store.plans.get(user_id, [])

    if not plans:
        return []

    current_plan = plans[-1]
    today = date.today()
    result = []

    if 'daily_schedule' in current_plan:
        for day in current_plan['daily_schedule']:
            day_date = datetime.strptime(day['date'], '%Y-%m-%d').date()

            if scope == "daily" and day_date == today:
                result.extend([task['title'] for task in day['tasks']])
            elif scope == "weekly":
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=6)
                if week_start <= day_date <= week_end:
                    result.extend([task['title'] for task in day['tasks']])
            elif scope == "monthly":
                if day_date.year == today.year and day_date.month == today.month:
                    result.extend([task['title'] for task in day['tasks']])

    return result


@router.get("/review")
async def get_review_plans(current_user: Dict = Depends(get_current_user)):
    user_id = current_user['user_id']
    plans = store.plans.get(user_id, [])

    if not plans:
        return []

    current_plan = plans[-1]
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    result = []
    if 'daily_schedule' in current_plan:
        for day in current_plan['daily_schedule']:
            if day['date'] == yesterday:
                for task in day['tasks']:
                    if task.get('completed', False):
                        result.append({"title": task['title'], "id": task.get('id', str(uuid.uuid4()))})

    return result


@router.get("/yesterday_review")
async def get_yesterday_review(current_user: Dict = Depends(get_current_user)):
    """어제 학습 내용 기반 복습 자료 반환 (유튜브 1개 + 블로그 1개)"""
    log_request("GET /plans/yesterday_review", current_user['name'])

    user_id = current_user['user_id']
    plans = store.plans.get(user_id, [])

    if not plans:
        return {"has_review": False, "materials": [], "yesterday_topic": ""}

    current_plan = plans[-1]
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    # 어제 학습한 내용 찾기
    yesterday_topics = []
    if 'daily_schedule' in current_plan:
        for day in current_plan['daily_schedule']:
            if day['date'] == yesterday:
                for task in day['tasks']:
                    yesterday_topics.append(task.get('title', ''))

    if not yesterday_topics:
        return {"has_review": False, "materials": [], "yesterday_topic": ""}

    # 첫 번째 토픽으로 복습 자료 검색
    topic = yesterday_topics[0]

    # 태스크에 미리 저장된 복습 자료가 있는지 확인
    for day in current_plan.get('daily_schedule', []):
        if day['date'] == yesterday:
            for task in day['tasks']:
                if task.get('review_materials'):
                    return {
                        "has_review": True,
                        "materials": task['review_materials'][:2],  # 유튜브 1 + 블로그 1
                        "yesterday_topic": topic
                    }

    # 없으면 기본 검색 링크 반환
    search_query = topic.replace(' ', '+')
    return {
        "has_review": True,
        "materials": [
            {"title": f"{topic} 복습 영상", "type": "유튜브", "url": f"https://www.youtube.com/results?search_query={search_query}+강의"},
            {"title": f"{topic} 복습 글", "type": "블로그", "url": f"https://www.google.com/search?q={search_query}+블로그"}
        ],
        "yesterday_topic": topic
    }


def _get_materials_for_task(topic: str) -> dict:
    """태스크에 대한 학습 자료 검색 (웹 검색 API 사용)"""
    try:
        return search_materials_for_topic(topic)
    except Exception as e:
        log_info(f"웹 검색 실패, 기본 URL 사용: {e}")
        # 실패 시 기본 검색 URL
        from urllib.parse import quote_plus
        search_query = quote_plus(topic)
        default_materials = [
            {"title": f"{topic} 강의 영상", "type": "유튜브", "url": f"https://www.youtube.com/results?search_query={search_query}+강의", "description": "유튜브에서 검색"},
            {"title": f"{topic} 블로그 글", "type": "블로그", "url": f"https://www.google.com/search?q={search_query}+블로그", "description": "구글에서 검색"},
        ]
        return {
            "related_materials": default_materials,
            "review_materials": default_materials
        }


@router.post("/generate")
async def generate_plan(request: PlanGenerateRequest, current_user: Dict = Depends(get_current_user)):
    log_request("POST /plans/generate", current_user['name'], f"skill={request.skill}")
    log_stage(7, "계획 생성", current_user['name'])

    user_id = current_user['user_id']

    prompt = f"""
학습 계획을 만들어주세요.

조건:
- 스킬: {request.skill}
- 하루 공부 시간: {request.hourPerDay}시간
- 시작 날짜: {request.startDate}
- 쉬는 요일: {', '.join(request.restDays) if request.restDays else '없음'}
- 학습자 수준: {request.selfLevel}

반드시 아래 JSON 형식으로만 응답해주세요:
```json
{{
  "plan_name": "{request.skill} 학습 계획",
  "total_duration": "4주",
  "daily_schedule": [
    {{
      "date": "YYYY-MM-DD",
      "tasks": [
        {{
          "id": "uuid",
          "title": "학습 내용",
          "description": "상세 설명",
          "duration": "1시간",
          "completed": false
        }}
      ]
    }}
  ]
}}
```

{request.startDate}부터 4주간의 일정을 만들되, 쉬는 요일({', '.join(request.restDays)})은 제외해주세요.
하루에 2-3개의 구체적인 학습 태스크를 배정해주세요.
"""

    response = call_gpt(prompt, use_search=False)
    data = extract_json(response)

    if data and 'daily_schedule' in data:
        log_info("학습 자료 검색 시작...")
        for day in data['daily_schedule']:
            for task in day['tasks']:
                if 'id' not in task:
                    task['id'] = str(uuid.uuid4())
                if 'completed' not in task:
                    task['completed'] = False
                # 각 태스크에 연관 자료 미리 추가 (웹 검색 API 사용)
                if 'related_materials' not in task or 'review_materials' not in task:
                    materials = _get_materials_for_task(task.get('title', request.skill))
                    task['related_materials'] = materials.get('related_materials', [])
                    task['review_materials'] = materials.get('review_materials', [])

        store.plans[user_id].append(data)
        log_success(f"학습 계획 생성 완료: {data.get('plan_name', 'Unknown')}")
        log_navigation(current_user['name'], "퀴즈 화면")
        return data

    # 기본 계획 생성
    start = datetime.strptime(request.startDate.split('T')[0], '%Y-%m-%d').date()
    schedule = []
    day_names = ['월', '화', '수', '목', '금', '토', '일']

    for i in range(28):
        current_date = start + timedelta(days=i)
        day_name = day_names[current_date.weekday()]

        if day_name in request.restDays:
            continue

        task_title = f"{request.skill} 학습 Day {len(schedule) + 1}"
        materials = _get_materials_for_task(task_title)
        schedule.append({
            "date": current_date.isoformat(),
            "tasks": [
                {
                    "id": str(uuid.uuid4()),
                    "title": task_title,
                    "description": f"{request.skill} 학습을 진행합니다.",
                    "duration": f"{request.hourPerDay}시간",
                    "completed": False,
                    "related_materials": materials.get('related_materials', []),
                    "review_materials": materials.get('review_materials', [])
                }
            ]
        })

    plan = {
        "plan_name": f"{request.skill} 학습 계획",
        "total_duration": "4주",
        "daily_schedule": schedule
    }

    store.plans[user_id].append(plan)
    log_success(f"기본 학습 계획 생성 완료")
    return plan


@router.get("/date/{target_date}")
async def get_plans_by_date(
    target_date: str,
    current_user: Dict = Depends(get_current_user)
):
    """특정 날짜의 상세 계획 조회"""
    log_request("GET /plans/date", current_user['name'], f"date={target_date}")

    user_id = current_user['user_id']
    plans = store.plans.get(user_id, [])

    if not plans:
        return {"date": target_date, "tasks": [], "message": "아직 학습 계획이 없습니다."}

    current_plan = plans[-1]

    for day in current_plan.get('daily_schedule', []):
        if day['date'] == target_date:
            return {
                "date": target_date,
                "tasks": day['tasks'],
                "plan_name": current_plan.get('plan_name', '학습 계획'),
                "message": None
            }

    return {"date": target_date, "tasks": [], "message": "해당 날짜에 계획이 없습니다."}


@router.post("/task/update")
async def update_task(
    date: str,
    task_id: str,
    completed: bool,
    current_user: Dict = Depends(get_current_user)
):
    user_id = current_user['user_id']
    plans = store.plans.get(user_id, [])

    if not plans:
        raise HTTPException(status_code=404, detail="No plans found")

    current_plan = plans[-1]

    for day in current_plan['daily_schedule']:
        if day['date'] == date:
            for task in day['tasks']:
                if task['id'] == task_id:
                    task['completed'] = completed
                    log_success(f"태스크 업데이트: {task['title']} → {'완료' if completed else '미완료'}")
                    return {"success": True}

    raise HTTPException(status_code=404, detail="Task not found")
