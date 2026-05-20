# -*- coding: utf-8 -*-
"""
MemoryManager - 记忆管理器
实现记忆流向完整流程
"""

import logging
from typing import Any, Optional, List, Dict, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from .memory_system import MemorySystem
from .l1_working import Message
from .l2_episodic import Session
from .l25_curated import CuratedEntry
from .l3_semantic import Skill

logger = logging.getLogger(__name__)


@dataclass
class MemoryContext:
    """记忆上下文 (注入到 System Prompt)"""
    # 当前会话
    current_session: Optional[Dict] = None
    
    # 相关历史会话摘要
    relevant_sessions: List[Dict] = field(default_factory=list)
    
    # 共享记忆
    curated_memory: List[str] = field(default_factory=list)
    
    # 用户信息
    user_info: Dict[str, str] = field(default_factory=dict)
    
    # 相关技能
    relevant_skills: List[Dict] = field(default_factory=list)
    
    # 系统提示
    system_reminder: str = ""
    
    def to_prompt(self) -> str:
        """转换为 Prompt 格式"""
        lines = []
        
        if self.current_session:
            lines.append("## 当前会话")
            lines.append(f"- 会话ID: {self.current_session.get('id', 'N/A')}")
            lines.append(f"- 消息数: {self.current_session.get('message_count', 0)}")
            lines.append("")
        
        if self.relevant_sessions:
            lines.append("## 相关历史会话")
            for i, s in enumerate(self.relevant_sessions[:3], 1):
                lines.append(f"{i}. [{s.get('title', 'N/A')}] {s.get('summary', '')[:100]}")
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
                lines.append(f"- {s.get('name', 'N/A')}: {s.get('description', '')[:50]}")
            lines.append("")
        
        if self.system_reminder:
            lines.append(f"## 系统提醒")
            lines.append(self.system_reminder)
        
        return "\n".join(lines)


@dataclass 
class SyncResult:
    """同步结果"""
    l1_synced: bool = False
    l2_synced: bool = False
    l2_5_synced: bool = False
    l3_synced: bool = False
    errors: List[str] = field(default_factory=list)


class MemoryManager:
    """
    记忆管理器
    
    实现记忆流向:
    1. prefetch_all(query) - 预取相关记忆
    2. 各Provider并行查询
    3. 组装memory-context注入System Prompt
    4. LLM API Call
    5. Tool Execution
    6. sync_all() - 同步每轮对话到各Provider
    """

    def __init__(
        self,
        memory_system: Optional[MemorySystem] = None,
        max_workers: int = 4,
        max_context_length: int = 4000
    ):
        """
        Args:
            memory_system: 记忆系统实例
            max_workers: 并行查询线程数
            max_context_length: 最大上下文长度 (字符)
        """
        self.memory = memory_system or MemorySystem()
        self.max_workers = max_workers
        self.max_context_length = max_context_length
        
        logger.info("MemoryManager initialized")

    # ============================================================
    # 步骤1: 预取相关记忆 (并行查询)
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
        预取所有相关记忆 (并行查询)
        
        Args:
            query: 当前查询/任务
            session_id: 当前会话ID
            max_sessions: 最大相关会话数
            max_memory: 最大记忆条数
            max_skills: 最大技能数
            
        Returns:
            MemoryContext - 组装好的记忆上下文
        """
        context = MemoryContext()
        
        # 并行查询
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            # L1: 当前会话
            if session_id:
                future = executor.submit(self._fetch_current_session, session_id)
                futures["current_session"] = future
            
            # L2: 相关历史会话
            future = executor.submit(
                self._fetch_relevant_sessions, 
                query, 
                max_sessions
            )
            futures["relevant_sessions"] = future
            
            # L2.5: 共享记忆
            future = executor.submit(self._fetch_curated_memory, query, max_memory)
            futures["curated_memory"] = future
            
            # L2.5: 用户信息
            future = executor.submit(self._fetch_user_info)
            futures["user_info"] = future
            
            # L3: 相关技能
            future = executor.submit(self._fetch_relevant_skills, query, max_skills)
            futures["relevant_skills"] = future
            
            # 收集结果
            for key, future in futures.items():
                try:
                    result = future.result(timeout=5)
                    if key == "current_session":
                        context.current_session = result
                    elif key == "relevant_sessions":
                        context.relevant_sessions = result
                    elif key == "curated_memory":
                        context.curated_memory = result
                    elif key == "user_info":
                        context.user_info = result
                    elif key == "relevant_skills":
                        context.relevant_skills = result
                except Exception as e:
                    logger.warning(f"prefetch {key} failed: {e}")
        
        # 生成系统提醒
        context.system_reminder = self._generate_reminder(context)
        
        # 截断过长的上下文
        context = self._truncate_context(context)
        
        return context

    def _fetch_current_session(self, session_id: str) -> Optional[Dict]:
        """获取当前会话信息"""
        messages = self.memory.session_get_messages(session_id)
        if not messages:
            return None
        
        return {
            "id": session_id,
            "message_count": len(messages),
            "preview": messages[0].content[:100] if messages else ""
        }

    def _fetch_relevant_sessions(self, query: str, max_count: int) -> List[Dict]:
        """获取相关历史会话"""
        results = self.memory.search_sessions(query, limit=max_count)
        return [
            {
                "id": s.session_id,
                "title": s.title,
                "summary": s.summary,
                "tags": s.tags,
                "created_at": str(s.created_at) if s.created_at else ""
            }
            for s, _ in results
        ]

    def _fetch_curated_memory(self, query: str, max_count: int) -> List[str]:
        """获取共享记忆"""
        entries = self.memory.memory_search(query)
        return [e.content for e in entries[:max_count]]

    def _fetch_user_info(self) -> Dict[str, str]:
        """获取用户信息"""
        user_content = self.memory.user_read()
        
        # 简单解析 key: value 格式
        info = {}
        for line in user_content.split("\n"):
            if ":" in line and not line.startswith("#"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    if key and value:
                        info[key] = value
        
        return info

    def _fetch_relevant_skills(self, query: str, max_count: int) -> List[Dict]:
        """获取相关技能"""
        skills = self.memory.skill_search(query, limit=max_count)
        return [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "category": s.category,
                "level": s.level
            }
            for s in skills
        ]

    def _generate_reminder(self, context: MemoryContext) -> str:
        """生成系统提醒"""
        reminders = []
        
        if context.relevant_sessions:
            reminders.append(f"注意：之前有 {len(context.relevant_sessions)} 个相关会话已提供参考")
        
        if context.user_info and "name" in context.user_info:
            reminders.append(f"用户名为 {context.user_info['name']}")
        
        if context.relevant_skills:
            skill_names = [s["name"] for s in context.relevant_skills[:3]]
            reminders.append(f"可参考技能: {', '.join(skill_names)}")
        
        return " | ".join(reminders) if reminders else ""

    def _truncate_context(self, context: MemoryContext) -> MemoryContext:
        """截断过长的上下文"""
        prompt = context.to_prompt()
        
        if len(prompt) <= self.max_context_length:
            return context
        
        # 按优先级截断
        # 1. 先截断技能
        while len(context.relevant_skills) > 1:
            context.relevant_skills.pop()
            if len(context.to_prompt()) <= self.max_context_length:
                break
        
        # 2. 截断记忆
        while len(context.curated_memory) > 1:
            context.curated_memory.pop()
            if len(context.to_prompt()) <= self.max_context_length:
                break
        
        # 3. 截断会话
        while len(context.relevant_sessions) > 1:
            context.relevant_sessions.pop()
            if len(context.to_prompt()) <= self.max_context_length:
                break
        
        context.system_reminder = "[上下文已截断]"
        return context

    # ============================================================
    # 步骤3: 生成 System Prompt
    # ============================================================

    def build_system_prompt(
        self,
        base_prompt: str,
        query: str,
        session_id: Optional[str] = None
    ) -> str:
        """
        构建完整的 System Prompt
        
        Args:
            base_prompt: 基础提示词
            query: 当前查询
            session_id: 会话ID
            
        Returns:
            完整的 System Prompt
        """
        # 预取记忆
        context = self.prefetch_all(query, session_id)
        
        # 组装
        memory_section = f"""
---
## 记忆上下文

{context.to_prompt()}
---
"""
        
        return base_prompt + memory_section

    # ============================================================
    # 步骤6: 同步对话到各Provider
    # ============================================================

    def sync_all(
        self,
        session_id: str,
        messages: Optional[List[Dict]] = None,
        tags: Optional[List[str]] = None,
        auto_archive: bool = True
    ) -> SyncResult:
        """
        同步对话到各记忆层
        
        Args:
            session_id: 会话ID
            messages: 消息列表 (为空则从L1获取)
            tags: 标签
            auto_archive: 是否自动归档到L2
            
        Returns:
            SyncResult - 同步结果
        """
        result = SyncResult()
        
        # 获取消息
        if messages is None:
            l1_messages = self.memory.session_get_messages(session_id)
            messages = [
                {"role": m.role, "content": m.content}
                for m in l1_messages
            ]
        
        # L1 同步 (已经是数据源，跳过)
        result.l1_synced = True
        
        # L2 同步 (历史会话)
        if auto_archive and len(messages) >= 2:
            try:
                session_db_id = self.memory.save_session(
                    session_id,
                    messages,
                    tags=tags
                )
                result.l2_synced = session_db_id is not None
            except Exception as e:
                result.errors.append(f"L2 sync error: {e}")
        
        # L2.5 同步 (提取重要信息到共享记忆)
        if messages:
            try:
                self._sync_to_curated(messages)
                result.l2_5_synced = True
            except Exception as e:
                result.errors.append(f"L2.5 sync error: {e}")
        
        # L3 同步 (提取技能相关到语义记忆)
        if messages:
            try:
                self._sync_to_semantic(messages)
                result.l3_synced = True
            except Exception as e:
                result.errors.append(f"L3 sync error: {e}")
        
        return result

    def _sync_to_curated(self, messages: List[Dict]):
        """提取信息同步到 L2.5"""
        # 分析用户信息
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                
                # 检测用户名
                if "我叫" in content or "我是" in content:
                    # 简单提取
                    pass
                
                # 检测偏好
                if "喜欢" in content or "偏好" in content:
                    self.memory.memory_add(
                        content,
                        author="user",
                        tags=["偏好"]
                    )

    def _sync_to_semantic(self, messages: List[Dict]):
        """提取技能相关同步到 L3"""
        # 检测是否提到技能
        skill_keywords = ["Python", "JavaScript", "React", "API", "数据库"]
        
        for msg in messages:
            content = msg.get("content", "")
            
            for keyword in skill_keywords:
                if keyword.lower() in content.lower():
                    # 可以在这里添加技能学习的触发逻辑
                    pass

    # ============================================================
    # 工具方法
    # ============================================================

    def archive_session(
        self,
        session_id: str,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        归档会话到历史
        
        Args:
            session_id: 会话ID
            tags: 标签
            
        Returns:
            是否成功
        """
        messages = self.memory.session_get_messages(session_id)
        if not messages:
            return False
        
        msg_dicts = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        
        return self.memory.save_session(session_id, msg_dicts, tags=tags) is not None

    def clear_session(
        self,
        session_id: str,
        archive: bool = True
    ) -> bool:
        """
        清理会话
        
        Args:
            session_id: 会话ID
            archive: 是否先归档
            
        Returns:
            是否成功
        """
        if archive:
            self.archive_session(session_id)
        
        return self.memory.session_delete(session_id)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.memory.health_check()
