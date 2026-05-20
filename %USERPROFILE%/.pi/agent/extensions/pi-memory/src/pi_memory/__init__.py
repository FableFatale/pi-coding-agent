# -*- coding: utf-8 -*-
"""
Pi Memory - 升级版三层记忆系统

L1: Working Memory (Redis) - 会话消息 + ContextCompressor
L2: Episodic Memory (PostgreSQL) - 历史会话 + LLM摘要
L2.5: Curated Memory (文件) - 共享记忆 + 用户信息
L3: Semantic Memory (skills/) - 技能知识 + Pinecone钩子

记忆流向:
1. prefetch_all(query) - 预取相关记忆
2. 并行查询各Provider
3. 组装memory-context注入System Prompt
4. LLM API Call
5. Tool Execution
6. sync_all() - 同步到各Provider
"""
__version__ = "2.0.0"

# L1
from .l1_working import L1WorkingMemory, Message, CompressionResult

# L2
from .l2_episodic import L2EpisodicMemory, Session, MemorySegment

# L2.5
from .l25_curated import L25CuratedMemory, CuratedEntry

# L3
from .l3_semantic import L3SemanticMemory, Skill, Conflict, ConflictResult

# 主系统
from .memory_system import MemorySystem

# 记忆管理器
from .memory_manager import MemoryManager, MemoryContext, SyncResult

__all__ = [
    # 版本
    "__version__",
    # 主系统
    "MemorySystem",
    # L1
    "L1WorkingMemory", "Message", "CompressionResult",
    # L2
    "L2EpisodicMemory", "Session", "MemorySegment",
    # L2.5
    "L25CuratedMemory", "CuratedEntry",
    # L3
    "L3SemanticMemory", "Skill", "Conflict", "ConflictResult",
    # 记忆管理器
    "MemoryManager", "MemoryContext", "SyncResult",
]
