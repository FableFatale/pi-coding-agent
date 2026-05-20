#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pi Memory 数据库初始化 (不需要 pgvector)
"""

import sys


def main():
    print("=" * 50)
    print("  Pi Memory 数据库初始化")
    print("=" * 50)
    
    # 交互式输入密码
    password = input("\n请输入 PostgreSQL 密码: ").strip()
    if not password:
        password = "postgres"
    
    print(f"\n连接 PostgreSQL...")
    
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # 连接默认数据库
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="postgres",
            user="postgres",
            password=password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # 创建数据库
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'pimemory'")
        if not cur.fetchone():
            cur.execute("CREATE DATABASE pimemory")
            print("✅ 数据库 pimemory 创建成功")
        else:
            print("✅ 数据库 pimemory 已存在")
        
        cur.close()
        conn.close()
        
        # 连接到目标数据库
        print("\n连接 pimemory 数据库...")
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="pimemory",
            user="postgres",
            password=password
        )
        cur = conn.cursor()
        
        # 创建表和索引 (使用纯 FTS，不需要 pgvector)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS episodic_memories (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                content_searchable TSVECTOR,
                metadata JSONB DEFAULT '{}',
                importance FLOAT DEFAULT 1.0,
                access_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # 创建 FTS 索引
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_fts 
            ON episodic_memories USING GIN (content_searchable);
        """)
        
        # 创建触发器
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_content_search()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.content_searchable := to_tsvector('simple', COALESCE(NEW.content, ''));
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        cur.execute("""
            DROP TRIGGER IF EXISTS trigger_fts ON episodic_memories;
            CREATE TRIGGER trigger_fts
            BEFORE INSERT OR UPDATE ON episodic_memories
            FOR EACH ROW EXECUTE FUNCTION update_content_search();
        """)
        
        # 创建时间索引
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_time 
            ON episodic_memories (created_at DESC);
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("✅ 表和索引创建成功 (FTS模式)")
        
        print("\n" + "=" * 50)
        print("  ✅ 初始化完成！")
        print("=" * 50)
        print("\n下一步:")
        print("  python examples\\basic_usage.py")
        
    except ImportError:
        print("❌ 请先安装: pip install psycopg2-binary")
    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
