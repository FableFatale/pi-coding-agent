# -*- coding: utf-8 -*-
"""
MemoryManager Extension for pi-code-runner

提供三层记忆系统集成：
L1: Working Memory (Redis)
L2: Episodic Memory (PostgreSQL)
L3: Semantic Memory (skills/)
"""

import json
import logging
from typing import Any, Optional, List, Dict, Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """对话消息"""
    role: str
    content: str
    timestamp: str = ""
    
    def to_dict(self) -> Dict:
        return {"role": self.role, "content": self.content}


@dataclass
class MemoryContext:
    """记忆上下文"""
    current_session: Optional[Dict] = None
    relevant_sessions: List[Dict] = field(default_factory=list)
    curated_memory: List[str] = field(default_factory=list)
    user_info: Dict[str, str] = field(default_factory=dict)
    relevant_skills: List[Dict] = field(default_factory=list)
    system_reminder: str = ""
    
    def to_prompt(self) -> str:
        lines = []
        if self.current_session:
            lines.append("## 当前会话")
            lines.append(f"- ID: {self.current_session.get('id', 'N/A')}")
            lines.append(f"- 消息数: {self.current_session.get('count', 0)}")
            lines.append("")
        if self.relevant_sessions:
            lines.append("## 相关历史会话")
            for s in self.relevant_sessions[:3]:
                lines.append(f"- {s.get('title', 'N/A')}: {s.get('summary', '')[:80]}")
            lines.append("")
        if self.curated_memory:
            lines.append("## 共享记忆")
            for m in self.curated_memory[:5]:
                lines.append(f"- {m}")
            lines.append("")
        if self.user_info:
            lines.append("## 用户信息")
            for k, v in self.user_info.items():
                lines.append(f"- {k}: {v}")
            lines.append("")
        if self.relevant_skills:
            lines.append("## 相关技能")
            for s in self.relevant_skills[:5]:
                lines.append(f"- {s.get('name')}: {s.get('description', '')[:50]}")
            lines.append("")
        if self.system_reminder:
            lines.append(f"## 系统提醒\n{self.system_reminder}")
        return "\n".join(lines)


class MemoryManagerExtension:
    """
    MemoryManager 扩展
    
    功能:
    - L1: 会话消息存储 (Redis)
    - L2: 历史会话 (PostgreSQL)
    - L3: 技能知识 (文件)
    - prefetch_all(): 并行预取
    - build_context(): 构建上下文
    - sync(): 同步记忆
    """
    
    name = "memory_manager"
    version = "1.0.0"
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        pg_host: str = "localhost",
        pg_port: int = 5432,
        pg_database: str = "pimemory",
        pg_user: str = "postgres",
        pg_password: str = "",
        skills_dir: Optional[str] = None,
        memory_dir: Optional[str] = None
    ):
        self.redis_config = {
            "host": redis_host,
            "port": redis_port,
            "db": redis_db
        }
        self.pg_config = {
            "host": pg_host,
            "port": pg_port,
            "database": pg_database,
            "user": pg_user,
            "password": pg_password
        }
        self.skills_dir = skills_dir
        self.memory_dir = memory_dir or ".pi-memory"
        
        self._redis = None
        self._pg = None
        
        logger.info(f"MemoryManagerExtension initialized")
    
    # ============================================================
    # L1: Working Memory (Redis)
    # ============================================================
    
    def _get_redis(self):
        """获取 Redis 连接"""
        if self._redis is None:
            import redis
            self._redis = redis.Redis(**self.redis_config, decode_responses=True)
        return self._redis
    
    def session_create(self, session_id: str, metadata: Optional[Dict] = None) -> bool:
        """创建会话"""
        try:
            r = self._get_redis()
            key = f"session:{session_id}:meta"
            data = {
                "created": True,
                "metadata": json.dumps(metadata or {}),
                "count": 0
            }
            r.hset(key, mapping=data)
            r.expire(key, 3600)
            return True
        except Exception as e:
            logger.error(f"session_create error: {e}")
            return False
    
    def session_add_message(self, session_id: str, role: str, content: str) -> bool:
        """添加消息"""
        try:
            r = self._get_redis()
            msg_key = f"session:{session_id}:messages"
            msg = json.dumps({"role": role, "content": content}, ensure_ascii=False)
            r.rpush(msg_key, msg)
            r.expire(msg_key, 3600)
            # 更新计数
            r.hincrby(f"session:{session_id}:meta", "count", 1)
            return True
        except Exception as e:
            logger.error(f"session_add_message error: {e}")
            return False
    
    def session_get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Message]:
        """获取消息"""
        try:
            r = self._get_redis()
            msg_key = f"session:{session_id}:messages"
            raw_list = r.lrange(msg_key, 0, -1)
            messages = [Message(**json.loads(raw)) for raw in raw_list]
            return messages[-limit:] if limit else messages
        except Exception as e:
            logger.error(f"session_get_messages error: {e}")
            return []
    
    def session_delete(self, session_id: str) -> bool:
        """删除会话"""
        try:
            r = self._get_redis()
            keys = r.keys(f"session:{session_id}:*")
            if keys:
                r.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"session_delete error: {e}")
            return False
    
    # ============================================================
    # L2: Episodic Memory (PostgreSQL)
    # ============================================================
    
    def _get_pg(self):
        """获取 PostgreSQL 连接"""
        if self._pg is None:
            import psycopg2
            self._pg = psycopg2.connect(**self.pg_config)
        return self._pg
    
    def _init_pg(self):
        """初始化数据库"""
        try:
            conn = self._get_pg()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS episodic_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) UNIQUE,
                    title VARCHAR(500),
                    summary TEXT,
                    messages JSONB,
                    tags TEXT[],
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.commit()
            cur.close()
        except Exception as e:
            logger.error(f"_init_pg error: {e}")
    
    def save_session(
        self,
        session_id: str,
        messages: List[Dict],
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None
    ) -> Optional[int]:
        """保存会话到历史"""
        try:
            self._init_pg()
            conn = self._get_pg()
            cur = conn.cursor()
            
            # 生成摘要
            if not summary and messages:
                user_msgs = [m for m in messages if m.get("role") == "user"]
                if user_msgs:
                    summary = f"主题: {user_msgs[0].get('content', '')[:100]}..."
            
            if not title and messages:
                user_msgs = [m for m in messages if m.get("role") == "user"]
                if user_msgs:
                    title = user_msgs[0].get("content", "")[:50]
            
            cur.execute("""
                INSERT INTO episodic_sessions (session_id, title, summary, messages, tags)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (session_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    summary = EXCLUDED.summary,
                    messages = EXCLUDED.messages,
                    tags = EXCLUDED.tags
                RETURNING id
            """, (session_id, title, summary, json.dumps(messages), tags or []))
            
            result = cur.fetchone()
            conn.commit()
            cur.close()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"save_session error: {e}")
            return None
    
    def search_sessions(self, query: str, limit: int = 5) -> List[Dict]:
        """搜索历史会话"""
        try:
            self._init_pg()
            conn = self._get_pg()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT session_id, title, summary, tags
                FROM episodic_sessions
                WHERE title ILIKE %s OR summary ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (f"%{query}%", f"%{query}%", limit))
            
            rows = cur.fetchall()
            cur.close()
            
            return [
                {"session_id": r[0], "title": r[1], "summary": r[2], "tags": r[3] or []}
                for r in rows
            ]
        except Exception as e:
            logger.error(f"search_sessions error: {e}")
            return []
    
    # ============================================================
    # L2.5: Curated Memory (文件)
    # ============================================================
    
    def memory_add(self, content: str, author: str = "agent") -> bool:
        """添加共享记忆"""
        try:
            import os
            os.makedirs(self.memory_dir, exist_ok=True)
            memory_file = os.path.join(self.memory_dir, "MEMORY.md")
            
            entry = f"\n---\n{author}: {content}\n"
            with open(memory_file, "a", encoding="utf-8") as f:
                f.write(entry)
            return True
        except Exception as e:
            logger.error(f"memory_add error: {e}")
            return False
    
    def memory_read(self) -> str:
        """读取共享记忆"""
        try:
            import os
            memory_file = os.path.join(self.memory_dir, "MEMORY.md")
            if os.path.exists(memory_file):
                return open(memory_file, encoding="utf-8").read()
            return ""
        except Exception as e:
            logger.error(f"memory_read error: {e}")
            return ""
    
    def memory_search(self, keyword: str) -> List[str]:
        """搜索记忆"""
        content = self.memory_read()
        results = []
        for line in content.split("\n"):
            if keyword.lower() in line.lower():
                results.append(line.strip())
        return results
    
    def user_info_set(self, key: str, value: str) -> bool:
        """设置用户信息"""
        try:
            import os
            os.makedirs(self.memory_dir, exist_ok=True)
            user_file = os.path.join(self.memory_dir, "USER.md")
            
            lines = []
            if os.path.exists(user_file):
                lines = open(user_file, encoding="utf-8").read().split("\n")
            
            # 更新或添加
            found = False
            new_lines = []
            for line in lines:
                if line.startswith(f"{key}:"):
                    new_lines.append(f"{key}: {value}")
                    found = True
                else:
                    new_lines.append(line)
            
            if not found:
                new_lines.append(f"{key}: {value}")
            
            with open(user_file, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines))
            return True
        except Exception as e:
            logger.error(f"user_info_set error: {e}")
            return False
    
    def user_info_get(self) -> Dict[str, str]:
        """获取用户信息"""
        try:
            import os
            user_file = os.path.join(self.memory_dir, "USER.md")
            info = {}
            if os.path.exists(user_file):
                for line in open(user_file, encoding="utf-8"):
                    if ":" in line and not line.startswith("#"):
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            k, v = parts[0].strip(), parts[1].strip()
                            if k:
                                info[k] = v
            return info
        except Exception as e:
            logger.error(f"user_info_get error: {e}")
            return {}
    
    # ============================================================
    # L3: Semantic Memory (文件)
    # ============================================================
    
    def skill_add(
        self,
        skill_id: str,
        name: str,
        content: str,
        description: str = "",
        category: str = "general",
        level: str = "beginner"
    ) -> bool:
        """添加技能"""
        try:
            import os
            import yaml
            os.makedirs(self.skills_dir, exist_ok=True)
            
            file_path = os.path.join(self.skills_dir, f"{skill_id}.md")
            
            frontmatter = {
                "id": skill_id,
                "name": name,
                "description": description,
                "category": category,
                "level": level
            }
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("---\n")
                f.write(yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False))
                f.write("---\n\n")
                f.write(content)
            
            return True
        except Exception as e:
            logger.error(f"skill_add error: {e}")
            return False
    
    def skill_get(self, skill_id: str) -> Optional[Dict]:
        """获取技能"""
        try:
            import os
            import yaml
            file_path = os.path.join(self.skills_dir, f"{skill_id}.md")
            
            if not os.path.exists(file_path):
                return None
            
            content = open(file_path, encoding="utf-8").read()
            
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    meta = yaml.safe_load(parts[1]) or {}
                    body = parts[2].strip()
                    return {**meta, "content": body}
            
            return {"id": skill_id, "content": content}
        except Exception as e:
            logger.error(f"skill_get error: {e}")
            return None
    
    def skill_search(self, query: str, limit: int = 5) -> List[Dict]:
        """搜索技能"""
        try:
            import os
            results = []
            query_lower = query.lower()
            
            if not os.path.exists(self.skills_dir):
                return results
            
            for file in os.listdir(self.skills_dir):
                if file.endswith(".md"):
                    skill_id = file[:-3]
                    skill = self.skill_get(skill_id)
                    if skill:
                        name = skill.get("name", "").lower()
                        desc = skill.get("description", "").lower()
                        if query_lower in name or query_lower in desc:
                            results.append({
                                "id": skill_id,
                                "name": skill.get("name"),
                                "description": skill.get("description"),
                                "category": skill.get("category"),
                                "level": skill.get("level")
                            })
                            if len(results) >= limit:
                                break
            
            return results
        except Exception as e:
            logger.error(f"skill_search error: {e}")
            return []
    
    # ============================================================
    # 预取 (并行查询)
    # ============================================================
    
    def prefetch_all(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_sessions: int = 3,
        max_memory: int = 5,
        max_skills: int = 5
    ) -> MemoryContext:
        """
        并行预取所有相关记忆
        
        Args:
            query: 当前查询
            session_id: 会话ID
            max_sessions: 最大相关会话数
            max_memory: 最大记忆条数
            max_skills: 最大技能数
            
        Returns:
            MemoryContext
        """
        context = MemoryContext()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            # L1: 当前会话
            if session_id:
                futures["current"] = executor.submit(self._prefetch_current, session_id)
            
            # L2: 相关会话
            futures["sessions"] = executor.submit(self.search_sessions, query, max_sessions)
            
            # L2.5: 记忆
            futures["memory"] = executor.submit(self.memory_search, query)
            
            # L2.5: 用户信息
            futures["user"] = executor.submit(self.user_info_get)
            
            # L3: 技能
            futures["skills"] = executor.submit(self.skill_search, query, max_skills)
            
            # 收集结果
            for key, future in futures.items():
                try:
                    result = future.result(timeout=5)
                    if key == "current":
                        context.current_session = result
                    elif key == "sessions":
                        context.relevant_sessions = result or []
                    elif key == "memory":
                        context.curated_memory = result or []
                    elif key == "user":
                        context.user_info = result or {}
                    elif key == "skills":
                        context.relevant_skills = result or []
                except Exception as e:
                    logger.warning(f"prefetch {key} failed: {e}")
        
        # 生成提醒
        if context.relevant_sessions:
            context.system_reminder = f"注意：有 {len(context.relevant_sessions)} 个相关历史会话"
        if context.user_info.get("name"):
            context.system_reminder += f" | 用户: {context.user_info['name']}"
        
        return context
    
    def _prefetch_current(self, session_id: str) -> Optional[Dict]:
        """预取当前会话"""
        messages = self.session_get_messages(session_id)
        if not messages:
            return None
        return {
            "id": session_id,
            "count": len(messages),
            "preview": messages[0].content[:50]
        }
    
    # ============================================================
    # 构建上下文
    # ============================================================
    
    def build_context(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> str:
        """构建记忆上下文"""
        context = self.prefetch_all(query, session_id)
        return context.to_prompt()
    
    def build_system_prompt(
        self,
        base_prompt: str,
        query: str,
        session_id: Optional[str] = None
    ) -> str:
        """构建完整的 System Prompt"""
        context_str = self.build_context(query, session_id)
        return f"""{base_prompt}

---
## 记忆上下文

{context_str}
---"""
    
    # ============================================================
    # 同步
    # ============================================================
    
    def sync_session(
        self,
        session_id: str,
        tags: Optional[List[str]] = None
    ) -> bool:
        """同步会话到历史"""
        messages = self.session_get_messages(session_id)
        if not messages:
            return False
        
        msg_dicts = [m.to_dict() for m in messages]
        result = self.save_session(session_id, msg_dicts, tags=tags)
        return result is not None
    
    # ============================================================
    # 工具
    # ============================================================
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = {"l1": "unknown", "l2": "unknown", "l2_5": "ok", "l3": "ok"}
        
        # L1 Redis
        try:
            r = self._get_redis()
            r.ping()
            status["l1"] = "ok"
        except Exception:
            status["l1"] = "error"
        
        # L2 PostgreSQL
        try:
            conn = self._get_pg()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            status["l2"] = "ok"
        except Exception:
            status["l2"] = "error"
        
        return status
    
    def close(self):
        """关闭连接"""
        if self._redis:
            self._redis.close()
            self._redis = None
        if self._pg:
            self._pg.close()
            self._pg = None
