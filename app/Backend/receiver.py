import asyncio
import json
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from bd.bd import create_table_chat, filling_the_chat
from sendk import send


RABBIT_URL = "amqp://guest:guest@localhost/"
EXCHANGE_NAME = "direct_exchange"
MY_CLIENT_ID = "server"

async def on_message(message: AbstractIncomingMessage):
    """Обработчик входящих сообщений"""
    async with message.process():
        try:
            body = message.body.decode('utf-8')
            data = json.loads(body)

            # 2. Извлекаем данные
            sender = int(data.get('from', 'Неизвестно'))
            target = int(data.get('target', 'Неизвестно'))
            content = data.get('content', 'Нет содержимого')
            timestamp = data.get('timestamp', '-')

            await create_table_chat(sender, target)
            await filling_the_chat(sender, target, content, timestamp)
            await send(str(target), content, str(sender))

        except json.JSONDecodeError:
            print(f" Ошибка парсинга JSON: {body}")
            await message.nack(requeue=True)
        except Exception as e:
            print(f" Ошибка обработки: {e}")
            await message.nack(requeue=True)


async def main():
    connection = None
    try:
        # 1. Подключение (robust = авто-переподключение при обрыве)
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

            # 4. Объявляем очередь
            queue = await channel.declare_queue(
                MY_CLIENT_ID,
                durable=True,
                auto_delete=False
            )

            # 5. Привязываем очередь к Exchange
            await queue.bind(exchange, routing_key=MY_CLIENT_ID)

            # 6. Настраиваем QoS (1 сообщение за раз)
            await channel.set_qos(prefetch_count=1)

            # 7. Запускаем потребление
            await queue.consume(on_message)

            # 8. Бесконечное ожидание
            await asyncio.Future()  # Ждём вечно

    except KeyboardInterrupt:
        print("\n Остановка приёмника...")
    except Exception as e:
        print(f" Ошибка: {e}")
    finally:
        if connection:
            await connection.close()


if __name__ == "__main__":
    asyncio.run(main())