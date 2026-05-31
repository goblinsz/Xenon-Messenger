import json
import aio_pika
import time
from datetime import datetime

RABBIT_URL = "amqp://guest:guest@10.0.0.103:15672/"
EXCHANGE_NAME = "direct_exchange"

async def send(target_id: str, content: str, sender:str):

    if not target_id or not content:
        #Сообщение не может быть пустым
        return

    message_data = {
        "from": sender,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    message_body = json.dumps(message_data, ensure_ascii=False).encode('utf-8')

    connection = None
    try:
        # 1. Подключение к брокеру
        connection = await aio_pika.connect_robust(RABBIT_URL)

        async with connection:
            # 2. Создаём канал
            channel = await connection.channel()

            # 3. Объявляем Exchange
            exchange = await channel.declare_exchange(
                EXCHANGE_NAME,
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )

            # 4. Создаём сообщение (persistent для надёжности)
            message = aio_pika.Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
                content_encoding="utf-8",
                headers={"sender": sender, "timestamp": str(time.time())}  # Можно отследить отправителя
            )

            await exchange.publish(message, routing_key=target_id)

            #Сообщение отправлено

    except Exception as e:
        print(f"\n❌ Ошибка отправки: {e}")
    finally:
        if connection:
            await connection.close()
