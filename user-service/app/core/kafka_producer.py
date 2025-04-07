import asyncio
import json
from aiokafka import AIOKafkaProducer
from app.core.config import settings

producer = None

async def init_kafka_producer():
    global producer
    if not producer:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
        )
        await producer.start()

async def send_follow_event(follower_id: int, followee_id: int):
    await init_kafka_producer()
    event = {
        "type": "follow",
        "follower_id": follower_id,
        "followee_id": followee_id,
    }
    await producer.send_and_wait("notifications", json.dumps(event).encode("utf-8"))
