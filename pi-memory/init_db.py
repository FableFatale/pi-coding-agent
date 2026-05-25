#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pi Memory 数据库初始化 (优先启用 pgvector，失败时降级 FTS)
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
        
        # 优先启用 pgvector；没有安装扩展时继续使用纯 FTS。
        vector_enabled = False
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            vector_enabled = True
            print("✅ pgvector 扩展已启用")
        except Exception as e:
            conn.rollback()
            print(f"⚠️  pgvector 不可用，使用 FTS 模式: {e}")

        # 创建表和索引
        cur.execute("""
            CREATE TABLE IF NOT EXISTS episodic_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                title VARCHAR(500),
                messages JSONB DEFAULT '[]',
                summary TEXT DEFAULT '',
                tags TEXT[] DEFAULT '{}',
                importance FLOAT DEFAULT 1.0,
                message_count INT DEFAULT 0,
                access_count INT DEFAULT 0,
                linked_sessions TEXT[] DEFAULT '{}',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)

        if vector_enabled:
            cur.execute("""
                ALTER TABLE episodic_sessions
                ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);
            """)
        
        # 创建 FTS 索引
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_fts 
            ON episodic_sessions USING GIN (
                to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary, ''))
            );
        """)

        # 创建时间索引
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_time 
            ON episodic_sessions (created_at DESC);
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id 
            ON episodic_sessions (session_id);
        """)

        conn.commit()

        if vector_enabled:
            try:
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_embedding_hnsw
                    ON episodic_sessions
                    USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                    WHERE embedding IS NOT NULL;
                """)
            except Exception as e:
                conn.rollback()
                print(f"⚠️  HNSW 索引不可用，改用 IVFFlat: {e}")
                cur = conn.cursor()
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_embedding_ivfflat
                    ON episodic_sessions
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                    WHERE embedding IS NOT NULL;
                """)
        
        conn.commit()
        cur.close()
        conn.close()
        
        mode = "pgvector + FTS" if vector_enabled else "FTS"
        print(f"✅ 表和索引创建成功 ({mode}模式)")
        
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
