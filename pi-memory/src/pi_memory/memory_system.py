# -*- coding: utf-8 -*-
"""
Pi Memory - 三层记忆系统 (升级版)

L1: Working Memory (Redis) - 会话消息 + ContextCompressor
L2: Episodic Memory (PostgreSQL) - 历史会话 + LLM摘要
L2.5: Curated Memory (文件) - 共享记忆 + 用户信息
L3: Semantic Memory (skills/) - 技能知识 + Pinecone钩子
"""

import logging
from typing import Any, Optional, List, Dict, Tuple, Callable

from .l1_working import L1WorkingMemory, Message, CompressionResult
from .l2_episodic import L2EpisodicMemory, Session, MemorySegment
from .l25_curated import L25CuratedMemory, CuratedEntry
from .l3_semantic import L3SemanticMemory, Skill, Conflict, ConflictResult

logger = logging.getLogger(__name__)


class MemorySystem:
    """
    三层记忆系统 (升级版)
    
    L1: Working Memory - Redis (会话消息, ContextCompressor)
    L2: Episodic Memory - PostgreSQL (历史会话, LLM摘要)
    L2.5: Curated Memory - 文件 (共享记忆, 用户信息)
    L3: Semantic Memory - skills/ (技能知识, Pinecone钩子)
    """

    def __init__(
        self,
        # L1 Redis
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        l1_ttl: int = 3600,
        
        # L2 PostgreSQL
        pg_host: str = "localhost",
        pg_port: int = 5432,
        pg_database: str = "pimemory",
        pg_user: str = "postgres",
        pg_password: str = "",
        
        # L2.5 Curated (文件)
        curated_dir: Optional[str] = None,
        
        # L3 Skills (文件 + Pinecone)
        skills_dir: Optional[str] = None,
        pinecone_api_key: Optional[str] = None,
        pinecone_env: str = "us-east-1",
        
        # 自定义函数
        compressor_fn: Optional[Callable[[List[Message]], str]] = None,
        summarizer_fn: Optional[Callable[[List[Dict]], str]] = None,
        vectorizer_fn: Optional[Callable[[str], List[float]]] = None
    ):
        """
        初始化记忆系统
        
        Args:
            compressor_fn: L1 压缩函数
            summarizer_fn: L2 摘要生成函数
            vectorizer_fn: L3 向量化函数
        """
        # L1 工作记忆
        self.l1 = L1WorkingMemory(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            ttl=l1_ttl,
            compressor_fn=compressor_fn
        )
        
        # L2 情景记忆
        self.l2 = L2EpisodicMemory(
            host=pg_host,
            port=pg_port,
            database=pg_database,
            user=pg_user,
            password=pg_password,
            summarizer_fn=summarizer_fn
        )
        
        # L2.5 策划记忆
        self.l2_5 = L25CuratedMemory(base_dir=curated_dir)
        
        # L3 语义记忆
        self.l3 = L3SemanticMemory(
            base_dir=skills_dir,
            pinecone_api_key=pinecone_api_key,
            pinecone_env=pinecone_env,
            vectorizer_fn=vectorizer_fn
        )
        
        logger.info("Memory System initialized (upgraded)")

    # ============================================================
    # L1: 工作记忆 (会话消息)
    # ============================================================
    
    def session_create(self, session_id: str, metadata: Optional[Dict] = None) -> bool:
        """创建会话"""
        return self.l1.create_session(session_id, metadata)
    
    def session_add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """添加消息"""
        return self.l1.add_message(session_id, role, content, metadata)
    
    def session_get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Message]:
        """获取消息"""
        return self.l1.get_messages(session_id, limit)
    
    def session_compress(self, session_id: str, preserve_count: int = 50) -> Optional[CompressionResult]:
        """压缩会话"""
        return self.l1.compress(session_id, preserve_count)
    
    def session_delete(self, session_id: str) -> bool:
        """删除会话"""
        return self.l1.delete_session(session_id)

    # ============================================================
    # L2: 情景记忆 (历史会话)
    # ============================================================
    
    def save_session(
        self,
        session_id: str,
        messages: List[Dict],
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        auto_summarize: bool = True
    ) -> Optional[int]:
        """保存会话到历史"""
        return self.l2.save_session(session_id, messages, title, tags, auto_summarize=auto_summarize)
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """获取历史会话"""
        return self.l2.get_session(session_id)
    
    def search_sessions(self, query: str, limit: int = 10) -> List[Tuple[Session, float]]:
        """搜索历史会话"""
        return self.l2.search(query, limit)
    
    def get_related_sessions(self, session_id: str, limit: int = 5) -> List[Session]:
        """获取关联会话"""
        return self.l2.get_related_sessions(session_id, limit)

    # ============================================================
    # L2.5: 策划记忆 (文件)
    # ============================================================
    
    def memory_add(self, content: str, author: str = "agent", tags: Optional[List[str]] = None) -> bool:
        """添加共享记忆"""
        return self.l2_5.add_entry(content, author, tags)
    
    def memory_add_user(self, key: str, value: str) -> bool:
        """添加用户信息"""
        return self.l2_5.add_user_info(key, value)
    
    def memory_search(self, keyword: str) -> List[CuratedEntry]:
        """搜索记忆"""
        return self.l2_5.search(keyword)
    
    def memory_read(self) -> str:
        """读取共享记忆"""
        return self.l2_5.read_memory()
    
    def user_read(self) -> str:
        """读取用户信息"""
        return self.l2_5.read_user()

    # ============================================================
    # L3: 语义记忆 (技能)
    # ============================================================
    
    def skill_add(
        self,
        skill_id: str,
        name: str,
        content: str,
        description: str = "",
        category: str = "general",
        level: str = "beginner",
        tags: Optional[List[str]] = None
    ) -> bool:
        """添加技能"""
        return self.l3.add_skill(skill_id, name, content, description, category, level, tags)
    
    def skill_get(self, skill_id: str) -> Optional[Skill]:
        """获取技能"""
        return self.l3.get_skill(skill_id)
    
    def skill_search(self, query: str, category: Optional[str] = None, limit: int = 10) -> List[Skill]:
        """搜索技能"""
        return self.l3.search(query, category, limit=limit)
    
    def skill_detect_conflict(self, content: str, name: str = "") -> ConflictResult:
        """检测技能冲突"""
        return self.l3.detect_conflict(content, name)

    # ============================================================
    # 快捷方法
    # ============================================================
    
    def prefetch(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        预取相关记忆
        
        Args:
            query: 当前查询/任务
            session_id: 当前会话ID
            
        Returns:
            预取的上下文
        """
        context = {
            "current_session": None,
            "relevant_sessions": [],
            "curated_memory": [],
            "relevant_skills": []
        }
        
        # 当前会话
        if session_id:
            context["current_session"] = self.session_get_messages(session_id)
        
        # 相关历史会话
        sessions = self.search_sessions(query, limit=3)
        context["relevant_sessions"] = [
            {"id": s.id, "title": s.title, "summary": s.summary}
            for s, _ in sessions
        ]
        
        # 共享记忆
        memory_entries = self.memory_search(query)
        context["curated_memory"] = [e.content for e in memory_entries]
        
        # 相关技能
        skills = self.skill_search(query, limit=5)
        context["relevant_skills"] = [
            {"id": s.id, "name": s.name, "description": s.description}
            for s in skills
        ]
        
        return context

    def sync_session_to_history(self, session_id: str, tags: Optional[List[str]] = None) -> Optional[int]:
        """将会话同步到历史"""
        messages = self.session_get_messages(session_id)
        if not messages:
            return None
        
        msg_dicts = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        
        return self.save_session(session_id, msg_dicts, tags=tags)

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "l1": {
                "status": "ok" if self.l1.ping() else "error",
                "info": self.l1.info()
            },
            "l2": {
                "status": "ok" if self.l2.ping() else "error",
                "count": self.l2.count()
            },
            "l2_5": {
                "status": "ok",
                "path": self.l2_5.get_path(),
                "stats": self.l2_5.get_stats()
            },
            "l3": {
                "status": "ok" if self.l3.ping() else "error",
                "stats": self.l3.get_stats(),
                "pinecone": self.l3.is_pinecone_enabled()
            }
        }

    def close(self):
        """关闭所有连接"""
        self.l1.redis.close()
        self.l2.close()
        logger.info("Memory System closed")
