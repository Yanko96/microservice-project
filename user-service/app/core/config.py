import os
from typing import List, Optional, Union, Dict, Any
from pydantic import AnyHttpUrl, field_validator, HttpUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "社交平台用户服务"
    API_V1_STR: str = "/api/v1"
    
    # 环境标识
    ENVIRONMENT: str = "development"
    
    # 数据库配置
    DATABASE_URL: str
    
    # JWT 配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时
    
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
    KAFKA_TOPIC_LOGS: str = "service.logs"
    KAFKA_TOPIC_NOTIFICATIONS: str = "user.notifications"
    
    # MinIO配置（对象存储）
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_USER_BUCKET: str = "user-content"
    
    # OAuth2 配置
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost/api/v1/auth/oauth/github/callback"
    
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost/api/v1/auth/oauth/google/callback"
    
    # 安全配置
    SECURITY_PASSWORD_SALT: str = "social-platform-salt"
    
    # API 文档
    DOCS_URL: Optional[str] = "/docs"
    OPENAPI_URL: Optional[str] = "/openapi.json"
    REDOC_URL: Optional[str] = "/redoc"
    
    # 日志级别
    LOG_LEVEL: str = "INFO"
    
    # 上传文件存储路径
    UPLOADS_DIR: str = "/app/uploads"
    
    # 静态文件配置
    STATIC_DIR: str = "/app/static"
    STATIC_URL: str = "/static"
    
    # 服务主机和端口
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# 创建设置实例
settings = Settings()