#!/bin/bash
set -e

# ✅ 使用 socket 而不是 TCP
until pg_isready -U admin; do
  echo "Waiting for postgres to be ready..."
  sleep 2
done

# ✅ 每个数据库存在性检测 + 创建
psql -U admin -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'social_platform_users'" | grep -q 1 || \
  psql -U admin -d postgres -c "CREATE DATABASE social_platform_users"

psql -U admin -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'social_platform_posts'" | grep -q 1 || \
  psql -U admin -d postgres -c "CREATE DATABASE social_platform_posts"

psql -U admin -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'social_platform_notifications'" | grep -q 1 || \
  psql -U admin -d postgres -c "CREATE DATABASE social_platform_notifications"

psql -U admin -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'grafana'" | grep -q 1 || \
  psql -U admin -d postgres -c "CREATE DATABASE grafana"

echo "✅ All databases created successfully"
