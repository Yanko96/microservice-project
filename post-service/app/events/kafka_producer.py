import json
import asyncio
from typing import Dict, Any, Optional, List

from aiokafka import AIOKafkaProducer
from loguru import logger

from app.core.config import settings

class KafkaProducer:
    """Kafka 生产者类，用于发送消息到指定的主题"""
    
    def __init__(self):
        """初始化Kafka生产者"""
        self.producer = None
        self.is_ready = False
    
    async def start(self):
        """启动Kafka生产者"""
        if self.producer is None:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                retry_backoff_ms=500,
                request_timeout_ms=10000
            )
            
            try:
                await self.producer.start()
                self.is_ready = True
                logger.info("Kafka生产者已启动")
            except Exception as e:
                logger.error(f"Kafka生产者启动失败: {str(e)}")
                self.is_ready = False
    
    async def stop(self):
        """停止Kafka生产者"""
        if self.producer is not None:
            await self.producer.stop()
            self.producer = None
            self.is_ready = False
            logger.info("Kafka生产者已停止")
    
    async def send_message(self, topic: str, message: Dict[str, Any], key: Optional[str] = None) -> bool:
        """
        发送消息到指定主题
        
        参数:
            topic: Kafka主题
            message: 要发送的消息
            key: 消息的键(可选)
        
        返回:
            是否成功发送
        """
        if not self.is_ready:
            logger.warning(f"Kafka生产者未就绪，无法发送消息到主题 {topic}")
            return False
        
        try:
            if key:
                encoded_key = key.encode('utf-8')
                await self.producer.send_and_wait(topic, message, key=encoded_key)
            else:
                await self.producer.send_and_wait(topic, message)
            return True
        except Exception as e:
            logger.error(f"发送消息到主题 {topic} 失败: {str(e)}")
            return False
    
    async def send_post_event(self, event_type: str, post_data: Dict[str, Any]) -> bool:
        """
        发送帖子相关事件
        
        参数:
            event_type: 事件类型，如 'created', 'updated', 'deleted'
            post_data: 帖子数据
        
        返回:
            是否成功发送
        """
        message = {
            "event_type": event_type,
            "post": post_data
        }
        return await self.send_message(
            topic=settings.KAFKA_TOPIC_POSTS,
            message=message,
            key=str(post_data.get("id", ""))
        )
    
    async def send_comment_event(self, event_type: str, comment_data: Dict[str, Any]) -> bool:
        """
        发送评论相关事件
        
        参数:
            event_type: 事件类型，如 'created', 'updated', 'deleted'
            comment_data: 评论数据
        
        返回:
            是否成功发送
        """
        message = {
            "event_type": event_type,
            "comment": comment_data
        }
        return await self.send_message(
            topic=settings.KAFKA_TOPIC_COMMENTS,
            message=message,
            key=str(comment_data.get("id", ""))
        )
    
    async def send_reaction_event(self, event_type: str, reaction_data: Dict[str, Any]) -> bool:
        """
        发送反应相关事件
        
        参数:
            event_type: 事件类型，如 'created', 'updated', 'deleted'
            reaction_data: 反应数据
        
        返回:
            是否成功发送
        """
        message = {
            "event_type": event_type,
            "reaction": reaction_data
        }
        return await self.send_message(
            topic=settings.KAFKA_TOPIC_REACTIONS,
            message=message,
            key=str(reaction_data.get("id", ""))
        )
    
    async def send_notification(self, user_id: int, notification_type: str, data: Dict[str, Any]) -> bool:
        """
        发送通知
        
        参数:
            user_id: 接收通知的用户ID
            notification_type: 通知类型
            data: 通知数据
        
        返回:
            是否成功发送
        """
        message = {
            "user_id": user_id,
            "type": notification_type,
            "data": data,
            "created_at": None  # 将由消费者设置
        }
        return await self.send_message(
            topic=settings.KAFKA_TOPIC_NOTIFICATIONS,
            message=message,
            key=str(user_id)
        )
    
    async def send_log(self, log_level: str, message: str, meta: Dict[str, Any]) -> bool:
        """
        发送日志
        
        参数:
            log_level: 日志级别
            message: 日志消息
            meta: 元数据
        
        返回:
            是否成功发送
        """
        log_data = {
            "level": log_level,
            "message": message,
            "service": "post-service",
            "meta": meta,
            "timestamp": None  # 将由消费者设置
        }
        return await self.send_message(
            topic=settings.KAFKA_TOPIC_LOGS,
            message=log_data
        )

# 创建Kafka生产者单例
kafka_producer = KafkaProducer()