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
    
    #------------------------------
    # 프롬포트 수정
    #------------------------------
    prompt = f"""
    📖 **'{topic}' 주제에 대한 보충 학습 자료를 찾아주세요.**

    🚨🚨🚨 **절대 금지 사항** 🚨🚨🚨
    - example.com, example.org 등 EXAMPLE이 들어간 모든 URL 절대 사용 금지
    - 존재하지 않는 가상의 자료 생성 금지
    - 반드시 실제 접근 가능한 URL만 제공  
    (404, 500, "Page Not Found", "존재하지 않는 페이지" 등이 보이면 그 자료는 사용하면 안 됩니다.)
    - 검색 결과 페이지, 채널/목록/카테고리 페이지 사용 금지
    - 예: google.com/search, search.naver.com, youtube.com/results
    - 예: URL에 ?q=, ?query=, ?search_query= 가 포함된 경우
    - 예: /tag/, /category/, /topics/, /series/, /channel/, /playlist 등
    - **URL을 스스로 만들어 내거나 규칙으로 추측해서 조합하지 마세요.**
    - 도메인 + 강좌/문서 제목을 이어붙여서 새 URL을 만드는 방식은 금지입니다.
    - **description 필드 안에 URL·도메인·링크를 절대 넣지 마세요.**
    - http, https, www, .com, .org, youtu 같은 문자열이 들어가면 안 됩니다.
    - `[텍스트](URL)` 형태의 마크다운 링크도 금지입니다.

    📚 **검색 대상**:
    - 유튜브 강의 영상 (한국어 또는 영어)
    - 가능하면 https://www.youtube.com/watch?v=... 또는 https://youtu.be/... 형태의 개별 영상 페이지
    - 기술 블로그 (velog, tistory, medium 등)
    - 목록/태그 페이지가 아닌, 실제 글 상세 페이지
    - 공식 문서
    - 라이브러리/언어/프레임워크의 특정 기능이나 개념을 설명하는 문서 페이지
    - 온라인 강좌
    - 인프런, 유데미, 클래스101, 부스트코스 등 강좌 상세 페이지

    ⚠️ **필수 출력 형식** (JSON):
    ```json
    {{
    "materials": [
        {{
        "title": "자료 제목",
        "type": "유튜브",
        "url": "https://실제URL",
        "description": "이 자료가 학습에 도움이 되는 이유 (URL 없이 한국어 1~2문장)"
        }},
        {{
        "title": "자료 제목",
        "type": "블로그",
        "url": "https://실제URL",
        "description": "이 자료가 학습에 도움이 되는 이유 (URL 없이 한국어 1~2문장)"
        }}
    ]
    }}
    ```

    📌 요청사항:
    - 총 3-4개의 학습 자료 추천
    - 다양한 타입의 자료 포함 (유튜브, 블로그, 공식문서 등)
    - 반드시 한국어 또는 영어로 된 실제 자료
    - title과 description은 한국어로 자연스럽게 작성
    - description에는 어떤 형태의 URL·도메인·링크도 넣지 말 것
    - URL은 반드시 실제로 접속이 되는 상세 페이지 URL만 사용 (검색·목록·채널 페이지 금지)
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

    #------------------------------
    # 프롬포트 수정
    #------------------------------
    prompt = f"""[시스템 지시]
당신은 개인 맞춤형 학습 플래너입니다.
사용자의 목표와 하루 공부 시간, 쉬는 요일을 고려하여 4주짜리 학습 일정을 설계합니다.
반드시 아래 규칙과 출력 형식을 지키고, **오직 JSON만** 출력해야 합니다.

[입력 정보]
- 스킬(skill): "{request.skill}"
- 하루 공부 시간(hourPerDay): {request.hourPerDay}시간
- 시작 날짜(startDate): {request.startDate} (형식: YYYY-MM-DD 또는 ISO8601)
- 쉬는 요일(restDays): {', '.join(request.restDays) if request.restDays else '없음'}
- 학습자 수준(selfLevel): {request.selfLevel}

[학습 계획 설계 규칙]

1. 기간 규칙
- 학습 계획 전체 기간은 시작 날짜({request.startDate})부터 4주(28일)입니다.
- daily_schedule에 포함되는 날짜는 시작 날짜 이후 28일 범위 안에서만 선택해야 합니다.
- 쉬는 요일(restDays)에 해당하는 날짜는 daily_schedule에 넣지 않습니다.

2. 날짜 및 정렬 규칙
- daily_schedule의 각 원소는 하나의 날짜를 나타냅니다.
- 각 날짜는 "date": "YYYY-MM-DD" 형식의 문자열이어야 합니다.
- 같은 날짜가 두 번 이상 등장하면 안 됩니다.
- 날짜는 시작 날짜부터 끝 날짜까지 시간 순(오름차순)으로 정렬해야 합니다.

3. 하루 공부 시간 규칙
- 각 날짜의 tasks에 있는 모든 duration 시간의 합이 **반드시 {request.hourPerDay}시간 이하여야 합니다.**
- duration은 "1시간", "30분"처럼 사람이 읽기 쉬운 형식으로 작성하되,
  하루 총합이 {request.hourPerDay}시간을 넘지 않도록 조절하세요.
- 하루에 2~3개의 구체적인 학습 태스크를 배정하는 것을 기본 원칙으로 합니다.
  (예: 30분~1시간짜리 태스크 2~3개)

4. 태스크 내용 규칙
- title에는 그날 구체적으로 할 학습 내용을 적습니다.
  (예: "파이썬 리스트와 튜플 개념 정리", "딥러닝 기본 용어 복습", "{request.skill} 실습 프로젝트 진행" 등)
- description에는 학습 방법이나 범위를 1~2문장으로 구체적으로 적습니다.
  (예: "공식 문서를 읽으며 주요 메서드를 정리하고 예제 코드를 따라 해보세요.")
- duration은 사람이 읽기 쉬운 시간 표현을 사용합니다. (예: "30분", "1시간", "1시간 30분")
- completed 값은 항상 false로 초기화합니다.
- id는 고유한 문자열(예: UUID 형식)을 사용합니다. (서버에서 다시 생성될 수 있지만, 일단 넣어두세요.)

5. 난이도/진행 흐름 규칙
- selfLevel과 스킬에 맞게, 초반에는 기초 개념 → 중반에 응용/실습 → 후반에 프로젝트/정리 순서로 구성합니다.
- 예시 흐름:
  - 1주차: 완전 기초 개념 이해, 환경 설정, 기본 문법/기능
  - 2주차: 실습 위주의 예제, 작은 과제
  - 3주차: 심화 개념, 실전 문제 풀이
  - 4주차: 작은 프로젝트, 전체 내용 복습, 정리 노트 작성

[출력 형식 - 반드시 이 스키마를 따라야 합니다]

최종 응답은 아래 스키마를 따르는 **하나의 JSON 객체만** 포함해야 합니다.

- 최상위 객체 필수 필드:
  - "plan_name": 문자열 (기본적으로 "{request.skill} 학습 계획" 형식 권장)
  - "total_duration": 문자열 (항상 "4주")
  - "daily_schedule": 객체 배열

- daily_schedule의 각 원소(하루 계획)는 다음 필드를 가져야 합니다.
  - "date": "YYYY-MM-DD" 형식의 문자열
  - "tasks": 태스크 객체 배열 (길이 1 이상, 보통 2~3개)

- 각 task 객체는 다음 필드를 가져야 합니다.
  - "id": 문자열 (고유 식별자, 예: UUID 형태)
  - "title": 문자열 (그날의 구체적인 학습 주제)
  - "description": 문자열 (1~2문장 정도의 상세 설명)
  - "duration": 문자열 (예: "30분", "1시간", "1시간 30분")
  - "completed": 불리언 false

[엄격한 제약 사항]

- 마크다운 코드블록(```json 등)을 사용하지 말고, **오직 JSON만** 응답하세요.
- JSON 바깥에 설명 문장, 인삿말, 해설 등의 텍스트를 절대 포함하지 마세요.
- daily_schedule의 날짜는 시작 날짜({request.startDate}) 기준 4주(28일) 범위를 넘지 않도록 해야 합니다.
- 쉬는 요일({', '.join(request.restDays) if request.restDays else '없음'})에는 해당하는 날짜를 daily_schedule에서 제외해야 합니다.
- 각 날짜의 duration 총합은 {request.hourPerDay}시간 이하여야 합니다.

위 규칙을 모두 지킨 하나의 JSON 객체만 출력하세요.
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
