# app/events/handlers.py

import logging
from typing import Dict, Any

from app.utils.elasticsearch import es_service
from app.events.kafka_producer import kafka_producer

logger = logging.getLogger(__name__)

async def handle_post_event(event_type: str, post_data: Dict[str, Any]) -> None:
    """
    处理帖子事件，并更新搜索索引
    
    参数:
        event_type: 事件类型 (created, updated, deleted)
        post_data: 帖子数据
    """
    # 根据事件类型更新Elasticsearch索引
    try:
        if event_type == "created":
            await es_service.index_post(post_data)
            logger.info(f"已索引新帖子: ID={post_data.get('id')}")
        elif event_type == "updated":
            await es_service.update_post_index(post_data)
            logger.info(f"已更新帖子索引: ID={post_data.get('id')}")
        elif event_type == "deleted":
            await es_service.delete_post_index(post_data.get('id'))
            logger.info(f"已删除帖子索引: ID={post_data.get('id')}")
    except Exception as e:
        logger.error(f"处理搜索索引失败: {str(e)}")
    
    # 发送事件到Kafka
    await kafka_producer.send_post_event(event_type, post_data)

# app/api/endpoints/posts.py 中需要修改的部分

# 在创建帖子的方法中添加:
# 在 return result 前添加:
# 异步索引帖子
asyncio.create_task(handle_post_event("created", jsonable_encoder(result)))

# 在更新帖子的方法中添加:
# 在 return post 前添加:
# 异步更新帖子索引
asyncio.create_task(handle_post_event("updated", jsonable_encoder(post)))

# 在删除帖子的方法中添加:
# 在 return {"message": "帖子已删除"} 前添加:
# 异步删除帖子索引
post_data = jsonable_encoder(post)
asyncio.create_task(handle_post_event("deleted", post_data))

# app/main.py 的启动和关闭事件中添加:

@app.on_event("startup")
async def startup_event():
    logger.info("服务启动中...")
    await kafka_producer.start()
    await es_service.connect()  # 启动Elasticsearch连接

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("服务关闭中...")
    await kafka_producer.stop()
    await es_service.close()  # 关闭Elasticsearch连接