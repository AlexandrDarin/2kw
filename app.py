import webbrowser
import threading
import time
from fastapi import FastAPI, Depends, HTTPException, Request, Response, Form, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import uvicorn

# Создаем приложение
app = FastAPI(
    title="FastAPI Control Work",
    description="Контрольная работа по FastAPI",
    version="1.0.0"
)

# ========== Задание 3.1: Модель пользователя ==========
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Имя пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    age: Optional[int] = Field(None, ge=1, le=150, description="Возраст пользователя")
    is_subscribed: Optional[bool] = Field(False, description="Подписка на рассылку")

@app.post("/create_user", response_model=UserCreate, status_code=201)
async def create_user(user: UserCreate):
    """Создание нового пользователя"""
    return user

# ========== Задание 3.2: Продукты ==========
sample_products = [
    {"product_id": 123, "name": "Smartphone", "category": "Electronics", "price": 599.99},
    {"product_id": 456, "name": "Phone Case", "category": "Accessories", "price": 19.99},
    {"product_id": 789, "name": "Iphone", "category": "Electronics", "price": 1299.99},
    {"product_id": 101, "name": "Headphones", "category": "Accessories", "price": 99.99},
    {"product_id": 202, "name": "Smartwatch", "category": "Electronics", "price": 299.99}
]

@app.get("/product/{product_id}")
async def get_product(product_id: int):
    """Получение продукта по ID"""
    product = next((p for p in sample_products if p["product_id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/products/search")
async def search_products(
    keyword: str = Query(..., min_length=1, description="Ключевое слово"),
    category: Optional[str] = Query(None, description="Категория"),
    limit: int = Query(10, ge=1, le=50, description="Лимит")
):
    """Поиск продуктов"""
    results = []
    for product in sample_products:
        if keyword.lower() in product["name"].lower():
            if category is None or product["category"].lower() == category.lower():
                results.append(product)
    return results[:limit]

# ========== Задание 5.1-5.3: Аутентификация ==========
import uuid
import time
from itsdangerous import URLSafeTimedSerializer, BadSignature

SECRET_KEY = "your-secret-key-2024"
serializer = URLSafeTimedSerializer(SECRET_KEY)

USERS = {
    "user123": {"password": "password123", "user_id": "550e8400-e29b-41d4-a716-446655440000", "name": "John Doe"},
    "alice": {"password": "alice123", "user_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8", "name": "Alice Smith"}
}

def create_signed_session(user_id: str, timestamp: int) -> str:
    """Создание подписанной сессии"""
    data = f"{user_id}.{timestamp}"
    signature = serializer.dumps(data)
    return f"{data}.{signature}"

def verify_signed_session(session_value: str):
    """Проверка подписи сессии"""
    try:
        parts = session_value.split('.')
        if len(parts) < 3:
            return None
        user_id = parts[0]
        timestamp = parts[1]
        signature = '.'.join(parts[2:])
        data = f"{user_id}.{timestamp}"
        verified = serializer.loads(signature)
        if verified != data:
            return None
        return user_id, int(timestamp)
    except:
        return None

@app.post("/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...)):
    """Логин пользователя"""
    user = USERS.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    current_time = int(time.time())
    signed_token = create_signed_session(user["user_id"], current_time)
    
    response.set_cookie(
        key="session_token",
        value=signed_token,
        httponly=True,
        secure=False,
        max_age=300
    )
    
    return {"message": "Login successful", "user_id": user["user_id"], "username": username}

@app.get("/profile")
async def get_profile(request: Request, response: Response):
    """Защищенный профиль"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    session_data = verify_signed_session(session_token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_id, timestamp = session_data
    current_time = int(time.time())
    time_since_last = current_time - timestamp
    
    if time_since_last > 300:
        raise HTTPException(status_code=401, detail="Session expired")
    
    if time_since_last >= 180:
        new_token = create_signed_session(user_id, current_time)
        response.set_cookie(
            key="session_token",
            value=new_token,
            httponly=True,
            secure=False,
            max_age=300
        )
    
    user_info = None
    for user in USERS.values():
        if user["user_id"] == user_id:
            user_info = user
            break
    
    return {
        "user_id": user_id,
        "name": user_info["name"] if user_info else "Unknown",
        "message": "Profile accessed successfully",
        "time_since_last": time_since_last
    }

@app.get("/logout")
async def logout(response: Response):
    """Выход из системы"""
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}

# ========== Задание 5.4-5.5: Заголовки ==========
class CommonHeaders(BaseModel):
    user_agent: str = Field(..., alias="User-Agent")
    accept_language: str = Field(..., alias="Accept-Language")
    
    class Config:
        populate_by_name = True

@app.get("/headers")
async def get_headers(headers: CommonHeaders = Depends()):
    """Получение заголовков"""
    return {
        "User-Agent": headers.user_agent,
        "Accept-Language": headers.accept_language
    }

@app.get("/headers/legacy")
async def get_headers_legacy(request: Request):
    """Старая версия получения заголовков"""
    user_agent = request.headers.get("User-Agent")
    accept_language = request.headers.get("Accept-Language")
    
    if not user_agent or not accept_language:
        raise HTTPException(status_code=400, detail="Both headers are required")
    
    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }

@app.get("/info")
async def get_info(headers: CommonHeaders = Depends(), response: Response = None):
    """Получение информации с серверным временем"""
    from datetime import datetime
    current_time = datetime.now().isoformat()
    response.headers["X-Server-Time"] = current_time
    
    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": {
            "User-Agent": headers.user_agent,
            "Accept-Language": headers.accept_language
        }
    }

# ========== Корневой эндпоинт ==========
@app.get("/")
async def root():
    return {
        "message": "FastAPI Control Work API",
        "docs": "http://127.0.0.1:8000/docs",
        "endpoints": {
            "create_user": "POST /create_user",
            "get_product": "GET /product/{product_id}",
            "search_products": "GET /products/search",
            "login": "POST /login",
            "profile": "GET /profile",
            "headers": "GET /headers",
            "info": "GET /info"
        }
    }

# Функция для открытия браузера
def open_browser():
    """Открывает браузер через 2 секунды"""
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8000/docs")

# ========== Запуск приложения ==========
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Запуск FastAPI Control Work")
    print("=" * 50)
    print("📖 Документация: http://127.0.0.1:8000/docs")
    print("📚 ReDoc: http://127.0.0.1:8000/redoc")
    print("🏠 Главная: http://127.0.0.1:8000")
    print("🔄 Нажмите CTRL+C для остановки")
    print("=" * 50)
    print("🌐 Открываю браузер...")
    
    # Открываем браузер в отдельном потоке
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Запускаем сервер
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)