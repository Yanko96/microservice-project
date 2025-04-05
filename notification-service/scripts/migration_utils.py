#!/usr/bin/env python3
"""
迁移工具脚本 - 用于解决和诊断Alembic迁移问题
用法:
    python migration_utils.py check_enums  # 检查枚举类型是否存在
    python migration_utils.py create_enums  # 创建所需的枚举类型
    python migration_utils.py reset  # 重置迁移状态
"""

import sys
import psycopg2
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 数据库连接信息
DB_PARAMS = {
    "dbname": "social_platform_notifications",
    "user": "admin",
    "password": "password",
    "host": "postgres",
    "port": "5432"
}

# 所需的枚举类型
ENUM_TYPES = {
    "notificationtype": ["follow", "post_like", "post_comment", "comment_like", "comment_reply", "mention", "system"]
}


def connect_db():
    """建立数据库连接"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except psycopg2.Error as e:
        print(f"无法连接到数据库: {e}")
        sys.exit(1)


def check_enums():
    """检查枚举类型是否存在"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("检查枚举类型:")
    
    for enum_name in ENUM_TYPES:
        cursor.execute(
            "SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = %s)",
            (enum_name,)
        )
        exists = cursor.fetchone()[0]
        
        if exists:
            cursor.execute(
                "SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = %s)",
                (enum_name,)
            )
            values = [row[0] for row in cursor.fetchall()]
            print(f"  ✓ {enum_name}: 存在 (值: {', '.join(values)})")
        else:
            print(f"  ✗ {enum_name}: 不存在")
    
    cursor.close()
    conn.close()


def create_enums():
    """创建所需的枚举类型"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("创建枚举类型:")
    
    for enum_name, values in ENUM_TYPES.items():
        try:
            # 检查是否存在
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = %s)",
                (enum_name,)
            )
            exists = cursor.fetchone()[0]
            
            if not exists:
                # 创建枚举类型
                values_str = ", ".join([f"'{v}'" for v in values])
                cursor.execute(f"CREATE TYPE {enum_name} AS ENUM ({values_str})")
                print(f"  ✓ {enum_name}: 已创建")
            else:
                print(f"  ℹ {enum_name}: 已存在，跳过")
        except psycopg2.Error as e:
            print(f"  ✗ {enum_name}: 创建失败 - {e}")
    
    cursor.close()
    conn.close()


def reset_migration():
    """重置迁移状态"""
    # 获取初始版本ID
    initial_version = None
    migration_file = "alembic/versions/initial_migration.py"
    
    if os.path.exists(migration_file):
        with open(migration_file, "r") as f:
            for line in f:
                if "revision = " in line:
                    initial_version = line.split("'")[1]
                    break
    
    if not initial_version:
        print("无法找到初始版本ID")
        return
    
    print(f"重置迁移版本到: {initial_version}")
    os.system(f"cd /app && alembic stamp {initial_version}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check_enums":
        check_enums()
    elif command == "create_enums":
        create_enums()
    elif command == "reset":
        reset_migration()
    else:
        print(f"未知命令: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()