# Backend/services/gpt_service.py
"""OpenAI GPT 서비스"""

from openai import OpenAI
import json
import re
import os
from typing import Optional, Dict
from dotenv import load_dotenv

from ..utils.logger import log_info, log_error, log_gpt

load_dotenv()

# OpenAI 클라이언트 설정
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 모델 설정 - fallback 지원
OPENAI_MODEL_SEARCH_PRIMARY = "gpt-5-search-api"  # 1차 웹 검색용 모델
OPENAI_MODEL_SEARCH_FALLBACK = "gpt-4o-search-preview"  # 2차 fallback 모델
OPENAI_MODEL_NORMAL = "gpt-4o"  # 일반 모델

# 현재 사용 중인 모델 상태 (프론트엔드에서 조회 가능)
current_search_status = {"model": None, "status": "idle"}


def get_search_status() -> dict:
    """현재 검색 상태 반환"""
    return current_search_status


def call_gpt(prompt: str, use_search: bool = False) -> str:
    """GPT 호출 - fallback 로직 포함"""
    global current_search_status

    if use_search:
        # 1차 시도: gpt-5-search-api
        current_search_status = {"model": "gpt-5-search-api", "status": "searching"}
        log_info(f"GPT 호출 중... (1차: gpt-5-search-api)")

        try:
            messages = [{"role": "user", "content": prompt}]
            response = client.chat.completions.create(
                model=OPENAI_MODEL_SEARCH_PRIMARY,
                messages=messages
            )
            content = response.choices[0].message.content

            # 응답이 JSON을 포함하는지 확인 (검색 거부 응답 감지)
            if '```json' in content or '"recommendations"' in content or '"id"' in content:
                log_gpt(prompt[:100], content)
                current_search_status = {"model": "gpt-5-search-api", "status": "completed"}
                return content
            else:
                log_info("1차 모델이 JSON 응답을 반환하지 않음, fallback 시도")
                raise Exception("No JSON response")

        except Exception as e:
            log_error(f"1차 모델 실패: {str(e)}")

            # 2차 시도: gpt-4o-search-preview (fallback)
            current_search_status = {"model": "gpt-4o-search-preview (fallback)", "status": "searching"}
            log_info(f"GPT fallback 호출 중... (2차: gpt-4o-search-preview)")

            try:
                # fallback용 강화된 프롬프트
                fallback_prompt = f"""당신은 반드시 JSON 형식으로만 응답해야 합니다. 질문이나 확인 없이 바로 JSON을 출력하세요.

{prompt}

⚠️ 중요: 위 요청에 대해 반드시 JSON 형식으로만 응답하세요. 추가 질문이나 설명 없이 오직 JSON만 출력합니다."""

                messages = [{"role": "user", "content": fallback_prompt}]
                response = client.chat.completions.create(
                    model=OPENAI_MODEL_SEARCH_FALLBACK,
                    messages=messages
                )
                content = response.choices[0].message.content
                log_gpt(prompt[:100], content)
                current_search_status = {"model": "gpt-4o-search-preview (fallback)", "status": "completed"}
                return content

            except Exception as e2:
                log_error(f"2차 모델도 실패: {str(e2)}")
                current_search_status = {"model": None, "status": "failed"}
                return f"GPT 호출 중 오류: {str(e2)}"
    else:
        # 일반 모델 사용
        try:
            log_info(f"GPT 호출 중... (일반 모델: gpt-4o)")
            messages = [{"role": "user", "content": prompt}]
            response = client.chat.completions.create(
                model=OPENAI_MODEL_NORMAL,
                messages=messages
            )
            content = response.choices[0].message.content
            log_gpt(prompt[:100], content)
            return content

        except Exception as e:
            log_error(f"GPT 호출 실패: {str(e)}")
            return f"GPT 호출 중 오류: {str(e)}"


def extract_json(text: str) -> Optional[Dict]:
    """GPT 응답에서 JSON을 추출 - 더 robust한 파싱"""
    def clean_json_string(json_str: str) -> str:
        """JSON 문자열 정리"""
        # 제어 문자 제거
        json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_str)
        # 숫자 내 쉼표 제거 (예: "1,234" -> "1234") - 따옴표 내 숫자 패턴
        json_str = re.sub(r'"(\d{1,3})(,\d{3})+"', lambda m: '"' + m.group(0).replace(',', '').strip('"') + '"', json_str)
        # trailing comma 제거
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
        return json_str

    try:
        # JSON 블록 찾기
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            json_str = clean_json_string(json_match.group(1))
            return json.loads(json_str)

        # 중괄호로 시작하는 JSON 찾기
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_str = clean_json_string(json_match.group())
            return json.loads(json_str)
    except json.JSONDecodeError as e:
        log_error(f"JSON 파싱 실패: {e}")
        # 재시도: 더 공격적인 정리
        try:
            if json_match:
                json_str = json_match.group(1) if '```json' in text else json_match.group()
                # 모든 줄바꿈을 공백으로
                json_str = json_str.replace('\n', ' ').replace('\r', ' ')
                json_str = clean_json_string(json_str)
                return json.loads(json_str)
        except:
            log_error("재시도 파싱도 실패")
    return None
