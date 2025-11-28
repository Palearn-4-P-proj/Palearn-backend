# Backend/utils/logger.py
"""터미널 컬러 로깅 유틸리티"""

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[35m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def log_divider():
    print(f"{Colors.CYAN}{'─'*70}{Colors.ENDC}")


def log_request(endpoint: str, user: str = "Anonymous", details: str = ""):
    """API 요청 로깅"""
    print(f"\n{Colors.CYAN}┌{'─'*68}┐{Colors.ENDC}")
    print(f"{Colors.CYAN}│{Colors.ENDC} {Colors.BOLD}[REQUEST]{Colors.ENDC} {endpoint}")
    print(f"{Colors.CYAN}│{Colors.ENDC} {Colors.YELLOW}User:{Colors.ENDC} {user}")
    if details:
        print(f"{Colors.CYAN}│{Colors.ENDC} {Colors.YELLOW}Details:{Colors.ENDC} {details}")
    print(f"{Colors.CYAN}└{'─'*68}┘{Colors.ENDC}")


def log_success(message: str):
    """성공 로깅"""
    print(f"{Colors.GREEN}✓ [SUCCESS]{Colors.ENDC} {message}")


def log_error(message: str):
    """에러 로깅"""
    print(f"{Colors.RED}✗ [ERROR]{Colors.ENDC} {message}")


def log_info(message: str):
    """정보 로깅"""
    print(f"{Colors.BLUE}ℹ [INFO]{Colors.ENDC} {message}")


def log_gpt(prompt_preview: str, response_preview: str):
    """GPT 요청/응답 로깅"""
    print(f"\n{Colors.MAGENTA}┌{'─'*68}┐{Colors.ENDC}")
    print(f"{Colors.MAGENTA}│{Colors.ENDC} {Colors.BOLD}[GPT REQUEST]{Colors.ENDC}")
    print(f"{Colors.MAGENTA}│{Colors.ENDC} Prompt: {prompt_preview[:100]}...")
    print(f"{Colors.MAGENTA}├{'─'*68}┤{Colors.ENDC}")
    print(f"{Colors.MAGENTA}│{Colors.ENDC} {Colors.BOLD}[GPT RESPONSE]{Colors.ENDC}")
    lines = response_preview[:500].split('\n')
    for line in lines[:10]:
        print(f"{Colors.MAGENTA}│{Colors.ENDC} {line[:66]}")
    if len(response_preview) > 500:
        print(f"{Colors.MAGENTA}│{Colors.ENDC} ... (총 {len(response_preview)} 글자)")
    print(f"{Colors.MAGENTA}└{'─'*68}┘{Colors.ENDC}")


def log_navigation(user: str, screen: str):
    """사용자 화면 이동 로깅"""
    print(f"{Colors.YELLOW}→ [NAVIGATION]{Colors.ENDC} {Colors.BOLD}{user}{Colors.ENDC} → {Colors.UNDERLINE}{screen}{Colors.ENDC}")


def log_stage(stage_num: int, stage_name: str, user: str = ""):
    """사용자 단계 로깅"""
    stages = {
        1: "🔐 회원가입",
        2: "🔑 로그인",
        3: "🏠 홈 화면",
        4: "📝 퀴즈 시작",
        5: "✅ 퀴즈 채점",
        6: "📚 강좌 추천",
        7: "📋 계획 생성",
        8: "👥 친구 목록",
        9: "🔔 알림 확인",
        10: "👤 프로필"
    }
    emoji_stage = stages.get(stage_num, f"📍 {stage_name}")
    print(f"\n{Colors.YELLOW}{'='*70}{Colors.ENDC}")
    print(f"{Colors.YELLOW}  STAGE {stage_num}: {emoji_stage}{Colors.ENDC}")
    print(f"{Colors.YELLOW}  User: {user}{Colors.ENDC}")
    print(f"{Colors.YELLOW}{'='*70}{Colors.ENDC}\n")
