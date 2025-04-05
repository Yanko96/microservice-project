#!/bin/bash
# 等待数据库准备好
echo "正在等待PostgreSQL数据库..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "数据库已就绪"

# 检查alembic_version表并处理版本问题
echo "检查迁移版本..."
PG_COUNT=$(PGPASSWORD=password psql -h postgres -U admin -d social_platform -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'alembic_version';")

if [[ $PG_COUNT == *"0"* ]]; then
  echo "没有发现alembic_version表，即将创建初始迁移..."
else
  # 检查是否有版本记录
  VERSION_COUNT=$(PGPASSWORD=password psql -h postgres -U admin -d social_platform -t -c "SELECT COUNT(*) FROM alembic_version;")
  if [[ $VERSION_COUNT == *"0"* ]]; then
    echo "alembic_version表为空，即将设置初始版本..."
    # 获取第一个迁移文件
    FIRST_MIGRATION=$(ls -1 /app/alembic/versions/ | head -n 1 | sed 's/.py//')
    echo "设置初始版本为: $FIRST_MIGRATION"
    cd /app && alembic stamp $FIRST_MIGRATION
  fi
fi

# 运行数据库迁移
echo "执行数据库迁移..."
cd /app && alembic upgrade head

# 启动应用
echo "启动user-service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000