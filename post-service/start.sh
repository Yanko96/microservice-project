#!/bin/bash
set -e

# 数据库名称
DB_NAME="social_platform_posts"

echo "正在等待PostgreSQL数据库..."
until PGPASSWORD=password psql -h postgres -U admin -d $DB_NAME -c '\q' 2>/dev/null; do
  echo "PostgreSQL尚未就绪，等待中..."
  sleep 2
done
echo "数据库 $DB_NAME 已就绪"

# 检查并创建枚举类型函数（作为备用方案）
function ensure_enum_types() {
  echo "检查枚举类型是否存在..."
  
  # 在数据库层面确保枚举类型存在
  PGPASSWORD=password psql -h postgres -U admin -d $DB_NAME -c "
  DO \$\$
  BEGIN
    -- 检查 mediatype 枚举类型
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mediatype') THEN
      CREATE TYPE mediatype AS ENUM ('image', 'video', 'link', 'none', 'IMAGE', 'VIDEO', 'LINK', 'NONE');
      RAISE NOTICE 'Created mediatype enum';
    ELSE
      RAISE NOTICE 'mediatype enum already exists';
    END IF;
    
    -- 检查 visibility 枚举类型
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'visibility') THEN
      CREATE TYPE visibility AS ENUM ('public', 'followers', 'private', 'PUBLIC', 'FOLLOWERS', 'PRIVATE');
      RAISE NOTICE 'Created visibility enum';
    ELSE
      RAISE NOTICE 'visibility enum already exists';
    END IF;
    
    -- 检查 reactiontype 枚举类型
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'reactiontype') THEN
      CREATE TYPE reactiontype AS ENUM ('like', 'love', 'haha', 'wow', 'sad', 'angry', 'LIKE', 'LOVE', 'HAHA', 'WOW', 'SAD', 'ANGRY');
      RAISE NOTICE 'Created reactiontype enum';
    ELSE
      RAISE NOTICE 'reactiontype enum already exists';
    END IF;
  END
  \$\$;
  "
  
  echo "枚举类型检查/创建完成"
}

echo "执行数据库迁移..."
cd /app

# 先尝试备份当前迁移状态（如有）
backup_dir="/tmp/alembic_backup_$(date +%Y%m%d%H%M%S)"
mkdir -p $backup_dir
alembic history > "$backup_dir/history.txt" 2>/dev/null || true
alembic current > "$backup_dir/current.txt" 2>/dev/null || true
echo "迁移状态已备份到 $backup_dir"

# 执行迁移
if alembic upgrade head; then
  echo "迁移成功完成"
else
  echo "迁移失败，尝试恢复..."
  
  # 确保枚举类型存在（备用方案）
  ensure_enum_types
  
  # 重置迁移状态
  INITIAL_VERSION=$(grep "revision = " /app/alembic/versions/initial_migration.py | head -1 | cut -d"'" -f2)
  if [ -n "$INITIAL_VERSION" ]; then
    echo "重置到初始版本: $INITIAL_VERSION"
    alembic stamp $INITIAL_VERSION
    
    # 再次尝试迁移
    if alembic upgrade head; then
      echo "第二次尝试迁移成功"
    else
      echo "迁移仍然失败，记录详细错误日志并继续启动服务..."
      alembic history > "$backup_dir/after_failure_history.txt"
      alembic current > "$backup_dir/after_failure_current.txt"
    fi
  else
    echo "无法确定初始版本，可能需要手动干预"
  fi
fi

echo "启动post-service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000