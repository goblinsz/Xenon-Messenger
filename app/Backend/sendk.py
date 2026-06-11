import json
import aio_pika

RABBIT_URL = "amqp://g:g@192.168.1.65/"
EXCHANGE_NAME = "direct_exchange"


async def send(target_id: str, content: str, sender: str, timestamp: str):
    if not target_id or not content:
        return

    message_data = {
        "from": sender,
        "content": content,
        "timestamp": timestamp
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
            print(f"📤 Message sent to queue: {target_id}")

    except Exception as e:
        print(f"\n❌ RabbitMQ Error: {e}")
    finally:
        if connection and not connection.is_closed:
            await connection.close()