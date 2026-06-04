import asyncio
from core.database import db
from services.auth_service import AuthService

async def main():
    await db.connect()
    await db.init_tables()
    
    # Регистрация
    success, result = await AuthService.register("alex", "123456")
    if success:
        print(f"Создан пользователь: alex (ID: {result})")
    else:
        print(f"Ошибка: {result}")
    
    # Логин
    success, result = await AuthService.login("alex", "123456")
    if success:
        print(f"Вход выполнен: {result['username']}")
    else:
        print(f"Ошибка: {result}")
    
    await db.close()

asyncio.run(main())