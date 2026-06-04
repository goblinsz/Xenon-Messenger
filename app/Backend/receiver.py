import asyncio
import json
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from bd.bd import create_table_chat, filling_the_chat, init_pool, close_pool
from sendk import send


RABBIT_URL = "amqp://g:g@localhost/"
EXCHANGE_NAME = "direct_exchange"
MY_CLIENT_ID = "server"


async def on_message(message: AbstractIncomingMessage):
    """Обработчик входящих сообщений"""
    try:
        # 1. Декодируем и парсим
        body = message.body.decode('utf-8')
        data = json.loads(body)

        sender = int(data.get('from', '0'))
        target = int(data.get('target', '0'))
        content = data.get('content', 'Нет содержимого')
        timestamp = data.get('timestamp', "Когда-то")

        # 2. Обрабатываем бизнес-логику
        await create_table_chat(sender, target)
        await filling_the_chat(sender, target, content, timestamp)
        await send(str(target), content, str(sender), timestamp)

        # 3. Успешное подтверждение
        await message.ack()
        print(f"✅ Обработано: {sender} → {target}")

    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        # Битое сообщение — не возвращаем в очередь
        await message.nack(requeue=False)

    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")
        # Временная ошибка — возвращаем в очередь для повторной попытки
        await message.nack(requeue=True)


async def main():
    connection = None
    try:
        # 1. СНАЧАЛА инициализируем БД
        await init_pool()
        print("✅ Пул БД инициализирован")

        # 2. ПОТОМ подключаем RabbitMQ
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

            print(f"📥 Приёмник запущен, слушаю: {MY_CLIENT_ID}")

            # Запускаем потребление
            await queue.consume(on_message)

            # Ждём вечно
            await asyncio.Future()

    except KeyboardInterrupt:
        print("\n👋 Остановка по Ctrl+C...")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        # 3. Закрываем пул БД ТОЛЬКО при завершении всего приложения
        await close_pool()
        print("✅ Пул БД закрыт")

        if connection and not connection.is_closed:
            await connection.close()
            print("✅ Соединение с RabbitMQ закрыто")


if __name__ == "__main__":
    asyncio.run(main())