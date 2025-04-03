#!/bin/bash
set -e

# 数据库名称
DB_NAME="social_platform_users"

echo "正在等待PostgreSQL数据库..."
until PGPASSWORD=password psql -h postgres -U admin -d $DB_NAME -c '\q' 2>/dev/null; do
  sleep 1
done
echo "数据库 $DB_NAME 已就绪"

echo "执行数据库迁移..."
cd /app && alembic upgrade head || {
  echo "迁移失败，尝试重置迁移状态..."
  # 如果失败，获取初始版本并重置
  INITIAL_VERSION=$(grep "revision = " /app/alembic/versions/initial_migration.py | head -1 | cut -d"'" -f2)
  echo "重置到初始版本: $INITIAL_VERSION"
  alembic stamp $INITIAL_VERSION
  # 再次尝试迁移
  alembic upgrade head
}

echo "启动user-service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000