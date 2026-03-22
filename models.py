from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re


class UserCreate(BaseModel):
    """Модель для создания пользователя (Задание 3.1)"""
    name: str = Field(..., min_length=1, max_length=100, description="Имя пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    age: Optional[int] = Field(None, ge=1, le=150, description="Возраст пользователя")
    is_subscribed: Optional[bool] = Field(False, description="Подписка на рассылку")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Alice",
                "email": "alice@example.com",
                "age": 30,
                "is_subscribed": True
            }
        }


class CommonHeaders(BaseModel):
    """Модель для общих заголовков (Задание 5.5)"""
    user_agent: str = Field(..., alias="User-Agent", description="User-Agent заголовок")
    accept_language: str = Field(..., alias="Accept-Language", description="Accept-Language заголовок")
    
    @field_validator('accept_language')
    @classmethod
    def validate_accept_language(cls, v: str) -> str:
        """Валидация формата Accept-Language"""
        if not v:
            raise ValueError('Accept-Language cannot be empty')
        
        # Простая валидация формата
        pattern = r'^[a-zA-Z]{2}(-[a-zA-Z]{2})?(,[a-zA-Z]{2}(-[a-zA-Z]{2})?;q=[0-9]\.[0-9])*$'
        # Упрощенная проверка: должно содержать хотя бы одну языковую метку
        if not re.match(r'^[a-zA-Z]{2}(-[a-zA-Z]{2})?', v.split(',')[0].strip()):
            raise ValueError('Invalid Accept-Language format')
        
        return v
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "en-US,en;q=0.9,es;q=0.8"
            }
        }


class Product(BaseModel):
    """Модель продукта"""
    product_id: int
    name: str
    category: str
    price: float