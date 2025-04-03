# app/api/endpoints/health.py

from typing import Any, Dict
import time
import platform
import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text  # Import the text function

from app.db.session import get_db
from app.utils.elasticsearch import es_service
from app.core.config import settings
from app.events.kafka_producer import kafka_producer

router = APIRouter()

@router.get("", response_model=Dict[str, Any])
async def health_check(db: Session = Depends(get_db)):
    """
    健康检查端点，用于监控服务状态
    """
    start_time = time.time()
    
    status = {
        "status": "UP",
        "components": {
            "service": {
                "status": "UP",
                "version": "1.0.0",  # 可以通过配置文件或环境变量设置
                "environment": settings.ENVIRONMENT,
                "timestamp": int(time.time())
            },
            "database": {
                "status": "UNKNOWN"
            },
            "elasticsearch": {
                "status": "UNKNOWN"
            },
            "kafka": {
                "status": "UNKNOWN"
            },
            "system": {
                "cpu_count": os.cpu_count(),
                "platform": platform.platform(),
                "python_version": platform.python_version()
            }
        }
    }
    
    # 检查数据库连接
    try:
        result = db.execute(text("SELECT 1"))  # Use text() to wrap the SQL statement
        db.commit()
        status["components"]["database"] = {
            "status": "UP",
            "type": "PostgreSQL"
        }
    except Exception as e:
        status["components"]["database"] = {
            "status": "DOWN",
            "error": str(e)
        }
        status["status"] = "DEGRADED"
    
    # 检查Elasticsearch连接
    try:
        if es_service.is_ready:
            es_info = await es_service.client.info()
            status["components"]["elasticsearch"] = {
                "status": "UP",
                "version": es_info.get("version", {}).get("number", "unknown")
            }
        else:
            # 尝试连接
            await es_service.connect()
            if es_service.is_ready:
                es_info = await es_service.client.info()
                status["components"]["elasticsearch"] = {
                    "status": "UP",
                    "version": es_info.get("version", {}).get("number", "unknown")
                }
            else:
                status["components"]["elasticsearch"] = {
                    "status": "DOWN",
                    "error": "无法连接到Elasticsearch"
                }
                status["status"] = "DEGRADED"
    except Exception as e:
        status["components"]["elasticsearch"] = {
            "status": "DOWN",
            "error": str(e)
        }
        status["status"] = "DEGRADED"
    
    # 检查Kafka连接
    try:
        if kafka_producer.is_ready:
            status["components"]["kafka"] = {
                "status": "UP",
                "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS
            }
        else:
            status["components"]["kafka"] = {
                "status": "DOWN",
                "error": "Kafka生产者未就绪"
            }
            status["status"] = "DEGRADED"
    except Exception as e:
        status["components"]["kafka"] = {
            "status": "DOWN",
            "error": str(e)
        }
        status["status"] = "DEGRADED"
    
    # 计算响应时间
    status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    return status

@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics(db: Session = Depends(get_db)):
    """
    获取服务指标
    """
    metrics = {
        "service": "post-service",
        "timestamp": int(time.time()),
    }
    
    # 添加数据库指标
    try:
        # 帖子总数
        posts_count = db.execute(text("SELECT COUNT(*) FROM posts")).scalar()
        # 评论总数
        comments_count = db.execute(text("SELECT COUNT(*) FROM comments")).scalar()
        # 反应总数
        reactions_count = db.execute(text("SELECT COUNT(*) FROM reactions")).scalar()
        # 标签总数
        tags_count = db.execute(text("SELECT COUNT(*) FROM tags")).scalar()
        
        metrics["database"] = {
            "posts_count": posts_count,
            "comments_count": comments_count,
            "reactions_count": reactions_count,
            "tags_count": tags_count
        }
    except Exception as e:
        metrics["database"] = {
            "error": str(e)
        }
    
    # 添加Elasticsearch指标
    try:
        if es_service.is_ready:
            # 获取索引文档数量
            index_stats = await es_service.client.indices.stats(index=es_service.index_name)
            docs_count = index_stats["_all"]["primaries"]["docs"]["count"]
            store_size = index_stats["_all"]["primaries"]["store"]["size_in_bytes"]
            
            metrics["elasticsearch"] = {
                "index_name": es_service.index_name,
                "documents_count": docs_count,
                "storage_bytes": store_size
            }
    except Exception as e:
        metrics["elasticsearch"] = {
            "error": str(e)
        }
    
    return metrics