import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
import redis.asyncio as aioredis

from app.core.config import settings
from app.websockets.connection import connection_manager

logger = logging.getLogger(__name__)

# Redis 客户端
redis_client: Optional[aioredis.Redis] = None

async def init_redis():
    """初始化Redis连接"""
    global redis_client
    
    if redis_client is not None:
        return
    
    try:
        redis_client = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True  # 自动解码为Python字符串
        )
        logger.info("Redis连接成功")
    except Exception as e:
        logger.error(f"Redis连接失败: {str(e)}")
        redis_client = None

async def close_redis():
    """关闭Redis连接"""
    global redis_client
    
    if redis_client is not None:
        await redis_client.close()
        redis_client = None
        logger.info("Redis连接已关闭")

async def publish_message(channel: str, message: Dict[str, Any]) -> bool:
    """
    发布消息到Redis频道
    
    参数:
        channel: 频道名称
        message: 要发布的消息
    
    返回:
        是否成功发布
    """
    global redis_client
    
    if redis_client is None:
        await init_redis()
        if redis_client is None:
            return False
    
    try:
        # 将消息转换为JSON字符串
        json_message = json.dumps(message)
        
        # 发布消息
        await redis_client.publish(channel, json_message)
        return True
    except Exception as e:
        logger.error(f"发布消息到Redis失败: {str(e)}")
        return False

async def subscribe_to_channel(channel: str) -> None:
    """
    订阅Redis频道，接收消息
    
    参数:
        channel: 频道名称
    """
    global redis_client
    
    if redis_client is None:
        await init_redis()
        if redis_client is None:
            logger.error("Redis连接不可用，无法订阅")
            return
    
    try:
        # 创建发布/订阅对象
        pubsub = redis_client.pubsub()
        
        # 订阅频道
        await pubsub.subscribe(channel)
        logger.info(f"已订阅频道: {channel}")
        
        # 启动消息监听任务
        asyncio.create_task(listen_for_messages(pubsub))
    except Exception as e:
        logger.error(f"订阅Redis频道失败: {str(e)}")

async def listen_for_messages(pubsub) -> None:
    """
    监听Redis发布/订阅消息
    
    参数:
        pubsub: Redis发布/订阅对象
    """
    try:
        async for message in pubsub.listen():
            # 只处理消息类型
            if message["type"] != "message":
                continue
            
            try:
                # 解析消息内容
                data = json.loads(message["data"])
                
                # 处理不同类型的消息
                if "type" in data and "data" in data:
                    await process_pubsub_message(data)
            except json.JSONDecodeError:
                logger.error(f"消息格式错误: {message['data']}")
            except Exception as e:
                logger.error(f"处理消息时发生错误: {str(e)}")
    except Exception as e:
        logger.error(f"消息监听循环发生错误: {str(e)}")
    finally:
        await pubsub.unsubscribe()
        logger.info("已取消订阅")

async def process_pubsub_message(message: Dict[str, Any]) -> None:
    """
    处理从Redis接收的消息
    
    参数:
        message: 消息内容
    """
    message_type = message.get("type")
    message_data = message.get("data", {})
    
    if message_type == "notification":
        # 通知消息
        user_id = message_data.get("user_id")
        if user_id:
            await connection_manager.send_personal_message(
                message={
                    "type": "notification",
                    "data": message_data
                },
                user_id=user_id
            )
    elif message_type == "broadcast":
        # 广播消息
        await connection_manager.broadcast(
            message={
                "type": "broadcast",
                "data": message_data
            }
        )

async def broadcast_to_user(user_id: int, message: Dict[str, Any]) -> bool:
    """
    向特定用户广播消息
    
    参数:
        user_id: 用户ID
        message: 消息内容
    
    返回:
        是否成功广播
    """
    # 先尝试直接发送到WebSocket
    if await connection_manager.send_personal_message(message, user_id):
        return True
    
    # 如果用户不在线，则通过Redis发布
    message_with_user = message.copy()
    if "data" in message_with_user:
        message_with_user["data"]["user_id"] = user_id
    else:
        message_with_user["data"] = {"user_id": user_id}
    
    return await publish_message(
        channel=settings.REDIS_CHANNEL,
        message=message_with_user
    )

async def broadcast_to_all(message: Dict[str, Any]) -> bool:
    """
    向所有用户广播消息
    
    参数:
        message: 消息内容
    
    返回:
        是否成功广播
    """
    # 先直接广播到所有WebSocket
    await connection_manager.broadcast(message)
    
    # 同时通过Redis发布
    return await publish_message(
        channel=settings.REDIS_CHANNEL,
        message={
            "type": "broadcast",
            "data": message
        }
    )