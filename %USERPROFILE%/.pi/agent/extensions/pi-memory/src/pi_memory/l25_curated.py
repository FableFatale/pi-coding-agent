# -*- coding: utf-8 -*-
"""
L2.5 Curated Memory - 文件系统
用户/Agent 共同编辑的策划记忆
"""

import os
import re
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CuratedEntry:
    """策划记忆条目"""
    id: str = ""
    content: str = ""
    author: str = ""  # user, agent, system
    tags: List[str] = field(default_factory=list)
    importance: float = 1.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    line_start: int = 0  # 在文件中的行号
    line_end: int = 0


class L25CuratedMemory:
    """
    L2.5 策划记忆 - 文件系统
    
    特点:
    - 用户/Agent 共同编辑
    - 角色分明 (user: / agent: 前缀)
    - 写入立即持久化
    - 字符限额防溢出
    """

    MAX_CONTENT_SIZE = 10000  # 单个内容最大字符数
    MAX_FILE_SIZE = 50000    # 文件最大字符数
    
    # 作者角色
    AUTHOR_USER = "user"
    AUTHOR_AGENT = "agent"
    AUTHOR_SYSTEM = "system"

    def __init__(
        self,
        base_dir: Optional[str] = None,
        memory_file: str = "MEMORY.md",
        user_file: str = "USER.md"
    ):
        """
        Args:
            base_dir: 基础目录，默认 ~/.pi-memory/
            memory_file: 共享记忆文件名
            user_file: 用户信息文件名
        """
        if base_dir is None:
            base_dir = os.path.expanduser("~/.pi-memory")
        
        self.base_dir = Path(base_dir)
        self.memory_file = self.base_dir / memory_file
        self.user_file = self.base_dir / user_file
        
        # 确保目录存在
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化文件
        self._init_files()
        
        logger.info(f"L2.5 Curated Memory initialized: {self.base_dir}")

    def _init_files(self):
        """初始化记忆文件"""
        # MEMORY.md - 共享记忆
        if not self.memory_file.exists():
            self.memory_file.write_text(
                "# 共享记忆\n\n"
                "> 此文件由 Agent 和用户共同维护\n\n"
                "## 重要规则\n\n"
                "- 角色: `user:` 表示用户编辑, `agent:` 表示 Agent 编辑\n"
                "- 格式: 每个条目用 `---` 分隔\n"
                "- 标签: 在末尾用 `#tag` 标记\n\n"
                "---\n\n",
                encoding="utf-8"
            )
            logger.info(f"Created: {self.memory_file}")
        
        # USER.md - 用户信息
        if not self.user_file.exists():
            self.user_file.write_text(
                "# 用户信息\n\n"
                "> 由用户维护的个人信息\n\n"
                "## 基本信息\n\n"
                "姓名: \n"
                "偏好: \n"
                "时区: \n\n"
                "---\n\n",
                encoding="utf-8"
            )
            logger.info(f"Created: {self.user_file}")

    # ============================================================
    # 读取
    # ============================================================

    def read_all(self) -> Dict[str, Any]:
        """读取所有策划记忆"""
        return {
            "memory": self.read_memory(),
            "user": self.read_user(),
            "stats": self.get_stats()
        }

    def read_memory(self) -> str:
        """读取共享记忆"""
        try:
            if self.memory_file.exists():
                return self.memory_file.read_text(encoding="utf-8")
            return ""
        except Exception as e:
            logger.error(f"L2.5 read_memory error: {e}")
            return ""

    def read_user(self) -> str:
        """读取用户信息"""
        try:
            if self.user_file.exists():
                return self.user_file.read_text(encoding="utf-8")
            return ""
        except Exception as e:
            logger.error(f"L2.5 read_user error: {e}")
            return ""

    def read_entries(self) -> List[CuratedEntry]:
        """解析所有条目"""
        content = self.read_memory()
        return self._parse_entries(content)

    def _parse_entries(self, content: str) -> List[CuratedEntry]:
        """解析条目"""
        entries = []
        lines = content.split("\n")
        
        current_entry = None
        current_lines = []
        line_num = 0
        
        for i, line in enumerate(lines, 1):
            if line.strip() == "---":
                if current_entry is not None:
                    # 保存上一个条目
                    current_entry.content = "\n".join(current_lines).strip()
                    current_entry.line_end = i - 1
                    entries.append(current_entry)
                
                # 开始新条目
                current_entry = CuratedEntry(line_start=i)
                current_lines = []
            else:
                if current_entry is not None:
                    current_lines.append(line)
                    
                    # 解析元数据
                    if line.startswith("user:") or line.startswith("agent:") or line.startswith("system:"):
                        parts = line.split(":", 1)
                        current_entry.author = parts[0]
                        current_entry.content = parts[1].strip()
                    
                    # 解析标签
                    tags = re.findall(r'#(\w+)', line)
                    current_entry.tags.extend(tags)
        
        # 保存最后一个条目
        if current_entry is not None:
            current_entry.content = "\n".join(current_lines).strip()
            current_entry.line_end = len(lines)
            entries.append(current_entry)
        
        return entries

    def get_entries_by_author(self, author: str) -> List[CuratedEntry]:
        """按作者筛选条目"""
        all_entries = self.read_entries()
        return [e for e in all_entries if e.author == author]

    def get_entries_by_tag(self, tag: str) -> List[CuratedEntry]:
        """按标签筛选条目"""
        all_entries = self.read_entries()
        return [e for e in all_entries if tag in e.tags]

    def search(self, keyword: str) -> List[CuratedEntry]:
        """关键词搜索"""
        all_entries = self.read_entries()
        return [
            e for e in all_entries
            if keyword.lower() in e.content.lower()
        ]

    # ============================================================
    # 写入
    # ============================================================

    def add_entry(
        self,
        content: str,
        author: str = "agent",
        tags: Optional[List[str]] = None,
        importance: float = 1.0
    ) -> bool:
        """
        添加记忆条目
        
        Args:
            content: 内容
            author: 作者 (user/agent/system)
            tags: 标签
            importance: 重要性
            
        Returns:
            是否成功
        """
        try:
            # 截断过长内容
            if len(content) > self.MAX_CONTENT_SIZE:
                content = content[:self.MAX_CONTENT_SIZE] + "\n\n[内容已截断]"
            
            # 格式化标签
            tag_str = ""
            if tags:
                tag_str = " " + " ".join([f"#{t}" for t in tags])
            
            # 构建条目
            entry = f"""---

{author}: {content}{tag_str}
"""
            
            # 检查文件大小
            current_size = len(self.read_memory())
            if current_size + len(entry) > self.MAX_FILE_SIZE:
                logger.warning("L2.5 file size limit reached, compressing...")
                self._compress()
            
            # 追加写入
            with open(self.memory_file, "a", encoding="utf-8") as f:
                f.write(entry)
            
            logger.debug(f"L2.5 add_entry: {author}")
            return True
        except Exception as e:
            logger.error(f"L2.5 add_entry error: {e}")
            return False

    def add_user_info(self, key: str, value: str) -> bool:
        """添加用户信息"""
        try:
            content = self.read_user()
            
            # 简单替换: 查找 "key: xxx" 并替换
            pattern = rf"({re.escape(key)}: ).*$"
            replacement = rf"\1{value}"
            
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            
            # 如果没找到，追加
            if new_content == content:
                new_content += f"\n{key}: {value}\n"
            
            self.user_file.write_text(new_content, encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"L2.5 add_user_info error: {e}")
            return False

    def update_entry(
        self,
        entry_id: str,
        content: str,
        tags: Optional[List[str]] = None
    ) -> bool:
        """更新条目 (通过内容匹配)"""
        try:
            entries = self.read_entries()
            
            # 找到并更新
            for i, entry in enumerate(entries):
                if str(entry.line_start) == entry_id or entry_id in entry.content:
                    # 更新内容
                    tag_str = ""
                    if tags:
                        tag_str = " " + " ".join([f"#{t}" for t in tags])
                    
                    entry.content = content
                    if tags:
                        entry.tags = tags
                    
                    # 重写文件
                    self._rewrite_entries(entries)
                    return True
            
            return False
        except Exception as e:
            logger.error(f"L2.5 update_entry error: {e}")
            return False

    def _rewrite_entries(self, entries: List[CuratedEntry]):
        """重写所有条目"""
        lines = ["# 共享记忆\n"]
        lines.append("> 此文件由 Agent 和用户共同维护\n")
        lines.append("## 重要规则\n")
        lines.append("- 角色: `user:` 表示用户编辑, `agent:` 表示 Agent 编辑\n")
        lines.append("- 格式: 每个条目用 `---` 分隔\n")
        lines.append("- 标签: 在末尾用 `#tag` 标记\n")
        
        for entry in entries:
            if entry.content:
                tag_str = ""
                if entry.tags:
                    tag_str = " " + " ".join([f"#{t}" for t in entry.tags])
                
                lines.append("\n---\n")
                lines.append(f"\n{entry.author}: {entry.content}{tag_str}\n")
        
        content = "\n".join(lines)
        
        # 检查大小
        if len(content) > self.MAX_FILE_SIZE:
            self._compress()
        else:
            self.memory_file.write_text(content, encoding="utf-8")

    def _compress(self):
        """压缩: 保留最新的 N 条"""
        entries = self.read_entries()
        if len(entries) <= 5:
            return
        
        # 保留最新的 10 条
        preserved = entries[-10:]
        self._rewrite_entries(preserved)
        
        # 添加压缩说明
        with open(self.memory_file, "a", encoding="utf-8") as f:
            f.write("\n\n> [系统] 记忆已自动压缩，保留最近10条\n")
        
        logger.info("L2.5 compressed entries")

    # ============================================================
    # 删除
    # ============================================================

    def delete_entry(self, entry_id: str) -> bool:
        """删除条目"""
        try:
            entries = self.read_entries()
            new_entries = [e for e in entries if str(e.line_start) != entry_id]
            
            if len(new_entries) == len(entries):
                return False
            
            self._rewrite_entries(new_entries)
            return True
        except Exception as e:
            logger.error(f"L2.5 delete_entry error: {e}")
            return False

    def clear_all(self, confirm: bool = False) -> bool:
        """清空所有记忆"""
        if not confirm:
            return False
        
        try:
            self._init_files()
            return True
        except Exception as e:
            logger.error(f"L2.5 clear_all error: {e}")
            return False

    # ============================================================
    # 工具
    # ============================================================

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            memory_content = self.read_memory()
            user_content = self.read_user()
            entries = self.read_entries()
            
            return {
                "memory_file": str(self.memory_file),
                "memory_size": len(memory_content),
                "memory_entries": len([e for e in entries if e.author == "agent"]),
                "user_file": str(self.user_file),
                "user_size": len(user_content),
                "user_entries": len([e for e in entries if e.author == "user"]),
                "total_entries": len(entries)
            }
        except Exception as e:
            logger.error(f"L2.5 get_stats error: {e}")
            return {}

    def export_json(self) -> str:
        """导出为 JSON"""
        import json
        return json.dumps({
            "memory": self.read_memory(),
            "user": self.read_user(),
            "stats": self.get_stats()
        }, ensure_ascii=False, indent=2)

    def import_from_json(self, json_str: str) -> bool:
        """从 JSON 导入"""
        import json
        try:
            data = json.loads(json_str)
            
            if "memory" in data:
                self.memory_file.write_text(data["memory"], encoding="utf-8")
            
            if "user" in data:
                self.user_file.write_text(data["user"], encoding="utf-8")
            
            return True
        except Exception as e:
            logger.error(f"L2.5 import error: {e}")
            return False

    def get_path(self) -> str:
        """获取记忆目录路径"""
        return str(self.base_dir)
