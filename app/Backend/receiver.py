import asyncio
import json
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from bd.bd import create_table_chat, filling_the_chat, init_pool, close_pool

RABBIT_URL = "amqp://g:g@10.0.0.103/"
EXCHANGE_NAME = "direct_exchange"
MY_CLIENT_ID = "server"


async def on_message(message: AbstractIncomingMessage):
    async with message.process():
        try:
            body = message.body.decode('utf-8')
            data = json.loads(body)

            sender = int(data.get('from', '0'))
            target = int(data.get('target', '0'))
            content = data.get('content', 'Нет содержимого')
            timestamp = data.get('timestamp', "")

            print(f"📥 Получено: от {sender} для {target}: {content}")

            await create_table_chat(sender, target)
            await filling_the_chat(sender, target, content, timestamp)

        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
        except Exception as e:
            print(f"❌ Ошибка обработки/БД: {e}")
            raise e


async def main():
    connection = None
    try:
        await init_pool()
        print("✅ Пул БД инициализирован")

        connection = await aio_pika.connect_robust(RABBIT_URL)

        async with connection:
            channel = await connection.channel()

            exchange = await channel.declare_exchange(
                EXCHANGE_NAME,
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )

            queue = await channel.declare_queue(
                MY_CLIENT_ID,
                durable=True,
                auto_delete=False
            )

            await queue.bind(exchange, routing_key=MY_CLIENT_ID)
            await channel.set_qos(prefetch_count=1)

            print(f"📥 Приёмник запущен, слушаю очередь: {MY_CLIENT_ID}")

            await queue.consume(on_message)
            await asyncio.Future()

    except KeyboardInterrupt:
        print("\n👋 Остановка...")
    finally:
        await close_pool()
        if connection and not connection.is_closed:
            await connection.close()


if __name__ == "__main__":
    asyncio.run(main())