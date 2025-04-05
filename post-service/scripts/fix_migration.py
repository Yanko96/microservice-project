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
    "dbname": "social_platform_posts",
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
          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mediatype') THEN
            CREATE TYPE mediatype AS ENUM ('image', 'video', 'link', 'none', 'IMAGE', 'VIDEO', 'LINK', 'NONE');
            RAISE NOTICE 'Created mediatype enum';
          ELSE
            RAISE NOTICE 'mediatype enum already exists';
          END IF;
        END
        $$;
        """,
        """
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'visibility') THEN
            CREATE TYPE visibility AS ENUM ('public', 'followers', 'private', 'PUBLIC', 'FOLLOWERS', 'PRIVATE');
            RAISE NOTICE 'Created visibility enum';
          ELSE
            RAISE NOTICE 'visibility enum already exists';
          END IF;
        END
        $$;
        """,
        """
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'reactiontype') THEN
            CREATE TYPE reactiontype AS ENUM ('like', 'love', 'haha', 'wow', 'sad', 'angry', 'LIKE', 'LOVE', 'HAHA', 'WOW', 'SAD', 'ANGRY');
            RAISE NOTICE 'Created reactiontype enum';
          ELSE
            RAISE NOTICE 'reactiontype enum already exists';
          END IF;
        END
        $$;
        """
    ]
    
    # 创建表结构
    table_commands = [
        """
        CREATE TABLE IF NOT EXISTS tags (
            name VARCHAR NOT NULL PRIMARY KEY,
            post_count INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            content TEXT,
            media_type mediatype NOT NULL DEFAULT 'none',
            media_urls JSON,
            location VARCHAR,
            visibility visibility NOT NULL DEFAULT 'public',
            is_edited BOOLEAN DEFAULT FALSE,
            is_pinned BOOLEAN DEFAULT FALSE,
            comment_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            share_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_posts_id ON posts (id);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_posts_user_id ON posts (user_id);
        """,
        """
        CREATE TABLE IF NOT EXISTS post_tag (
            post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            tag_name VARCHAR NOT NULL REFERENCES tags(name) ON DELETE CASCADE,
            PRIMARY KEY (post_id, tag_name)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS comments (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
            like_count INTEGER DEFAULT 0,
            reply_count INTEGER DEFAULT 0,
            is_edited BOOLEAN DEFAULT FALSE,
            is_deleted BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_comments_id ON comments (id);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_comments_post_id ON comments (post_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_comments_user_id ON comments (user_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_comments_parent_id ON comments (parent_id);
        """,
        """
        CREATE TABLE IF NOT EXISTS reactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            type reactiontype NOT NULL DEFAULT 'like',
            post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
            comment_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE,
            CONSTRAINT uix_user_post_reaction UNIQUE (user_id, post_id),
            CONSTRAINT uix_user_comment_reaction UNIQUE (user_id, comment_id)
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_reactions_id ON reactions (id);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_reactions_user_id ON reactions (user_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_reactions_post_id ON reactions (post_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_reactions_comment_id ON reactions (comment_id);
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
        INSERT INTO alembic_version (version_num) VALUES ('8b72e3a19f8e');
        """
    ]
    
    # 执行所有命令
    all_commands = enum_check_commands + table_commands + alembic_commands
    return run_sql_commands(all_commands)


if __name__ == "__main__":
    print("开始修复post-service的数据库迁移...")
    success = fix_migration()
    if success:
        print("✅ 修复成功！数据库表已创建完成")
    else:
        print("❌ 修复失败，请检查错误日志")