#!/bin/bash
set -e

# 数据库名称
DB_NAME="social_platform_notifications"


# 等待数据库可用
until PGPASSWORD=password psql -h postgres -U admin -d $DB_NAME -c '\q' 2>/dev/null; do
  echo "等待 PostgreSQL 启动..."
  sleep 2
done

echo "数据库 $DB_NAME 已就绪，开始迁移..."

# 执行 Alembic 数据库迁移
alembic upgrade head

# 启动服务
exec uvicorn app.main:app --host 0.0.0.0 --port 8000