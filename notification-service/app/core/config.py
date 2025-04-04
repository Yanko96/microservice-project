import os
from typing import List, Optional, Union, Dict, Any
from pydantic import AnyHttpUrl, field_validator, HttpUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "社交平台通知服务"
    API_V1_STR: str = "/api/v1"
    
    # 环境标识
    ENVIRONMENT: str = "development"
    
    # 数据库配置
    DATABASE_URL: str
    
    # JWT 配置 (从用户服务获取)
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
        
    # Redis配置 (WebSocket广播)
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_CHANNEL: str = "notifications"
    
    # Kafka配置 (事件消息)
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_TOPIC_NOTIFICATIONS: str = "user.notifications"
    KAFKA_TOPIC_POSTS: str = "social.posts"
    KAFKA_TOPIC_COMMENTS: str = "social.comments"
    KAFKA_TOPIC_REACTIONS: str = "social.reactions"
    KAFKA_CONSUMER_GROUP: str = "notification-service-group"
    
    # 用户服务 API
    USER_SERVICE_BASE_URL: str = "http://user-service:8000/api/v1"
    
    # WebSocket 设置
    WEBSOCKET_PATH: str = "/ws/notifications"
    
    # API 文档
    DOCS_URL: Optional[str] = "/docs"
    OPENAPI_URL: Optional[str] = "/openapi.json"
    REDOC_URL: Optional[str] = "/redoc"
    
    # 日志级别
    LOG_LEVEL: str = "INFO"
    
    # 通知设置
    NOTIFICATION_PAGE_SIZE: int = 20
    NOTIFICATION_MAX_AGE_DAYS: int = 30  # 通知保留天数
    
    # 服务主机和端口
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# 创建设置实例
settings = Settings()