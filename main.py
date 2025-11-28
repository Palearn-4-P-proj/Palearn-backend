# Backend/main.py
"""Palearn API 메인 진입점"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from .utils.logger import Colors
from .routers import auth, quiz, profile, home, plans, recommend, friends, notifications, review, plan_apply

app = FastAPI(title="Palearn API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(quiz.router)
app.include_router(profile.router)
app.include_router(home.router)
app.include_router(plans.router)
app.include_router(recommend.router)
app.include_router(friends.router)
app.include_router(notifications.router)
app.include_router(review.router)
app.include_router(plan_apply.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/")
async def root():
    return {"message": "Palearn API Server", "version": "1.0.0", "docs": "/docs"}


@app.on_event("startup")
async def startup_event():
    print(f"""
{Colors.CYAN}{'='*70}

    ____        _
   |  _ \\ __ _| | ___  __ _ _ __ _ __
   | |_) / _` | |/ _ \\/ _` | '__| '_ \\
   |  __/ (_| | |  __/ (_| | |  | | | |
   |_|   \\__,_|_|\\___|\\__,_|_|  |_| |_|

   Backend Server v1.0.0 (Modular)

{'='*70}{Colors.ENDC}

{Colors.GREEN}✓ [SERVER READY]{Colors.ENDC} http://localhost:8000
{Colors.BLUE}ℹ [API DOCS]{Colors.ENDC}     http://localhost:8000/docs

{Colors.YELLOW}━━━ 모듈 구조 ━━━{Colors.ENDC}
  routers/
     auth.py        - 인증 (회원가입/로그인)
     quiz.py        - 퀴즈
     profile.py     - 프로필
     home.py        - 홈
     plans.py       - 학습 계획
     recommend.py   - 강좌 추천
     friends.py     - 친구
     notifications.py - 알림
     review.py      - 복습 자료

  services/
     store.py       - 데이터 저장소
     gpt_service.py - GPT 호출

  utils/
     logger.py      - 로깅

{Colors.CYAN}대기 중... Flutter 앱에서 요청을 보내주세요!{Colors.ENDC}
""")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
