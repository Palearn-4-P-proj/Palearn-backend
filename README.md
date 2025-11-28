# Palearn Backend API

FastAPI 기반 백엔드 서버입니다. GPT-4o Search Preview 모델을 사용하여 실제 강좌/도서를 웹 검색으로 추천합니다.

## 설치 및 실행

### 1. 가상환경 생성 (권장)
```bash
cd Backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정
`.env` 파일이 이미 생성되어 있습니다. 필요시 API 키를 수정하세요.

### 4. 서버 실행
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 http://localhost:8000 에서 접속 가능합니다.

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 주요 엔드포인트

### 인증
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /auth/signup | 회원가입 |
| POST | /auth/login | 로그인 |
| POST | /auth/logout | 로그아웃 |

### 프로필
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /profile/me | 내 프로필 조회 |
| POST | /profile/update | 프로필 수정 |

### 홈 & 계획
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /home/header | 홈 헤더 정보 |
| GET | /plans?scope=daily | 계획 목록 (daily/weekly/monthly) |
| GET | /plans/review | 복습 항목 |
| POST | /plans/generate | AI 계획 생성 |

### 퀴즈
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /quiz/items?skill=python&level=초급 | 퀴즈 문제 조회 |
| POST | /quiz/grade | 퀴즈 채점 |

### 강좌 추천
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /recommend/courses?skill=python&level=초급 | 강좌 추천 (GPT 웹검색) |
| POST | /recommend/select | 강좌 선택 |
| POST | /plan/apply_recommendation | 추천 기반 계획 생성 |

### 친구
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /friends | 친구 목록 |
| POST | /friends/add | 친구 추가 (코드로) |
| GET | /friends/{id}/plans | 친구 계획 조회 |

### 알림
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /notifications | 알림 조회 |
| POST | /notifications/read | 알림 읽음 처리 |

### 복습
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /review/yesterday | 어제 복습 자료 (GPT 웹검색) |

## Flutter 앱 연동

`lib/data/api_service.dart` 파일을 사용하여 Flutter 앱에서 API를 호출합니다.

```dart
import 'package:plearn/data/api_service.dart';

// 로그인
final result = await AuthService.login(
  email: 'user@example.com',
  password: 'password123',
);

// 강좌 추천 (GPT 웹검색)
final courses = await RecommendService.getCourses(
  skill: 'Python',
  level: '초급',
);

// 계획 생성
final plan = await PlanService.generatePlan(
  skill: 'Python',
  hourPerDay: 2.0,
  startDate: '2025-01-01',
  restDays: ['토', '일'],
  selfLevel: '초급',
);
```

## 기술 스택

- **FastAPI**: 고성능 Python 웹 프레임워크
- **OpenAI GPT-4o Search Preview**: 웹 검색 기반 AI 응답
- **Pydantic**: 데이터 검증
- **Uvicorn**: ASGI 서버

## 참고사항

- 현재 데이터는 인메모리에 저장됩니다 (서버 재시작시 초기화)
- 프로덕션 환경에서는 PostgreSQL/MongoDB 등 DB 연동 필요
- API 키는 `.env` 파일에서 관리됩니다
