import asyncio
from core.database import db
from services.auth_service import AuthService
from services.message_service import MessageService

async def main():
    await db.connect()
    await db.init_tables()
    
    # 1. Создаём двух пользователей
    print("1. Регистрация пользователей...")
    await AuthService.register("alex", "123456")
    await AuthService.register("bob", "123456")
    print("   ✅ Пользователи созданы: alex, bob")
    
    # 2. Отправляем сообщения
    print("\n2. Отправка сообщений...")
    
    success, result = await MessageService.send_message("alex", "bob", "Привет, Боб!")
    if success:
        print(f"   ✅ Алекс → Боб: {result['text']}")
    
    success, result = await MessageService.send_message("bob", "alex", "Привет, Алекс!")
    if success:
        print(f"   ✅ Боб → Алекс: {result['text']}")
    
    success, result = await MessageService.send_message("alex", "bob", "Как дела?")
    if success:
        print(f"   ✅ Алекс → Боб: {result['text']}")
    
    # 3. Получаем диалог
    print("\n3. Диалог между Алексом и Бобом:")
    success, messages = await MessageService.get_dialog("alex", "bob")
    
    if success:
        for msg in messages:
            print(f"   {msg['sender_name']}: {msg['text']} ({msg['created_at']})")
    
    # 4. Проверяем непрочитанные сообщения для Боба
    print("\n4. Непрочитанные сообщения:")
    success, count = await MessageService.get_unread_count("bob")
    if success:
        print(f"   У Боба: {count} непрочитанных сообщений")
    
    await db.close()

if __name__ == "__main__":
    asyncio.run(main())