import uuid
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import HTTPException, Response, Request, Cookie, status


# Секретный ключ для подписи (в реальном приложении должен храниться в переменных окружения)
SECRET_KEY = "your-secret-key-change-in-production-12345"
serializer = URLSafeTimedSerializer(SECRET_KEY)


class SessionManager:
    """Менеджер сессий для заданий 5.1-5.3"""
    
    # Временные хранилища для демонстрации (в реальном приложении используйте БД)
    sessions: Dict[str, Dict] = {}  # session_token -> user_data
    user_sessions: Dict[str, str] = {}  # user_id -> session_token
    
    @staticmethod
    def create_session(user_id: str) -> str:
        """Создание новой сессии"""
        session_token = str(uuid.uuid4())
        current_time = int(time.time())
        
        SessionManager.sessions[session_token] = {
            "user_id": user_id,
            "created_at": current_time,
            "last_activity": current_time
        }
        SessionManager.user_sessions[user_id] = session_token
        
        return session_token
    
    @staticmethod
    def get_session(session_token: str) -> Optional[Dict]:
        """Получение данных сессии"""
        return SessionManager.sessions.get(session_token)
    
    @staticmethod
    def update_activity(session_token: str) -> bool:
        """Обновление времени активности"""
        session = SessionManager.sessions.get(session_token)
        if session:
            current_time = int(time.time())
            session["last_activity"] = current_time
            return True
        return False
    
    @staticmethod
    def delete_session(session_token: str):
        """Удаление сессии"""
        session = SessionManager.sessions.get(session_token)
        if session:
            user_id = session["user_id"]
            SessionManager.sessions.pop(session_token, None)
            SessionManager.user_sessions.pop(user_id, None)
    
    @staticmethod
    def create_signed_session(user_id: str, timestamp: int) -> str:
        """Создание подписанной сессии (задание 5.2)"""
        # Формат: user_id.timestamp
        data = f"{user_id}.{timestamp}"
        signature = serializer.dumps(data)
        return f"{data}.{signature}"
    
    @staticmethod
    def verify_signed_session(session_value: str) -> Optional[tuple]:
        """Проверка подписи и извлечение данных сессии"""
        try:
            # Пытаемся разделить значение
            parts = session_value.split('.')
            if len(parts) < 3:
                return None
            
            # user_id и timestamp находятся в первых двух частях
            user_id = parts[0]
            timestamp = parts[1]
            signature = '.'.join(parts[2:])
            
            # Восстанавливаем исходные данные для проверки
            data = f"{user_id}.{timestamp}"
            
            # Проверяем подпись
            verified = serializer.loads(signature)
            
            if verified != data:
                return None
                
            return user_id, int(timestamp)
        except (BadSignature, SignatureExpired, ValueError):
            return None
    
    @staticmethod
    def check_session_validity(session_token: str) -> tuple:
        """
        Проверка валидности сессии с учетом времени активности
        Возвращает: (is_valid, should_update, user_id)
        """
        session = SessionManager.sessions.get(session_token)
        if not session:
            return False, False, None
        
        current_time = int(time.time())
        last_activity = session["last_activity"]
        time_since_last = current_time - last_activity
        
        # Если прошло больше 5 минут - сессия истекла
        if time_since_last > 300:  # 5 минут = 300 секунд
            SessionManager.delete_session(session_token)
            return False, False, None
        
        # Если прошло 3 минуты и более, но менее 5 - нужно обновить
        should_update = time_since_last >= 180  # 3 минуты = 180 секунд
        
        return True, should_update, session["user_id"]


# Пример пользовательских данных (в реальном приложении используйте БД)
USERS = {
    "user123": {"password": "password123", "user_id": "550e8400-e29b-41d4-a716-446655440000", "name": "John Doe"},
    "alice": {"password": "alice123", "user_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8", "name": "Alice Smith"}
}


async def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Аутентификация пользователя"""
    user = USERS.get(username)
    if user and user["password"] == password:
        return {"user_id": user["user_id"], "username": username, "name": user["name"]}
    return None


# Задание 5.1 и 5.2: Маршрут логина
async def login_endpoint(username: str, password: str, response: Response) -> Dict:
    """Эндпоинт логина"""
    user = await authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Создаем подписанную сессию
    current_time = int(time.time())
    signed_token = SessionManager.create_signed_session(user["user_id"], current_time)
    
    # Устанавливаем cookie с подписью
    response.set_cookie(
        key="session_token",
        value=signed_token,
        httponly=True,
        secure=False,  # Для тестирования, в продакшене True
        max_age=300,  # 5 минут
        samesite="lax"
    )
    
    return {
        "message": "Login successful",
        "user_id": user["user_id"],
        "username": user["username"]
    }


# Задание 5.1, 5.2, 5.3: Защищенный эндпоинт профиля
async def profile_endpoint(request: Request, response: Response) -> Dict:
    """Защищенный эндпоинт профиля"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Проверяем подписанную сессию
    session_data = SessionManager.verify_signed_session(session_token)
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_id, timestamp = session_data
    current_time = int(time.time())
    time_since_last = current_time - timestamp
    
    # Проверяем время активности
    if time_since_last > 300:
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Обновляем cookie при необходимости
    if time_since_last >= 180:
        new_timestamp = current_time
        new_signed_token = SessionManager.create_signed_session(user_id, new_timestamp)
        response.set_cookie(
            key="session_token",
            value=new_signed_token,
            httponly=True,
            secure=False,
            max_age=300
        )
    
    # Ищем информацию о пользователе
    user_info = None
    for user in USERS.values():
        if user["user_id"] == user_id:
            user_info = user
            break
    
    return {
        "user_id": user_id,
        "username": user_info.get("username") if user_info else "Unknown",
        "name": user_info.get("name") if user_info else "Unknown",
        "message": "Profile accessed successfully",
        "last_activity": timestamp,
        "current_time": current_time,
        "time_since_last": time_since_last
    }