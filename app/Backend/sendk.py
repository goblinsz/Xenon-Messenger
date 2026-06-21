import json
import aio_pika
import os

try:
    from dotenv import load_dotenv
    _dotenv_available = True
except ImportError:
    _dotenv_available = False

_script_dir = os.path.abspath(os.path.dirname(__file__))
_dotenv_path = os.path.join(_script_dir, '..', '.env')
if _dotenv_available and os.path.isfile(_dotenv_path):
    load_dotenv(_dotenv_path)

RABBIT_URL = os.getenv("RABBIT_URL")
if RABBIT_URL is None:
    raise EnvironmentError("Missing RABBIT_URL in .env file")
EXCHANGE_NAME = "direct_exchange"


async def send(target_id: str, content: str, sender: str, timestamp: str, conversation_id: int = None, is_group: bool = False):
    if not target_id or not content:
        return

    message_data = {
        "content": content,
        "from": sender,
        "timestamp": timestamp,
        "conversation_id": conversation_id,
        "is_group": is_group
    }

    message_body = json.dumps(message_data, ensure_ascii=False).encode('utf-8')

    connection = None
    try:
        connection = await aio_pika.connect_robust(RABBIT_URL)
        async with connection:
            channel = await connection.channel()

            exchange = await channel.declare_exchange(
                EXCHANGE_NAME,
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )

            message = aio_pika.Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
                content_encoding="utf-8"
            )

            await exchange.publish(message, routing_key=target_id)
            print(f"Message sent to queue: {target_id}")

    except Exception as e:
        print(f"\nRabbitMQ Error: {e}")
    finally:
        if connection and not connection.is_closed:
            await connection.close()
