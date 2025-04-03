import time
from fastapi import APIRouter, Depends
from sqlalchemy import text  # Import the text function
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.events.kafka_consumer import kafka_consumer

router = APIRouter()

@router.get("", response_model=dict)
def health_check(db: Session = Depends(get_db)):
    """
    健康检查端点，用于 Docker 的健康检查。
    检查数据库连接是否正常，以及服务是否在运行。
    """
    # 尝试执行一个简单的数据库查询，以检查数据库连接
    try:
        db.execute(text("SELECT 1"))  # Use text() to wrap the SQL statement
        db_status = "UP"
    except Exception as e:
        db_status = f"DOWN: {str(e)}"
    
    # 返回额外的Kafka状态信息
    kafka_status = "UP" if kafka_consumer.running else "DOWN (服务仍可用)"
    
    return {
        "status": "UP",
        "database": db_status,
        "kafka": kafka_status,
        "timestamp": int(time.time())
    }