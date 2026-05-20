# -*- coding: utf-8 -*-
"""
L1 Working Memory - Redis + ContextCompressor
会话级工作记忆
"""

import json
import logging
from typing import Any, Optional, List, Dict, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field

import redis

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """对话消息"""
    role: str  # user, assistant, system
    content: str
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class CompressionResult:
    """压缩结果"""
    original_count: int
    compressed_count: int
    summary: str
    preserved_messages: List[Message]


class L1WorkingMemory:
    """
    L1 工作记忆 - Redis
    - 会话消息历史
    - ContextCompressor 压缩
    - TTL=1小时，访问自动延长
    """

    DEFAULT_TTL = 3600
    MAX_MESSAGES = 100  # 超过此数量触发压缩
    COMPRESSION_THRESHOLD = 50  # 压缩保留的消息数

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ttl: int = DEFAULT_TTL,
        key_prefix: str = "pimem:l1:",
        compressor_fn: Optional[Callable[[List[Message]], str]] = None
    ):
        """
        Args:
            compressor_fn: 自定义压缩函数，接收消息列表，返回摘要字符串
        """
        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )
        self.ttl = ttl
        self.key_prefix = key_prefix
        self.compressor_fn = compressor_fn
        logger.info(f"L1 Working Memory initialized: {host}:{port}, TTL={ttl}s")

    def _make_key(self, session_id: str, key: str = "messages") -> str:
        return f"{self.key_prefix}{session_id}:{key}"

    # ============================================================
    # 会话管理
    # ============================================================

    def create_session(self, session_id: str, metadata: Optional[Dict] = None) -> bool:
        """创建新会话"""
        try:
            meta_key = self._make_key(session_id, "meta")
            data = {
                "created_at": datetime.now().isoformat(),
                "message_count": 0,
                "compressed": False,
                **(metadata or {})
            }
            self.redis.setex(meta_key, self.ttl, json.dumps(data, ensure_ascii=False))
            return True
        except Exception as e:
            logger.error(f"L1 create_session error: {e}")
            return False

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        try:
            meta_key = self._make_key(session_id, "meta")
            data = self.redis.get(meta_key)
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            keys = self.redis.keys(f"{self.key_prefix}{session_id}:*")
            if keys:
                self.redis.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"L1 delete_session error: {e}")
            return False

    # ============================================================
    # 消息操作
    # ============================================================

    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """添加消息"""
        try:
            msg_key = self._make_key(session_id, "messages")
            
            msg = Message(role=role, content=content, metadata=metadata or {})
            msg_data = json.dumps({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "metadata": msg.metadata
            }, ensure_ascii=False)
            
            self.redis.rpush(msg_key, msg_data)
            self.redis.expire(msg_key, self.ttl)
            
            # 更新计数
            self._update_session_count(session_id)
            
            # 检查是否需要压缩
            self._check_compression(session_id)
            
            return True
        except Exception as e:
            logger.error(f"L1 add_message error: {e}")
            return False

    def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Message]:
        """获取消息列表"""
        try:
            msg_key = self._make_key(session_id, "messages")
            raw_list = self.redis.lrange(msg_key, 0, -1)
            
            messages = []
            for raw in raw_list:
                data = json.loads(raw)
                messages.append(Message(
                    role=data["role"],
                    content=data["content"],
                    timestamp=data.get("timestamp", ""),
                    metadata=data.get("metadata", {})
                ))
            
            # 延长 TTL
            self.redis.expire(msg_key, self.ttl)
            meta_key = self._make_key(session_id, "meta")
            self.redis.expire(meta_key, self.ttl)
            
            if limit:
                return messages[-limit:]
            return messages
        except Exception as e:
            logger.error(f"L1 get_messages error: {e}")
            return []

    def get_messages_count(self, session_id: str) -> int:
        """获取消息数量"""
        try:
            msg_key = self._make_key(session_id, "messages")
            return self.redis.llen(msg_key)
        except Exception:
            return 0

    def clear_messages(self, session_id: str) -> bool:
        """清空消息"""
        try:
            msg_key = self._make_key(session_id, "messages")
            self.redis.delete(msg_key)
            self._update_session_count(session_id, 0)
            return True
        except Exception as e:
            logger.error(f"L1 clear_messages error: {e}")
            return False

    def _update_session_count(self, session_id: str, count: Optional[int] = None):
        """更新会话消息计数"""
        try:
            if count is None:
                count = self.get_messages_count(session_id)
            
            meta_key = self._make_key(session_id, "meta")
            meta = self.get_session_info(session_id)
            if meta:
                meta["message_count"] = count
                self.redis.setex(meta_key, self.ttl, json.dumps(meta, ensure_ascii=False))
        except Exception:
            pass

    def _check_compression(self, session_id: str):
        """检查是否需要压缩"""
        count = self.get_messages_count(session_id)
        if count > self.MAX_MESSAGES:
            self.compress(session_id)

    # ============================================================
    # ContextCompressor - 消息压缩
    # ============================================================

    def compress(self, session_id: str, preserve_count: int = None) -> Optional[CompressionResult]:
        """
        压缩消息历史
        
        Args:
            session_id: 会话ID
            preserve_count: 保留最近的N条消息
            
        Returns:
            CompressionResult 压缩结果
        """
        try:
            if preserve_count is None:
                preserve_count = self.COMPRESSION_THRESHOLD
            
            messages = self.get_messages(session_id)
            if len(messages) <= preserve_count:
                return None
            
            original_count = len(messages)
            
            # 保留最近的 N 条
            preserved = messages[-preserve_count:]
            to_summarize = messages[:-preserve_count]
            
            # 生成摘要
            summary = self._generate_summary(to_summarize)
            
            # 压缩: 只保留最近的 + 摘要
            msg_key = self._make_key(session_id, "messages")
            
            # 清空并重新写入
            self.redis.delete(msg_key)
            
            # 写入摘要作为第一条
            summary_msg = Message(
                role="system",
                content=f"[历史摘要] {summary}",
                metadata={"type": "summary", "original_count": original_count}
            )
            self.redis.rpush(msg_key, json.dumps({
                "role": summary_msg.role,
                "content": summary_msg.content,
                "timestamp": summary_msg.timestamp,
                "metadata": summary_msg.metadata
            }, ensure_ascii=False))
            
            # 写入保留的消息
            for msg in preserved:
                self.redis.rpush(msg_key, json.dumps({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata
                }, ensure_ascii=False))
            
            self.redis.expire(msg_key, self.ttl)
            
            # 更新元数据
            meta_key = self._make_key(session_id, "meta")
            meta = self.get_session_info(session_id) or {}
            meta["compressed"] = True
            meta["compression_count"] = meta.get("compression_count", 0) + 1
            meta["message_count"] = preserve_count + 1  # +1 摘要
            self.redis.setex(meta_key, self.ttl, json.dumps(meta, ensure_ascii=False))
            
            logger.info(f"L1 compressed session {session_id}: {original_count} -> {preserve_count + 1}")
            
            return CompressionResult(
                original_count=original_count,
                compressed_count=preserve_count + 1,
                summary=summary,
                preserved_messages=preserved
            )
        except Exception as e:
            logger.error(f"L1 compress error: {e}")
            return None

    def _generate_summary(self, messages: List[Message]) -> str:
        """生成摘要"""
        if self.compressor_fn:
            return self.compressor_fn(messages)
        
        # 默认摘要: 取前几条的关键信息
        user_msgs = [m for m in messages if m.role == "user"]
        if user_msgs:
            first_topic = user_msgs[0].content[:50]
            total = len(messages)
            return f"会话共{total}条消息，主题: {first_topic}..."
        
        return f"历史会话，共{len(messages)}条消息"

    # ============================================================
    # 工具方法
    # ============================================================

    def list_sessions(self, limit: int = 100) -> List[str]:
        """列出所有会话"""
        try:
            keys = self.redis.keys(f"{self.key_prefix}*:meta")
            sessions = []
            for key in keys[:limit]:
                # 提取 session_id
                parts = key.replace(self.key_prefix, "").split(":")
                if parts:
                    sessions.append(parts[0])
            return list(set(sessions))
        except Exception as e:
            logger.error(f"L1 list_sessions error: {e}")
            return []

    def ping(self) -> bool:
        """检查连接"""
        try:
            return self.redis.ping()
        except Exception:
            return False

    def info(self) -> Dict[str, Any]:
        """获取状态信息"""
        try:
            info = self.redis.info("memory")
            return {
                "status": "connected" if self.ping() else "disconnected",
                "sessions": len(self.list_sessions()),
                "used_memory": info.get("used_memory_human", "unknown"),
                "ttl_default": self.ttl
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
