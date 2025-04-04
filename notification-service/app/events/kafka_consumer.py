import asyncio
import json
from typing import List, Dict, Any, Callable, Awaitable
from datetime import datetime
import logging

from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.websockets.broadcaster import broadcast_to_user

logger = logging.getLogger(__name__)

class KafkaConsumer:
    """Kafka 消费者，用于接收和处理事件"""
    
    def __init__(self, topics: List[str], handler_map: Dict[str, Callable[[Dict[str, Any], Session], Awaitable[None]]]):
        """
        初始化 Kafka 消费者
        
        参数:
            topics: 要订阅的主题列表
            handler_map: 主题到处理函数的映射
        """
        self.topics = topics
        self.handler_map = handler_map
        self.consumer = None
        self.running = False
        self.should_stop = False
    
    async def start(self):
        """启动消费者"""
        # 创建消费者
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.KAFKA_CONSUMER_GROUP,
            auto_offset_reset="latest",  # latest 确保只获取新消息
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        await self.consumer.start()
        self.running = True
        logger.info(f"Kafka 消费者已启动，订阅主题: {', '.join(self.topics)}")
        
        # 启动消费循环
        asyncio.create_task(self.consume_loop())
    
    async def consume_loop(self):
        """消费循环，处理消息"""
        try:
            while self.running and not self.should_stop:
                try:
                    # 获取消息
                    async for message in self.consumer:
                        if self.should_stop:
                            break
                            
                        topic = message.topic
                        value = message.value
                        
                        logger.debug(f"收到来自主题 {topic} 的消息: {value}")
                        
                        # 处理消息
                        if topic in self.handler_map:
                            try:
                                # 创建数据库会话
                                db = SessionLocal()
                                try:
                                    await self.handler_map[topic](value, db)
                                finally:
                                    db.close()
                            except Exception as e:
                                logger.error(f"处理消息时发生错误: {str(e)}")
                except Exception as e:
                    logger.error(f"消费消息时发生错误: {str(e)}")
                    
                    # 如果出错，等待一秒后重试
                    await asyncio.sleep(1)
        finally:
            await self.stop()
    
    async def stop(self):
        """停止消费者"""
        self.should_stop = True
        self.running = False
        
        if self.consumer is not None:
            await self.consumer.stop()
            logger.info("Kafka 消费者已停止")


# 创建通知处理函数
async def process_notification(message: Dict[str, Any], db: Session):
    """
    处理来自通知主题的消息
    """
    from app.events.handlers import handle_notification
    
    if "user_id" not in message:
        logger.error("消息缺少 user_id 字段")
        return
    
    # 处理通知
    notification = await handle_notification(message, db)
    
    if notification:
        # 通过 WebSocket 广播通知
        await broadcast_to_user(
            user_id=notification.user_id,
            message={
                "type": "notification",
                "data": {
                    "id": notification.id,
                    "type": notification.type,
                    "title": notification.title,
                    "body": notification.body,
                    "created_at": notification.created_at.isoformat()
                }
            }
        )

# 创建帖子事件处理函数
async def process_post_event(message: Dict[str, Any], db: Session):
    """
    处理来自帖子主题的消息
    """
    from app.events.handlers import handle_post_event
    
    if "event_type" not in message or "post" not in message:
        logger.error("消息格式不正确")
        return
    
    # 处理帖子事件
    await handle_post_event(message["event_type"], message["post"], db)

# 创建评论事件处理函数
async def process_comment_event(message: Dict[str, Any], db: Session):
    """
    处理来自评论主题的消息
    """
    from app.events.handlers import handle_comment_event
    
    if "event_type" not in message or "comment" not in message:
        logger.error("消息格式不正确")
        return
    
    # 处理评论事件
    await handle_comment_event(message["event_type"], message["comment"], db)

# 创建反应事件处理函数
async def process_reaction_event(message: Dict[str, Any], db: Session):
    """
    处理来自反应主题的消息
    """
    from app.events.handlers import handle_reaction_event
    
    if "event_type" not in message or "reaction" not in message:
        logger.error("消息格式不正确")
        return
    
    # 处理反应事件
    await handle_reaction_event(message["event_type"], message["reaction"], db)

# 创建 Kafka 消费者实例
kafka_consumer = KafkaConsumer(
    topics=[
        settings.KAFKA_TOPIC_NOTIFICATIONS,
        settings.KAFKA_TOPIC_POSTS,
        settings.KAFKA_TOPIC_COMMENTS,
        settings.KAFKA_TOPIC_REACTIONS
    ],
    handler_map={
        settings.KAFKA_TOPIC_NOTIFICATIONS: process_notification,
        settings.KAFKA_TOPIC_POSTS: process_post_event,
        settings.KAFKA_TOPIC_COMMENTS: process_comment_event,
        settings.KAFKA_TOPIC_REACTIONS: process_reaction_event
    }
)