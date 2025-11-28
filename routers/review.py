# Backend/routers/review.py
"""복습 자료 관련 라우터"""

from fastapi import APIRouter, Depends
from typing import Dict, List
from datetime import date, timedelta

from ..services.store import store
from ..services.gpt_service import call_gpt, extract_json
from ..utils.logger import log_request, log_success, log_navigation, log_info
from .auth import get_current_user

router = APIRouter(prefix="/review", tags=["Review"])


@router.get("/yesterday")
async def get_review_materials(
    user_id: str = None,
    current_user: Dict = Depends(get_current_user)
):
    log_request("GET /review/yesterday", current_user['name'])
    log_navigation(current_user['name'], "복습 화면")

    uid = user_id or current_user['user_id']
    plans = store.plans.get(uid, [])

    if not plans:
        log_info("학습 계획이 없습니다")
        return {"materials": [], "topics": [], "message": "아직 학습 계획이 없습니다."}

    current_plan = plans[-1]
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    completed_topics = []
    for day in current_plan.get('daily_schedule', []):
        if day['date'] == yesterday:
            completed_topics = [t['title'] for t in day['tasks'] if t.get('completed', False)]
            break

    if not completed_topics:
        log_info("어제 완료한 학습 항목이 없습니다")
        return {"materials": [], "topics": [], "message": "어제 완료한 학습 항목이 없습니다."}

    topics_str = ', '.join(completed_topics)

    # Flask 기반 프롬프트 - 복습 자료 검색
    prompt = f"""
📖 **어제 학습하신 내용에 대한 복습 자료를 찾아드리겠습니다.**

🔍 **검색할 주제**: {topics_str}

🚨🚨🚨 **절대 금지 사항** 🚨🚨🚨
- example.com, example.org 등 EXAMPLE이 들어간 모든 URL 절대 사용 금지
- 존재하지 않는 가상의 자료 생성 금지
- 반드시 실제 접근 가능한 URL만 제공

📚 **검색 대상**:
- 유튜브 강의 영상
- 기술 블로그 (velog, tistory, medium 등)
- 공식 문서
- 온라인 강좌 (인프런, 유데미 등)

⚠️ **필수 출력 형식** (JSON):
```json
{{
  "materials": [
    {{
      "title": "자료 제목",
      "type": "유튜브",
      "url": "https://실제URL",
      "description": "이 자료가 복습에 도움이 되는 이유",
      "duration": "영상 길이 또는 예상 학습 시간"
    }},
    {{
      "title": "자료 제목",
      "type": "블로그",
      "url": "https://실제URL",
      "description": "이 자료가 복습에 도움이 되는 이유",
      "duration": "예상 읽기 시간"
    }}
  ]
}}
```

📌 **요청사항**:
- 총 5개의 복습 자료 추천
- 유튜브 영상 2개, 블로그/문서 2개, 기타(강좌/도서) 1개
- 각 자료에 대해 왜 복습에 도움이 되는지 description 포함
- 반드시 한국어 또는 영어로 된 실제 자료
"""

    response = call_gpt(prompt, use_search=True)
    data = extract_json(response)

    if data and 'materials' in data:
        valid_materials = [m for m in data['materials'] if 'example' not in m.get('url', '').lower()]
        if valid_materials:
            log_success(f"복습 자료 {len(valid_materials)}개 찾기 완료")
            return {
                "materials": valid_materials[:5],
                "topics": completed_topics,
                "message": f"'{topics_str}'에 대한 복습 자료입니다."
            }

    search_query = topics_str.replace(' ', '+').replace(',', '')
    log_info("GPT 응답 실패, 기본 검색 링크 반환")
    return {
        "materials": [
            {"title": f"{topics_str} - 유튜브 검색", "type": "유튜브", "url": f"https://www.youtube.com/results?search_query={search_query}", "description": "유튜브에서 관련 영상을 검색합니다.", "duration": "-"},
            {"title": f"{topics_str} - 네이버 블로그", "type": "블로그", "url": f"https://search.naver.com/search.naver?where=post&query={search_query}", "description": "네이버 블로그에서 관련 글을 검색합니다.", "duration": "-"},
            {"title": f"{topics_str} - 구글 검색", "type": "기타", "url": f"https://www.google.com/search?q={search_query}+강의", "description": "구글에서 관련 강의를 검색합니다.", "duration": "-"},
        ],
        "topics": completed_topics,
        "message": f"'{topics_str}'에 대한 검색 링크입니다."
    }


@router.get("/topics")
async def get_yesterday_topics(
    current_user: Dict = Depends(get_current_user)
):
    """어제 완료한 학습 주제 목록 조회"""
    log_request("GET /review/topics", current_user['name'])

    uid = current_user['user_id']
    plans = store.plans.get(uid, [])

    if not plans:
        return {"topics": [], "date": None}

    current_plan = plans[-1]
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    completed_topics = []
    for day in current_plan.get('daily_schedule', []):
        if day['date'] == yesterday:
            completed_topics = [
                {"title": t['title'], "completed": t.get('completed', False)}
                for t in day['tasks']
            ]
            break

    return {"topics": completed_topics, "date": yesterday}
