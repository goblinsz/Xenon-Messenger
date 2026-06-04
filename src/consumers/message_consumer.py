import asyncio
import json
from ..core.database import db
from ..core.rabbitmq import rabbitmq
from ..repositories.message_repo import MessageRepository

async def process_message(message):
    async with message.process():
        try:
            data = message.body.decode().split(":")
            from_user_id = int(data[0])
            to_user_id = int(data[1])
            text = data[2]
            
            message_id = await MessageRepository.create(from_user_id, to_user_id, text)
            print(f"Сообщение {message_id} сохранено в БД")
                 
        except Exception as e:
            print(f"❌ Ошибка обработки: {e}")

async def start_consumer():
    await rabbitmq.connect()
    await rabbitmq.consume_messages(process_message)
    print("Consumer запущен, жду сообщений ")

if __name__ == "__main__":
    asyncio.run(start_consumer())