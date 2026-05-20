# -*- coding: utf-8 -*-
"""
pi-code-runner Extensions

提供两个主要扩展:
1. MemoryManager - 记忆管理器
2. Agent - 智能体
"""

__version__ = "1.0.0"

from .memory_manager import MemoryManagerExtension, MemoryContext, Message
from .agent import AgentExtension, AgentResponse, AgentState, Tool, Step, ToolCall

__all__ = [
    # 版本
    "__version__",
    
    # MemoryManager
    "MemoryManagerExtension",
    "MemoryContext",
    "Message",
    
    # Agent
    "AgentExtension",
    "AgentResponse",
    "AgentState",
    "Tool",
    "Step",
    "ToolCall",
]
