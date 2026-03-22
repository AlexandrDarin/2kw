from typing import List, Optional
from fastapi import HTTPException, Query
from models import Product


# Пример данных продуктов (Задание 3.2)
sample_product_1 = {
    "product_id": 123,
    "name": "Smartphone",
    "category": "Electronics",
    "price": 599.99
}

sample_product_2 = {
    "product_id": 456,
    "name": "Phone Case",
    "category": "Accessories",
    "price": 19.99
}

sample_product_3 = {
    "product_id": 789,
    "name": "Iphone",
    "category": "Electronics",
    "price": 1299.99
}

sample_product_4 = {
    "product_id": 101,
    "name": "Headphones",
    "category": "Accessories",
    "price": 99.99
}

sample_product_5 = {
    "product_id": 202,
    "name": "Smartwatch",
    "category": "Electronics",
    "price": 299.99
}

sample_products = [sample_product_1, sample_product_2, sample_product_3, sample_product_4, sample_product_5]


async def get_product(product_id: int) -> Product:
    """Получение продукта по ID (Задание 3.2)"""
    product = next((p for p in sample_products if p["product_id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)


async def search_products(
    keyword: str = Query(..., min_length=1, description="Ключевое слово для поиска"),
    category: Optional[str] = Query(None, description="Категория товара"),
    limit: int = Query(10, ge=1, le=50, description="Максимальное количество товаров")
) -> List[Product]:
    """Поиск продуктов (Задание 3.2)"""
    results = []
    
    for product in sample_products:
        # Проверяем соответствие ключевому слову (регистронезависимо)
        if keyword.lower() in product["name"].lower():
            # Проверяем категорию, если указана
            if category is None or product["category"].lower() == category.lower():
                results.append(Product(**product))
    
    # Ограничиваем количество результатов
    return results[:limit]