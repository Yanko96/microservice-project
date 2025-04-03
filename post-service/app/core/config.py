import os
from typing import List, Optional, Union, Dict, Any
from pydantic import AnyHttpUrl, field_validator, HttpUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "社交平台帖子服务"
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
        
    # Redis配置
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    
    # Kafka配置
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_TOPIC_POSTS: str = "social.posts"
    KAFKA_TOPIC_COMMENTS: str = "social.comments"
    KAFKA_TOPIC_REACTIONS: str = "social.reactions"
    KAFKA_TOPIC_NOTIFICATIONS: str = "user.notifications"
    KAFKA_TOPIC_LOGS: str = "service.logs"
    
    # Elasticsearch配置
    ELASTICSEARCH_HOST: str = "elasticsearch"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_INDEX_POSTS: str = "posts"
    
    # MinIO配置（对象存储）
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_POST_BUCKET: str = "post-content"
    
    # 用户服务 API
    USER_SERVICE_BASE_URL: str = "http://user-service:8000/api/v1"
    
    # API 文档
    DOCS_URL: Optional[str] = "/docs"
    OPENAPI_URL: Optional[str] = "/openapi.json"
    REDOC_URL: Optional[str] = "/redoc"
    
    # 日志级别
    LOG_LEVEL: str = "INFO"
    
    # 帖子内容限制
    POST_MAX_LENGTH: int = 5000  # 帖子最大字符数
    POST_MIN_LENGTH: int = 1     # 帖子最小字符数
    
    # 上传文件配置
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    ALLOWED_VIDEO_TYPES: List[str] = ["video/mp4", "video/mpeg", "video/quicktime"]
    
    # 分页默认值
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # 服务主机和端口
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# 创建设置实例
settings = Settings()