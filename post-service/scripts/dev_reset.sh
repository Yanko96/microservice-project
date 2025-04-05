#!/bin/bash

# === 配置参数 ===
DB_NAME="social_platform"
DB_USER="admin"
DB_HOST="postgres"
ALEMBIC_INI="alembic/alembic.ini"
REBUILD_SCRIPT="scripts/rebuild_index.py"

echo "🔄 正在重置开发数据库和索引..."

# === Step 1: 连接 postgres 数据库，DROP 并重新 CREATE 目标库 ===
echo "📦 清空数据库：$DB_NAME"

PGPASSWORD=password psql -U "$DB_USER" -h "$DB_HOST" -d postgres <<EOF
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME;
EOF

# === Step 2: 执行 Alembic 迁移 ===
echo "🚧 执行 Alembic upgrade..."
alembic -c "$ALEMBIC_INI" upgrade head

# === Step 3: 重建 Elasticsearch 索引（可选） ===
if [ -f "$REBUILD_SCRIPT" ]; then
  echo "🔍 重建 Elasticsearch 索引..."
  python "$REBUILD_SCRIPT"
else
  echo "⚠️ 未找到索引脚本: $REBUILD_SCRIPT，跳过索引重建。"
fi

echo "✅ 全部完成！数据库已重建，索引已更新。"
