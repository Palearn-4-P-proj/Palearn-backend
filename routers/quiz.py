# Backend/routers/quiz.py
"""퀴즈 관련 라우터"""

from fastapi import APIRouter, Depends
from typing import Dict

from ..models.schemas import QuizSubmitRequest
from ..services.store import store
from ..services.gpt_service import call_gpt, extract_json
from ..utils.logger import log_request, log_stage, log_success, log_navigation
from .auth import get_current_user

router = APIRouter(prefix="/quiz", tags=["Quiz"])


@router.get("/items")
async def get_quiz_items(
    skill: str = "general",
    level: str = "초급",
    limit: int = 10,
    current_user: Dict = Depends(get_current_user)
):
    log_request("GET /quiz/items", current_user['name'], f"skill={skill}, level={level}, limit={limit}")
    log_stage(4, "퀴즈 시작", current_user['name'])
    log_navigation(current_user['name'], "퀴즈 화면")

    # Flask 기반 프롬프트 - O/X 퀴즈 + explanation
    #------------------------------
    # 프롬포트 수정
    #------------------------------
    prompt = f"""[시스템 지시]
당신은 '{skill}' 분야의 개념 이해도를 점검하는 OX 퀴즈 출제기입니다.
반드시 규칙을 지키고, 오직 JSON만 출력해야 합니다.

🎯 목적:
- '{skill}' 분야를 학습하는 {level} 학습자의 이해도를 점검하는 OX 퀴즈 10개를 만듭니다.
- 모든 문항은 O(참) 또는 X(거짓)으로 명확하게 판단할 수 있어야 합니다.

✅ 난이도 규칙:
- {level} 수준(입문/초급/중급/고급)에 맞는 개념을 선택합니다.
- 기초 개념, 자주 헷갈리는 개념, 실무에서 자주 쓰이는 개념을 고루 섞어냅니다.

📌 문제 내용 규칙:
1. 각 문제는 하나의 명확한 주장/사실을 말해야 합니다.
2. 질문은 반드시 한국어 문장이어야 하고, 보통 평서문 형태로 작성합니다.
   (예: "~이다.", "~라고 할 수 있다." 등)
3. 질문에서 "O/X를 고르시오" 같은 문장은 쓰지 않습니다. 사실/주장만 제시합니다.
4. answerKey는 "O" 또는 "X" 둘 중 하나여야 합니다.
5. explanation에는 왜 O 또는 X인지, 개념을 이해하는 데 도움이 되도록 2~4문장 정도로 상세히 설명합니다.

📊 응답 형식 (반드시 이 스키마를 따라야 함):
- 반환값은 하나의 JSON 객체여야 합니다.
- 최상위 키는 "quizzes" 하나만 존재해야 합니다.
- "quizzes" 값은 길이 10인 배열이어야 합니다.
- "quizzes" 배열의 각 원소는 다음 필드를 가진 객체입니다:
  - "id": 1부터 10까지의 정수 (서로 모두 달라야 합니다)
  - "type": 문자열 "OX"
  - "question": 한국어 질문 문자열 (마침표 또는 물음표로 끝나는 자연스러운 문장)
  - "options": 빈 배열 [] (항상 비워 두세요)
  - "answerKey": "O" 또는 "X"
  - "explanation": 정답의 이유를 설명하는 한국어 문장 2~4개 정도

⚠️ 엄격한 제약:
- 반드시 퀴즈는 10개여야 합니다. (quizzes 배열 길이 = 10)
- "id" 값은 1,2,...,10 이어야 하며 중복되면 안 됩니다.
- "type"은 모든 문항에서 "OX" 여야 합니다.
- "options"는 모든 문항에서 빈 배열([])이어야 합니다.
- "answerKey"는 "O" 또는 "X" 이외의 값을 절대 사용하지 마세요.
- "explanation"에는 정답만 말하지 말고, 왜 그런지 개념을 풀어서 설명하세요.
- 마크다운, 코드블록, 설명 문장 없이 **오직 JSON만** 출력하세요.
"""


    response = call_gpt(prompt, use_search=False)
    data = extract_json(response)

    if data and 'quizzes' in data:
        store.quiz_answers[current_user['user_id']] = data['quizzes']
        log_success(f"퀴즈 {len(data['quizzes'])}개 생성 완료")
        return data['quizzes']

    # 기본 퀴즈 (폴백) - explanation 추가
    default_quizzes = [
        {"id": 1, "type": "OX", "question": "컴퓨터는 0과 1로 모든 연산을 처리한다.", "options": [], "answerKey": "O", "explanation": "컴퓨터는 이진법(Binary)을 사용하여 0과 1만으로 모든 데이터를 표현하고 연산합니다. 이를 디지털 연산이라고 합니다."},
        {"id": 2, "type": "OX", "question": "인터넷과 월드와이드웹(WWW)은 같은 의미이다.", "options": [], "answerKey": "X", "explanation": "인터넷은 컴퓨터들을 연결하는 네트워크 인프라이고, WWW는 인터넷 위에서 동작하는 서비스 중 하나입니다. WWW는 인터넷의 일부일 뿐입니다."},
        {"id": 3, "type": "OX", "question": "프로그래밍 언어는 기계어만 존재한다.", "options": [], "answerKey": "X", "explanation": "프로그래밍 언어는 기계어 외에도 어셈블리어(저급 언어), Python/Java/C++ 같은 고급 언어 등 다양하게 존재합니다."},
        {"id": 4, "type": "OX", "question": "RAM은 전원이 꺼지면 데이터가 사라지는 휘발성 메모리이다.", "options": [], "answerKey": "O", "explanation": "RAM(Random Access Memory)은 휘발성 메모리로, 전원이 꺼지면 저장된 데이터가 모두 사라집니다. 반면 SSD나 HDD는 비휘발성입니다."},
        {"id": 5, "type": "OX", "question": "HTML은 프로그래밍 언어이다.", "options": [], "answerKey": "X", "explanation": "HTML은 HyperText Markup Language의 약자로, 웹 페이지의 구조를 정의하는 '마크업 언어'입니다. 프로그래밍 언어처럼 로직을 처리하지 않습니다."},
        {"id": 6, "type": "OX", "question": "1바이트(Byte)는 8비트(bit)이다.", "options": [], "answerKey": "O", "explanation": "1바이트는 8비트로 구성됩니다. 비트는 0 또는 1의 최소 정보 단위이고, 바이트는 컴퓨터에서 문자 하나를 표현하는 기본 단위입니다."},
        {"id": 7, "type": "OX", "question": "CPU는 컴퓨터의 장기 저장 장치이다.", "options": [], "answerKey": "X", "explanation": "CPU(Central Processing Unit)는 컴퓨터의 '두뇌'로, 연산과 제어를 담당합니다. 장기 저장은 HDD, SSD 같은 저장 장치가 담당합니다."},
        {"id": 8, "type": "OX", "question": "운영체제(OS)는 하드웨어와 소프트웨어 사이를 중재하는 시스템 소프트웨어이다.", "options": [], "answerKey": "O", "explanation": "운영체제는 컴퓨터 하드웨어를 관리하고, 응용 프로그램이 하드웨어를 사용할 수 있도록 인터페이스를 제공하는 시스템 소프트웨어입니다."},
        {"id": 9, "type": "OX", "question": "IP 주소는 인터넷에서 컴퓨터를 식별하는 고유한 주소이다.", "options": [], "answerKey": "O", "explanation": "IP(Internet Protocol) 주소는 네트워크상에서 각 장치를 식별하기 위한 고유한 숫자 주소입니다. IPv4는 32비트, IPv6는 128비트를 사용합니다."},
        {"id": 10, "type": "OX", "question": "클라우드 컴퓨팅은 반드시 인터넷 연결 없이도 사용할 수 있다.", "options": [], "answerKey": "X", "explanation": "클라우드 컴퓨팅은 인터넷을 통해 원격 서버의 리소스를 사용하는 기술이므로, 기본적으로 인터넷 연결이 필요합니다."},
    ]
    store.quiz_answers[current_user['user_id']] = default_quizzes
    return default_quizzes[:limit]


@router.post("/grade")
async def grade_quiz(request: QuizSubmitRequest, current_user: Dict = Depends(get_current_user)):
    log_request("POST /quiz/grade", current_user['name'], f"answers={len(request.answers)}개")
    log_stage(5, "퀴즈 채점", current_user['name'])

    saved_quizzes = store.quiz_answers.get(current_user['user_id'], [])
    answer_map = {q['id']: q['answerKey'] for q in saved_quizzes}

    total = len(request.answers)
    correct = 0
    detail = []

    for answer in request.answers:
        correct_answer = answer_map.get(answer.id, "")
        user_answer = answer.userAnswer.strip()
        expected = correct_answer.strip()

        # 비교 (대소문자 무시, 공백 정리)
        is_correct = user_answer.lower() == expected.lower()

        if is_correct:
            correct += 1
        detail.append(is_correct)

    rate = correct / total if total > 0 else 0

    if rate >= 0.8:
        level = "고급"
    elif rate >= 0.6:
        level = "중급"
    else:
        level = "초급"

    log_success(f"퀴즈 채점 완료: {correct}/{total} ({rate*100:.0f}%) → 레벨: {level}")
    log_navigation(current_user['name'], "퀴즈 결과 화면")

    return {
        "total": total,
        "correct": correct,
        "detail": detail,
        "rate": rate,
        "level": level
    }
