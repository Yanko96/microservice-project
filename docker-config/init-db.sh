#!/bin/bash
set -e

# 等待PostgreSQL启动
until PGPASSWORD=password psql -h postgres -U admin -d postgres -c '\l'; do
  echo "Waiting for postgres..."
  sleep 2
done

# 创建数据库（如果不存在）
PGPASSWORD=password psql -h postgres -U admin -d postgres <<EOF
  SELECT 'CREATE DATABASE social_platform_users' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'social_platform_users');
  SELECT 'CREATE DATABASE social_platform_posts' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'social_platform_posts');
  SELECT 'CREATE DATABASE social_platform_notifications' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'social_platform_notifications');
EOF
echo "Databases created successfully"