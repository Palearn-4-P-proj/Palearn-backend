from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from config.settings import settings

# 라우터 임포트
from routers import auth, users, plans, quiz, friends, recommendations

load_dotenv()

app = FastAPI(
    title="palearn API",
    description="AI 학습 계획 관리 백엔드 (GPT-4o 통합)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정 (Flutter 앱과 통신)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB 연결
@app.on_event("startup")
async def startup_db():
    app.mongodb_client = AsyncIOMotorClient(settings.mongodb_url)
    app.mongodb = app.mongodb_client[settings.db_name]
    print(f"✅ MongoDB 연결 성공: {settings.db_name}")
    print(f"✅ OpenAI 모델: {settings.openai_model}")

@app.on_event("shutdown")
async def shutdown_db():
    app.mongodb_client.close()
    print("❌ MongoDB 연결 종료")

# 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["🔐 인증"])
app.include_router(users.router, prefix="/api/users", tags=["👤 사용자"])
app.include_router(plans.router, prefix="/api/plans", tags=["📚 학습계획"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["📝 퀴즈"])
app.include_router(friends.router, prefix="/api/friends", tags=["👥 친구"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["🎯 추천"])

@app.get("/", tags=["서버"])
async def root():
    return {
        "message": "palearn API 서버 실행중 🚀",
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", tags=["서버"])
async def health_check():
    return {"status": "ok", "database": "connected"}