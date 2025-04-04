import logging
import sys
import json
from typing import Dict, Any, Optional

from loguru import logger
from pydantic import BaseModel

from app.core.config import settings

# 配置 loguru 日志器
class LoggingConfig(BaseModel):
    LOGGING_LEVEL: str = settings.LOG_LEVEL

# 拦截所有标准库的日志
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # 获取对应的 Loguru 级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 寻找调用者
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

# 定义结构化日志格式
class StructuredLogger:
    def __init__(self, logger_instance):
        self.logger = logger_instance
    
    def _log(self, level: str, message: str, **kwargs):
        """
        记录结构化日志
        """
        # 添加服务名称
        kwargs["service"] = "post-service"
        
        # 添加环境信息
        kwargs["environment"] = settings.ENVIRONMENT
        
        # 记录日志
        log_func = getattr(self.logger, level)
        if kwargs:
            # 如果有额外信息，添加为JSON
            log_func(f"{message} | {json.dumps(kwargs)}")
        else:
            log_func(message)
    
    def debug(self, message: str, **kwargs):
        self._log("debug", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log("error", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log("critical", message, **kwargs)

def setup_logging():
    # 配置日志级别
    config = LoggingConfig()
    logging_level = config.LOGGING_LEVEL

    # 拦截所有的标准库日志
    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    # 删除所有的默认处理器
    logger.configure(handlers=[{"sink": sys.stderr, "level": logging_level}])

    # 修改 uvicorn 的日志
    for _log in ["uvicorn", "uvicorn.error", "fastapi"]:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]

    # 创建结构化日志
    structured_logger = StructuredLogger(logger)

    return structured_logger