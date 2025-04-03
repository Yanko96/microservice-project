# 修改 scripts/rebuild_index.py 文件

import asyncio
import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app.db.session import get_db
from app.models.post import Post
from app.utils.elasticsearch import es_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建异步数据库会话
engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def rebuild_index():
    """重建全部帖子的搜索索引"""
    # 连接Elasticsearch
    await es_service.connect()
    if not es_service.is_ready:
        logger.error("无法连接到Elasticsearch")
        return
    
    # 创建新索引
    index_name = f"posts_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    previous_index = es_service.index_name
    
    # 设置新索引名称
    es_service.index_name = index_name
    
    # 创建新索引
    success = await es_service.create_index()
    if not success:
        logger.error("无法创建新索引")
        es_service.index_name = previous_index  # 恢复原索引名称
        return
    
    logger.info(f"已创建新索引: {index_name}")
    
    # 从数据库批量读取公开帖子并索引
    try:
        async with AsyncSessionLocal() as session:
            # 分批查询所有公开帖子
            batch_size = 100
            offset = 0
            total_indexed = 0
            
            while True:
                # 使用正确的异步查询语法
                query = select(Post).filter(Post.visibility == "public").order_by(Post.id).offset(offset).limit(batch_size)
                
                result = await session.execute(query)
                posts = result.scalars().all()
                
                if not posts:
                    break
                
                # 索引批量帖子
                for post in posts:
                    post_data = jsonable_encoder(post)
                    success = await es_service.index_post(post_data)
                    if success:
                        total_indexed += 1
                
                logger.info(f"已索引 {total_indexed} 个帖子")
                offset += batch_size
            
            logger.info(f"索引重建完成，共索引 {total_indexed} 个帖子")
            
            # 将别名指向新索引
            if total_indexed > 0:
                # 创建或更新别名
                await es_service.client.indices.put_alias(index=index_name, name="posts_current")
                
                # 删除旧索引（如果存在且不是当前新建的）
                if previous_index != index_name:
                    try:
                        exists = await es_service.client.indices.exists(index=previous_index)
                        if exists:
                            await es_service.client.indices.delete(index=previous_index)
                            logger.info(f"已删除旧索引: {previous_index}")
                    except Exception as e:
                        logger.error(f"删除旧索引失败: {str(e)}")
            
    except Exception as e:
        logger.error(f"索引重建失败: {str(e)}")
    finally:
        # 关闭连接
        await es_service.close()
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(rebuild_index())