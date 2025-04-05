#!/usr/bin/env python3
"""
修复迁移脚本 - 确保创建所有必要的表结构和枚举类型
"""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 数据库配置
DB_PARAMS = {
    "dbname": "social_platform_notifications",
    "user": "admin",
    "password": "password",
    "host": "postgres",
    "port": "5432"
}

def run_sql_commands(sql_commands):
    """运行SQL命令列表"""
    try:
        # 连接到数据库
        conn = psycopg2.connect(**DB_PARAMS)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        for sql in sql_commands:
            print(f"执行SQL: {sql[:60]}...")
            cursor.execute(sql)
        
        cursor.close()
        conn.close()
        print("所有SQL命令执行完成")
        return True
    except Exception as e:
        print(f"执行SQL时出错: {e}")
        return False

def fix_migration():
    """修复迁移，确保创建所有必要的表"""
    # 检查枚举类型是否存在并创建
    enum_check_commands = [
        """
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notificationtype') THEN
            CREATE TYPE notificationtype AS ENUM ('follow', 'post_like', 'post_comment', 'comment_like', 'comment_reply', 'mention', 'system', 'FOLLOW', 'POST_LIKE', 'POST_COMMENT', 'COMMENT_LIKE', 'COMMENT_REPLY', 'MENTION', 'SYSTEM');
            RAISE NOTICE 'Created notificationtype enum';
          ELSE
            RAISE NOTICE 'notificationtype enum already exists';
          END IF;
        END
        $$;
        """
    ]
    
    # 创建表结构
    table_commands = [
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            type notificationtype NOT NULL,
            title VARCHAR NOT NULL,
            body TEXT,
            sender_id INTEGER,
            sender_name VARCHAR,
            sender_avatar VARCHAR,
            resource_type VARCHAR,
            resource_id INTEGER,
            meta_data JSON,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_notifications_id ON notifications (id);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications (created_at);
        """
    ]
    
    # 设置alembic版本
    alembic_commands = [
        """
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL,
            PRIMARY KEY (version_num)
        );
        """,
        """
        DELETE FROM alembic_version;
        """,
        """
        INSERT INTO alembic_version (version_num) VALUES ('9b91adc45f2e');
        """
    ]
    
    # 执行所有命令
    all_commands = enum_check_commands + table_commands + alembic_commands
    return run_sql_commands(all_commands)


if __name__ == "__main__":
    print("开始修复notification-service的数据库迁移...")
    success = fix_migration()
    if success:
        print("✅ 修复成功！数据库表已创建完成")
    else:
        print("❌ 修复失败，请检查错误日志")