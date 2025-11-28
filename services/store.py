# Backend/services/store.py
"""인메모리 데이터 저장소"""

from typing import Dict, List, Optional
from datetime import datetime
import uuid
import hashlib


class DataStore:
    def __init__(self):
        self.users: Dict[str, Dict] = {}
        self.tokens: Dict[str, str] = {}
        self.friend_codes: Dict[str, str] = {}
        self.friendships: Dict[str, List[str]] = {}
        self.plans: Dict[str, List[Dict]] = {}
        self.notifications: Dict[str, Dict[str, List[str]]] = {}
        self.quiz_answers: Dict[str, List[Dict]] = {}

    def create_user(self, username: str, email: str, password: str, name: str, birth: str, photo_url: str = None) -> Optional[Dict]:
        for user in self.users.values():
            if user['email'] == email:
                return None

        user_id = str(uuid.uuid4())
        friend_code = hashlib.md5(user_id.encode()).hexdigest()[:8].upper()

        self.users[user_id] = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'password': hashlib.sha256(password.encode()).hexdigest(),
            'name': name,
            'birth': birth,
            'photo_url': photo_url,
            'friend_code': friend_code,
            'created_at': datetime.now().isoformat()
        }

        self.friend_codes[friend_code] = user_id
        self.friendships[user_id] = []
        self.plans[user_id] = []
        self.notifications[user_id] = {'new': [], 'old': []}
        self.quiz_answers[user_id] = []

        return self.users[user_id]

    def login(self, email: str, password: str) -> Optional[Dict]:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        for user_id, user in self.users.items():
            if user['email'] == email and user['password'] == password_hash:
                token = str(uuid.uuid4())
                self.tokens[token] = user_id
                return {'token': token, 'user_id': user_id, 'name': user['name']}
        return None

    def get_user_by_token(self, token: str) -> Optional[Dict]:
        user_id = self.tokens.get(token)
        if user_id:
            return self.users.get(user_id)
        return None

    def get_user_id_by_token(self, token: str) -> Optional[str]:
        return self.tokens.get(token)

    def logout(self, token: str) -> bool:
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False


# 싱글톤 인스턴스
store = DataStore()
