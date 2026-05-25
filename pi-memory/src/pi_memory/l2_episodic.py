# -*- coding: utf-8 -*-
"""
L2 Episodic Memory - PostgreSQL + pgvector (FTS + vector search + LLM摘要)
历史会话存储
"""

import json
import logging
from typing import Any, Optional, List, Dict, Tuple, Callable
from datetime import datetime
from dataclasses import dataclass, field

import psycopg2

logger = logging.getLogger(__name__)


@dataclass
class MemorySegment:
    """记忆片段"""
    id: int = 0
    session_id: str = ""
    content: str = ""
    summary: str = ""  # LLM 摘要
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 1.0
    access_count: int = 0
    linked_sessions: List[str] = field(default_factory=list)  # 关联会话
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Session:
    """完整会话"""
    id: int = 0
    session_id: str = ""
    title: str = ""
    messages: List[Dict] = field(default_factory=list)
    summary: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    message_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class L2EpisodicMemory:
    """
    L2 情景记忆 - PostgreSQL
    - 历史会话存储
    - pgvector 可用时启用 embedding + 向量检索
    - pgvector 不可用时自动降级为 FTS
    - LLM 自动摘要
    - 去重 + 链接
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "pimemory",
        user: str = "postgres",
        password: str = "",
        summarizer_fn: Optional[Callable[[str, int], str]] = None,
        vectorizer_fn: Optional[Callable[[str], List[float]]] = None,
        vector_dim: int = 1536,
        auto_init: bool = True
    ):
        """
        Args:
            summarizer_fn: 自定义摘要函数，输入(内容, 消息数)，输出摘要
        """
        self.conn_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
        self.summarizer_fn = summarizer_fn
        self.vectorizer_fn = vectorizer_fn
        self.vector_dim = vector_dim
        self.vector_enabled = False
        self._conn = None
        if auto_init:
            self._init_db()
        logger.info(f"L2 Episodic Memory initialized: {host}:{port}/{database}")

    def _get_conn(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(**self.conn_params)
        return self._conn

    def _init_db(self):
        """初始化数据库"""
        conn = self._get_conn()
        cur = conn.cursor()

        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            self.vector_enabled = True
            logger.info("L2 pgvector extension enabled")
        except Exception as e:
            conn.rollback()
            self.vector_enabled = False
            logger.warning(f"L2 pgvector unavailable, using FTS-only mode: {e}")
        
        # 会话表
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

        if self.vector_enabled:
            cur.execute(f"""
                ALTER TABLE episodic_sessions
                ADD COLUMN IF NOT EXISTS embedding VECTOR({self.vector_dim});
            """)
        
        # 全文搜索索引
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_fts 
            ON episodic_sessions USING GIN (
                to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary, ''))
            );
        """)
        
        # 时间索引
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_time 
            ON episodic_sessions (created_at DESC);
        """)
        
        # session_id 索引
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id 
            ON episodic_sessions (session_id);
        """)

        conn.commit()

        if self.vector_enabled:
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
                logger.warning(f"L2 HNSW index unavailable, falling back to IVFFlat: {e}")
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
        mode = "pgvector+FTS" if self.vector_enabled else "FTS-only"
        logger.info(f"L2 sessions table initialized ({mode})")

    # ============================================================
    # 会话操作
    # ============================================================

    def save_session(
        self,
        session_id: str,
        messages: List[Dict],
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        embedding: Optional[List[float]] = None,
        auto_summarize: bool = True
    ) -> Optional[int]:
        """
        保存会话
        
        Args:
            session_id: 会话ID
            messages: 消息列表 [{"role": "user", "content": "..."}]
            title: 会话标题
            tags: 标签
            metadata: 元数据
            auto_summarize: 是否自动生成摘要
        """
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            
            # 生成摘要
            summary = ""
            if auto_summarize and messages:
                summary = self._generate_summary(messages)
            
            # 生成标题
            if not title:
                title = self._generate_title(messages)

            if embedding is None and self.vector_enabled and self.vectorizer_fn:
                embedding = self.vectorizer_fn(f"{title}\n{summary}")

            if embedding and len(embedding) != self.vector_dim:
                logger.warning(
                    f"L2 embedding dim mismatch: got {len(embedding)}, expected {self.vector_dim}; ignoring"
                )
                embedding = None

            embedding_value = self._format_vector(embedding) if self.vector_enabled and embedding else None

            if self.vector_enabled:
                cur.execute("""
                    INSERT INTO episodic_sessions 
                    (session_id, title, messages, summary, tags, message_count, metadata, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
                    ON CONFLICT (session_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        messages = EXCLUDED.messages,
                        summary = EXCLUDED.summary,
                        tags = EXCLUDED.tags,
                        message_count = EXCLUDED.message_count,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding,
                        updated_at = NOW()
                    RETURNING id
                """, (
                    session_id,
                    title,
                    json.dumps(messages, ensure_ascii=False),
                    summary,
                    tags or [],
                    len(messages),
                    json.dumps(metadata or {}, ensure_ascii=False),
                    embedding_value
                ))
            else:
                cur.execute("""
                    INSERT INTO episodic_sessions 
                    (session_id, title, messages, summary, tags, message_count, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        messages = EXCLUDED.messages,
                        summary = EXCLUDED.summary,
                        tags = EXCLUDED.tags,
                        message_count = EXCLUDED.message_count,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    RETURNING id
                """, (
                    session_id,
                    title,
                    json.dumps(messages, ensure_ascii=False),
                    summary,
                    tags or [],
                    len(messages),
                    json.dumps(metadata or {}, ensure_ascii=False)
                ))
            
            session_db_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            
            logger.debug(f"L2 save_session: {session_id}, messages={len(messages)}")
            return session_db_id
        except Exception as e:
            logger.error(f"L2 save_session error: {e}")
            return None

    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, session_id, title, messages, summary, tags,
                       importance, message_count, linked_sessions,
                       metadata, access_count, created_at, updated_at
                FROM episodic_sessions
                WHERE session_id = %s
            """, (session_id,))
            
            row = cur.fetchone()
            cur.close()
            
            if row:
                self._update_access(row[0])
                return Session(
                    id=row[0],
                    session_id=row[1],
                    title=row[2],
                    messages=json.loads(row[3]) if row[3] else [],
                    summary=row[4] or "",
                    tags=row[5] or [],
                    importance=row[6],
                    message_count=row[7],
                    linked_sessions=row[8] or [],
                    metadata=row[9] or {},
                    access_count=row[10] + 1,
                    created_at=row[11],
                    updated_at=row[12]
                )
            return None
        except Exception as e:
            logger.error(f"L2 get_session error: {e}")
            return None

    def _update_access(self, db_id: int):
        """更新访问次数"""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                UPDATE episodic_sessions
                SET access_count = access_count + 1,
                    updated_at = NOW()
                WHERE id = %s
            """, (db_id,))
            conn.commit()
            cur.close()
        except Exception:
            pass

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM episodic_sessions WHERE session_id = %s", (session_id,))
            conn.commit()
            cur.close()
            return True
        except Exception as e:
            logger.error(f"L2 delete_session error: {e}")
            return False

    # ============================================================
    # 搜索
    # ============================================================

    def search(
        self,
        query: str,
        limit: int = 10,
        tags: Optional[List[str]] = None,
        query_embedding: Optional[List[float]] = None,
        hybrid_weight: float = 0.7
    ) -> List[Tuple[Session, float]]:
        """
        搜索会话
        
        Returns:
            (Session, 相关度) 列表
        """
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            
            tag_filter = ""
            if tags:
                tag_list = " OR ".join([f"%s = ANY(tags)" for _ in tags])
                tag_filter = f"AND ({tag_list})"

            results: Dict[str, Tuple[Session, float]] = {}

            if (
                self.vector_enabled
                and query_embedding
                and len(query_embedding) == self.vector_dim
            ):
                cur.execute(f"""
                    SELECT id, session_id, title, messages, summary, tags,
                           importance, message_count, linked_sessions,
                           metadata, access_count, created_at, updated_at,
                           embedding <=> %s::vector as distance
                    FROM episodic_sessions
                    WHERE embedding IS NOT NULL
                          {tag_filter}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, tuple(
                    [self._format_vector(query_embedding)]
                    + (tags or [])
                    + [self._format_vector(query_embedding), limit * 2]
                ))

                for row in cur.fetchall():
                    session = self._row_to_session(row)
                    distance = float(row[13]) if row[13] is not None else 1.0
                    score = max(0.0, 1.0 - distance / 2.0) * hybrid_weight
                    results[session.session_id] = (session, score)
            
            cur.execute(f"""
                SELECT id, session_id, title, messages, summary, tags,
                       importance, message_count, linked_sessions,
                       metadata, access_count, created_at, updated_at,
                       ts_rank(
                           to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary, '')),
                           plainto_tsquery('simple', %s)
                       ) as rank
                FROM episodic_sessions
                WHERE to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary, ''))
                      @@ plainto_tsquery('simple', %s)
                      {tag_filter}
                ORDER BY rank DESC
                LIMIT %s
            """, tuple([query, query] + (tags or []) + [limit]))
            
            rows = cur.fetchall()
            cur.close()
            
            for row in rows:
                self._update_access(row[0])
                session = self._row_to_session(row)
                fts_score = min(float(row[13]) * 10, 1.0) if row[13] else 0.5
                score = fts_score * (1 - hybrid_weight if query_embedding else 1.0)
                existing = results.get(session.session_id)
                if existing:
                    results[session.session_id] = (session, existing[1] + score)
                else:
                    results[session.session_id] = (session, score)
            
            return sorted(results.values(), key=lambda item: item[1], reverse=True)[:limit]
        except Exception as e:
            logger.error(f"L2 search error: {e}")
            return []

    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[Session]:
        """按标签搜索"""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, session_id, title, messages, summary, tags,
                       importance, message_count, linked_sessions,
                       metadata, access_count, created_at, updated_at
                FROM episodic_sessions
                WHERE tags && %s
                ORDER BY importance DESC, created_at DESC
                LIMIT %s
            """, (tags, limit))
            
            rows = cur.fetchall()
            cur.close()
            
            return [Session(
                id=row[0],
                session_id=row[1],
                title=row[2],
                messages=json.loads(row[3]) if row[3] else [],
                summary=row[4] or "",
                tags=row[5] or [],
                importance=row[6],
                message_count=row[7],
                linked_sessions=row[8] or [],
                metadata=row[9] or {},
                access_count=row[10],
                created_at=row[11],
                updated_at=row[12]
            ) for row in rows]
        except Exception as e:
            logger.error(f"L2 search_by_tags error: {e}")
            return []

    # ============================================================
    # 关联
    # ============================================================

    def link_sessions(self, session_a: str, session_b: str) -> bool:
        """关联两个会话"""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE episodic_sessions
                SET linked_sessions = array_distinct(array_append(linked_sessions, %s)),
                    updated_at = NOW()
                WHERE session_id = %s
            """, (session_b, session_a))
            
            cur.execute("""
                UPDATE episodic_sessions
                SET linked_sessions = array_distinct(array_append(linked_sessions, %s)),
                    updated_at = NOW()
                WHERE session_id = %s
            """, (session_a, session_b))
            
            conn.commit()
            cur.close()
            return True
        except Exception as e:
            logger.error(f"L2 link_sessions error: {e}")
            return False

    def get_related_sessions(self, session_id: str, limit: int = 5) -> List[Session]:
        """获取关联会话"""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT s2.id, s2.session_id, s2.title, s2.messages, s2.summary, s2.tags,
                       s2.importance, s2.message_count, s2.linked_sessions,
                       s2.metadata, s2.access_count, s2.created_at, s2.updated_at
                FROM episodic_sessions s1
                JOIN episodic_sessions s2 ON s2.session_id = ANY(s1.linked_sessions)
                WHERE s1.session_id = %s AND s2.session_id != %s
                ORDER BY s2.access_count DESC
                LIMIT %s
            """, (session_id, session_id, limit))
            
            rows = cur.fetchall()
            cur.close()
            
            return [Session(
                id=row[0],
                session_id=row[1],
                title=row[2],
                messages=json.loads(row[3]) if row[3] else [],
                summary=row[4] or "",
                tags=row[5] or [],
                importance=row[6],
                message_count=row[7],
                linked_sessions=row[8] or [],
                metadata=row[9] or {},
                access_count=row[10],
                created_at=row[11],
                updated_at=row[12]
            ) for row in rows]
        except Exception as e:
            logger.error(f"L2 get_related error: {e}")
            return []

    # ============================================================
    # 摘要生成
    # ============================================================

    def _generate_summary(self, messages: List[Dict]) -> str:
        """生成会话摘要"""
        if self.summarizer_fn:
            return self.summarizer_fn(messages, len(messages))
        
        # 默认摘要
        user_msgs = [m for m in messages if m.get("role") == "user"]
        if user_msgs:
            first = user_msgs[0].get("content", "")[:100]
            return f"会话共{len(messages)}条消息，主题: {first}..."
        
        return f"会话共{len(messages)}条消息"

    def _generate_title(self, messages: List[Dict]) -> str:
        """生成会话标题"""
        user_msgs = [m for m in messages if m.get("role") == "user"]
        if user_msgs:
            first = user_msgs[0].get("content", "")[:50]
            return first + ("..." if len(first) >= 50 else "")
        
        return f"会话_{datetime.now().strftime('%Y%m%d_%H%M')}"

    def _format_vector(self, values: List[float]) -> str:
        """格式化为 pgvector 字面量"""
        return "[" + ",".join(str(float(v)) for v in values) + "]"

    def _row_to_session(self, row) -> Session:
        """把 SELECT 结果映射为 Session；兼容带额外 score/distance 列的查询。"""
        messages = json.loads(row[3]) if isinstance(row[3], str) else (row[3] or [])
        return Session(
            id=row[0],
            session_id=row[1],
            title=row[2],
            messages=messages,
            summary=row[4] or "",
            tags=row[5] or [],
            importance=row[6],
            message_count=row[7],
            linked_sessions=row[8] or [],
            metadata=row[9] or {},
            access_count=row[10],
            created_at=row[11],
            updated_at=row[12],
        )

    def regenerate_summary(self, session_id: str) -> Optional[str]:
        """重新生成摘要"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        summary = self._generate_summary(session.messages)
        
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                UPDATE episodic_sessions
                SET summary = %s, updated_at = NOW()
                WHERE session_id = %s
            """, (summary, session_id))
            conn.commit()
            cur.close()
            return summary
        except Exception as e:
            logger.error(f"L2 regenerate_summary error: {e}")
            return None

    # ============================================================
    # 工具
    # ============================================================

    def count(self) -> int:
        """统计会话数量"""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM episodic_sessions")
            count = cur.fetchone()[0]
            cur.close()
            return count
        except Exception as e:
            logger.error(f"L2 count error: {e}")
            return 0

    def get_recent(self, limit: int = 10) -> List[Session]:
        """获取最近会话"""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, session_id, title, messages, summary, tags,
                       importance, message_count, linked_sessions,
                       metadata, access_count, created_at, updated_at
                FROM episodic_sessions
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            
            rows = cur.fetchall()
            cur.close()
            
            return [Session(
                id=row[0],
                session_id=row[1],
                title=row[2],
                messages=json.loads(row[3]) if row[3] else [],
                summary=row[4] or "",
                tags=row[5] or [],
                importance=row[6],
                message_count=row[7],
                linked_sessions=row[8] or [],
                metadata=row[9] or {},
                access_count=row[10],
                created_at=row[11],
                updated_at=row[12]
            ) for row in rows]
        except Exception as e:
            logger.error(f"L2 get_recent error: {e}")
            return []

    def get_hot(self, limit: int = 10) -> List[Session]:
        """获取热门会话"""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, session_id, title, messages, summary, tags,
                       importance, message_count, linked_sessions,
                       metadata, access_count, created_at, updated_at
                FROM episodic_sessions
                ORDER BY access_count DESC
                LIMIT %s
            """, (limit,))
            
            rows = cur.fetchall()
            cur.close()
            
            return [Session(
                id=row[0],
                session_id=row[1],
                title=row[2],
                messages=json.loads(row[3]) if row[3] else [],
                summary=row[4] or "",
                tags=row[5] or [],
                importance=row[6],
                message_count=row[7],
                linked_sessions=row[8] or [],
                metadata=row[9] or {},
                access_count=row[10],
                created_at=row[11],
                updated_at=row[12]
            ) for row in rows]
        except Exception as e:
            logger.error(f"L2 get_hot error: {e}")
            return []

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None

    def ping(self) -> bool:
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            return True
        except Exception:
            return False
