import aio_pika
from .config import config

class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
    
    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            config.RABBITMQ_URL
        )
        self.channel = await self.connection.channel()
        print("Подключено к RabbitMQ")
    
    async def close(self):
        if self.connection:
            await self.connection.close()
            print("RabbitMQ закрыт")
    
    async def publish_message(self, from_user_id: int, to_user_id: int, text: str):
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=f"{from_user_id}:{to_user_id}:{text}".encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key="message_queue"
        )
    
    async def consume_messages(self, callback):
        queue = await self.channel.declare_queue("message_queue", durable=True)
        await queue.consume(callback)

rabbitmq = RabbitMQClient()