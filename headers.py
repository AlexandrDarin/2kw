from fastapi import Request, HTTPException, Response
from datetime import datetime
from models import CommonHeaders


async def get_headers_endpoint(headers: CommonHeaders) -> dict:
    """Эндпоинт для получения заголовков (Задание 5.5)"""
    return {
        "User-Agent": headers.user_agent,
        "Accept-Language": headers.accept_language
    }


async def get_info_endpoint(headers: CommonHeaders, response: Response) -> dict:
    """Эндпоинт с дополнительной информацией (Задание 5.5)"""
    current_time = datetime.now().isoformat()
    
    # Добавляем заголовок ответа
    response.headers["X-Server-Time"] = current_time
    
    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": {
            "User-Agent": headers.user_agent,
            "Accept-Language": headers.accept_language
        }
    }