from openai import OpenAI
from config.settings import settings
from typing import List, Dict, Any
import json

client = OpenAI(api_key=settings.openai_api_key)

class LLMService:
    
    @staticmethod
    async def generate_learning_plan(
        skill: str,
        level: str,
        hour_per_day: str,
        rest_days: List[str]
    ) -> Dict[str, Any]:
        """학습 계획 생성"""
        
        prompt = f"""
당신은 전문 교육 컨설턴트입니다. 다음 조건에 맞는 학습 계획을 생성해주세요.

**학습 정보:**
- 스킬: {skill}
- 현재 수준: {level}
- 하루 학습 시간: {hour_per_day}
- 쉬는 요일: {', '.join(rest_days) if rest_days else '없음'}

**생성할 내용:**
1. Daily Tasks (10개): 매일 수행할 구체적인 작업
2. Weekly Goals (4개): 주간 목표
3. Monthly Milestones (3개): 월간 마일스톤

**출력 형식 (JSON):**
{{
    "daily_tasks": [
        {{"title": "작업명", "description": "설명"}},
        {{"title": "작업명", "description": "설명"}},
        {{"title": "작업명", "description": "설명"}},
        {{"title": "작업명", "description": "설명"}},
        {{"title": "작업명", "description": "설명"}},
        {{"title": "작업명", "description": "설명"}},
        {{"title": "작업명", "description": "설명"}},
        {{"title": "작업명", "description": "설명"}},
        {{"title": "작업명", "description": "설명"}},
        {{"title": "작업명", "description": "설명"}}
    ],
    "weekly_goals": [
        {{"title": "목표명", "description": "설명", "tasks": ["세부 작업1", "세부 작업2"]}},
        {{"title": "목표명", "description": "설명", "tasks": ["세부 작업1", "세부 작업2"]}},
        {{"title": "목표명", "description": "설명", "tasks": ["세부 작업1", "세부 작업2"]}},
        {{"title": "목표명", "description": "설명", "tasks": ["세부 작업1", "세부 작업2"]}}
    ],
    "monthly_milestones": [
        {{"title": "마일스톤명", "description": "설명", "goals": ["목표1", "목표2"]}},
        {{"title": "마일스톤명", "description": "설명", "goals": ["목표1", "목표2"]}},
        {{"title": "마일스톤명", "description": "설명", "goals": ["목표1", "목표2"]}}
    ]
}}

반드시 위 JSON 형식으로만 응답하세요.
"""
        
        try:
            print(f"🔍 [INFO] GPT-4o로 학습 계획 생성 중... (스킬: {skill}, 수준: {level})")
            
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content
            print(f"✅ [GPT Response Length]: {len(content)} characters")
            
            # JSON 파싱
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"❌ [GPT Error]: {str(e)}")
            return {
                "daily_tasks": [
                    {"title": f"{skill} 기초 개념 학습", "description": "기본 용어와 개념 이해하기"},
                    {"title": f"{skill} 환경 설정", "description": "필요한 도구 설치 및 설정"},
                    {"title": "첫 실습 프로젝트", "description": "간단한 예제 따라하기"},
                    {"title": "핵심 개념 복습", "description": "배운 내용 정리하기"},
                    {"title": "실습 문제 풀이", "description": "기초 문제 해결하기"},
                    {"title": "심화 개념 학습", "description": "다음 단계 내용 학습"},
                    {"title": "프로젝트 구현", "description": "작은 프로젝트 만들기"},
                    {"title": "코드 리뷰", "description": "작성한 코드 점검하기"},
                    {"title": "오류 수정", "description": "버그 찾아 고치기"},
                    {"title": "주간 정리", "description": "이번 주 학습 내용 복습"}
                ],
                "weekly_goals": [
                    {"title": "1주차: 기초", "description": "기본 개념", "tasks": ["개념", "실습"]},
                    {"title": "2주차: 실습", "description": "실전 연습", "tasks": ["예제", "문제"]},
                    {"title": "3주차: 심화", "description": "고급 내용", "tasks": ["심화", "프로젝트"]},
                    {"title": "4주차: 완성", "description": "최종 정리", "tasks": ["복습", "완성"]}
                ],
                "monthly_milestones": [
                    {"title": "1개월: 기초", "description": f"{skill} 기본", "goals": ["이론", "실습"]},
                    {"title": "2개월: 응용", "description": "실전 프로젝트", "goals": ["프로젝트", "완성"]},
                    {"title": "3개월: 심화", "description": "고급 단계", "goals": ["심화", "포트폴리오"]}
                ]
            }
    
    @staticmethod
    async def generate_quiz(skill: str, level: str) -> List[Dict[str, Any]]:
        """퀴즈 생성"""
        
        prompt = f"""
{skill}에 대한 {level} 수준 퀴즈를 10문제 생성해주세요.

**문제 구성:**
- OX 문제: 3개
- 객관식: 4개
- 단답형: 3개

**JSON 형식:**
{{
    "questions": [
        {{"id": 1, "type": "OX", "question": "질문", "options": [], "answer_key": "O"}},
        {{"id": 2, "type": "MULTI", "question": "질문", "options": ["1","2","3","4"], "answer_key": "1"}},
        {{"id": 3, "type": "SHORT", "question": "질문", "options": [], "answer_key": "답"}}
    ]
}}

JSON만 응답하세요.
"""
        
        try:
            print(f"🔍 [INFO] GPT-4o로 퀴즈 생성 중... (스킬: {skill}, 수준: {level})")
            
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content
            print(f"✅ [GPT Response Length]: {len(content)} characters")
            
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            return result.get("questions", [])
            
        except Exception as e:
            print(f"❌ [GPT Error]: {str(e)}")
            return [
                {"id": 1, "type": "OX", "question": f"{skill}은 프로그래밍 언어이다.", "options": [], "answer_key": "O"},
                {"id": 2, "type": "OX", "question": f"{skill}은 {level} 수준에서 어렵다.", "options": [], "answer_key": "X"},
                {"id": 3, "type": "OX", "question": f"{skill} 학습에 실습이 중요하다.", "options": [], "answer_key": "O"},
                {"id": 4, "type": "MULTI", "question": f"{skill}의 특징은?", "options": ["특징1", "특징2", "특징3", "특징4"], "answer_key": "특징1"},
                {"id": 5, "type": "MULTI", "question": f"{skill} 학습 방법은?", "options": ["방법1", "방법2", "방법3", "방법4"], "answer_key": "방법1"},
                {"id": 6, "type": "MULTI", "question": f"{skill} 사용 분야는?", "options": ["분야1", "분야2", "분야3", "분야4"], "answer_key": "분야1"},
                {"id": 7, "type": "MULTI", "question": f"{skill}의 장점은?", "options": ["장점1", "장점2", "장점3", "장점4"], "answer_key": "장점1"},
                {"id": 8, "type": "SHORT", "question": f"{skill}의 기본 개념은?", "options": [], "answer_key": "개념"},
                {"id": 9, "type": "SHORT", "question": f"{skill} 학습에 필요한 것?", "options": [], "answer_key": "실습"},
                {"id": 10, "type": "SHORT", "question": f"{skill} 배우는 이유는?", "options": [], "answer_key": "성장"}
            ]
    
    @staticmethod
    async def recommend_courses(
        skill: str,
        level: str,
        quiz_details: List[bool]
    ) -> Dict[str, Any]:
        """강좌 추천 (웹 검색)"""
        
        correct_rate = sum(quiz_details) / len(quiz_details) if quiz_details else 0
        
        prompt = f"""
🔍 **웹 검색 필수** 🔍
- 실제 강좌만 찾으세요
- example.com 사용 금지
- Coursera, Udemy, 인프런 등 실제 플랫폼만

학습자: {skill} / {level} / 정답률 {correct_rate:.1%}

실제 강좌 3개 추천해주세요.

**JSON 형식:**
{{
    "courses": [
        {{
            "id": "1",
            "title": "실제 강좌명",
            "provider": "플랫폼",
            "weeks": 6,
            "free": true,
            "summary": "설명",
            "syllabus": ["1강","2강","3강","4강","5강"],
            "url": "실제URL"
        }}
    ],
    "reasoning": "추천 이유"
}}

실제 강좌만! JSON만!
"""
        
        try:
            print(f"🔍 [INFO] GPT-4o로 강좌 추천 중... (스킬: {skill}, 수준: {level})")
            
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content
            
            if 'example' in content.lower():
                print("⚠️ [WARNING] example 링크 발견!")
            
            print(f"✅ [GPT Response Length]: {len(content)} characters")
            
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"❌ [GPT Error]: {str(e)}")
            return {
                "courses": [
                    {
                        "id": "1",
                        "title": f"{skill} 기초",
                        "provider": "온라인",
                        "weeks": 6,
                        "free": False,
                        "summary": f"{skill} 학습",
                        "syllabus": ["1강","2강","3강","4강","5강"],
                        "url": "https://www.example.com"
                    }
                ],
                "reasoning": f"{level} 수준 추천"
            }