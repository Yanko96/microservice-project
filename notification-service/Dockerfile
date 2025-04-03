FROM python:3.11-slim

WORKDIR /app

# 设置 Python 环境
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc curl netcat-openbsd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 添加启动脚本
COPY start.sh .
RUN chmod 755 start.sh && \
    ls -la start.sh && \
    apt-get update && \
    apt-get install -y netcat-openbsd postgresql-client curl && \
    apt-get clean

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["/bin/bash", "/app/start.sh"]