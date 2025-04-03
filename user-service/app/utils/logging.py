import logging
import sys
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

    return logger