# Backend/services/web_search.py
"""웹 검색 서비스 - 유튜브/블로그 링크 검색"""

import os
import requests
from typing import List, Dict
from urllib.parse import quote_plus
from dotenv import load_dotenv

from ..utils.logger import log_info, log_error, log_success

load_dotenv()

# Google API 설정 (선택적)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def search_youtube(query: str, max_results: int = 1) -> List[Dict]:
    """유튜브에서 강의 영상 검색"""
    log_info(f"유튜브 검색: {query}")

    # YouTube Data API 사용 (API 키가 있는 경우)
    if YOUTUBE_API_KEY:
        try:
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet",
                "q": f"{query} 강의 튜토리얼",
                "type": "video",
                "maxResults": max_results,
                "key": YOUTUBE_API_KEY,
                "relevanceLanguage": "ko",
                "videoDuration": "medium"  # 4-20분 영상
            }
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get("items", []):
                    video_id = item["id"]["videoId"]
                    title = item["snippet"]["title"]
                    results.append({
                        "title": title,
                        "type": "유튜브",
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "description": f"'{query}' 관련 유튜브 강의"
                    })
                if results:
                    log_success(f"유튜브 검색 성공: {len(results)}개")
                    return results
        except Exception as e:
            log_error(f"YouTube API 오류: {e}")

    # API 없으면 검색 URL 반환
    search_query = quote_plus(f"{query} 강의")
    return [{
        "title": f"{query} 강의 영상",
        "type": "유튜브",
        "url": f"https://www.youtube.com/results?search_query={search_query}",
        "description": "유튜브에서 관련 강의를 검색합니다"
    }]


def search_blog(query: str, max_results: int = 1) -> List[Dict]:
    """블로그에서 학습 자료 검색"""
    log_info(f"블로그 검색: {query}")

    # Google Custom Search API 사용 (API 키가 있는 경우)
    if GOOGLE_API_KEY and GOOGLE_CSE_ID:
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": GOOGLE_API_KEY,
                "cx": GOOGLE_CSE_ID,
                "q": f"{query} 블로그 튜토리얼",
                "num": max_results,
                "lr": "lang_ko"
            }
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get("items", []):
                    results.append({
                        "title": item.get("title", ""),
                        "type": "블로그",
                        "url": item.get("link", ""),
                        "description": item.get("snippet", "")[:100]
                    })
                if results:
                    log_success(f"블로그 검색 성공: {len(results)}개")
                    return results
        except Exception as e:
            log_error(f"Google Search API 오류: {e}")

    # API 없으면 검색 URL 반환
    search_query = quote_plus(f"{query} 블로그 강의")
    return [{
        "title": f"{query} 학습 블로그",
        "type": "블로그",
        "url": f"https://www.google.com/search?q={search_query}",
        "description": "구글에서 관련 블로그를 검색합니다"
    }]


def search_materials_for_topic(topic: str) -> Dict[str, List[Dict]]:
    """특정 주제에 대한 학습 자료 검색 (유튜브 1개 + 블로그 1개)"""
    log_info(f"학습 자료 검색 시작: {topic}")

    youtube_results = search_youtube(topic, max_results=1)
    blog_results = search_blog(topic, max_results=1)

    return {
        "related_materials": youtube_results + blog_results,
        "review_materials": youtube_results + blog_results
    }


def batch_search_materials(topics: List[str]) -> Dict[str, Dict[str, List[Dict]]]:
    """여러 주제에 대한 학습 자료 일괄 검색"""
    log_info(f"일괄 검색 시작: {len(topics)}개 주제")

    results = {}
    for topic in topics:
        try:
            results[topic] = search_materials_for_topic(topic)
        except Exception as e:
            log_error(f"검색 실패 ({topic}): {e}")
            # 실패 시 기본 검색 URL
            search_query = quote_plus(topic)
            results[topic] = {
                "related_materials": [
                    {"title": f"{topic} 강의", "type": "유튜브", "url": f"https://www.youtube.com/results?search_query={search_query}+강의", "description": "유튜브 검색"},
                    {"title": f"{topic} 블로그", "type": "블로그", "url": f"https://www.google.com/search?q={search_query}+블로그", "description": "구글 검색"}
                ],
                "review_materials": [
                    {"title": f"{topic} 복습", "type": "유튜브", "url": f"https://www.youtube.com/results?search_query={search_query}+강의", "description": "유튜브 검색"},
                    {"title": f"{topic} 정리", "type": "블로그", "url": f"https://www.google.com/search?q={search_query}+정리", "description": "구글 검색"}
                ]
            }

    log_success(f"일괄 검색 완료: {len(results)}개")
    return results
