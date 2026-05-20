# -*- coding: utf-8 -*-
"""
L3 Semantic Memory - 本地 skills/ + Pinecone 钩子
结构化知识存储
"""

import os
import re
import json
import logging
from typing import Any, Optional, List, Dict, Tuple, Callable
from datetime import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path
from dataclasses import dataclass

import yaml

logger = logging.getLogger(__name__)


@dataclass
class Skill:
    """技能"""
    id: str = ""
    name: str = ""
    description: str = ""
    category: str = ""
    level: str = "beginner"  # beginner, intermediate, expert
    tags: List[str] = field(default_factory=list)
    content: str = ""  # 技能内容/代码
    metadata: Dict[str, Any] = field(default_factory=dict)
    vector: Optional[List[float]] = None  # 向量 (可选)
    confidence: float = 1.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Conflict:
    """冲突"""
    skill_a: str = ""
    skill_b: str = ""
    type: str = ""  # duplicate, overlap, similar
    similarity: float = 0.0
    details: str = ""


@dataclass
class ConflictResult:
    """冲突检测结果"""
    has_conflicts: bool
    conflicts: List[Conflict]
    suggestions: List[str]


class L3SemanticMemory:
    """
    L3 语义记忆 - 本地 skills/ 目录 + Pinecone 钩子
    
    特点:
    - 结构化知识文档 (Markdown + Frontmatter)
    - Frontmatter 元数据
    - 渐进式加载
    - Pinecone 向量存储钩子 (可选)
    """

    def __init__(
        self,
        base_dir: Optional[str] = None,
        pinecone_api_key: Optional[str] = None,
        pinecone_env: str = "us-east-1",
        pinecone_index: str = "pi-skills",
        vectorizer_fn: Optional[Callable[[str], List[float]]] = None
    ):
        """
        Args:
            base_dir: skills 目录，默认 ~/.pi-memory/skills/
            pinecone_api_key: Pinecone API Key (可选)
            pinecone_env: Pinecone 环境
            pinecone_index: Pinecone 索引名
            vectorizer_fn: 自定义向量化函数，输入文本，输出向量
        """
        if base_dir is None:
            base_dir = os.path.expanduser("~/.pi-memory/skills")
        
        self.base_dir = Path(base_dir)
        self.pinecone_api_key = pinecone_api_key
        self.pinecone_index_name = pinecone_index
        self.vectorizer_fn = vectorizer_fn
        
        # Pinecone 客户端 (延迟初始化)
        self._pinecone = None
        self._pinecone_index = None
        
        # 确保目录存在
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化
        self._init_pinecone()
        
        logger.info(f"L3 Semantic Memory initialized: {self.base_dir}")

    # ============================================================
    # Pinecone 钩子 (可选)
    # ============================================================

    def _init_pinecone(self):
        """初始化 Pinecone (如果配置了)"""
        if not self.pinecone_api_key:
            logger.info("Pinecone not configured, using local storage only")
            return
        
        try:
            from pinecone import Pinecone, ServerlessSpec
            
            self._pinecone = Pinecone(api_key=self.pinecone_api_key)
            
            # 创建/获取索引
            existing = [idx.name for idx in self._pinecone.list_indexes()]
            
            if self.pinecone_index_name not in existing:
                self._pinecone.create_index(
                    name=self.pinecone_index_name,
                    dimension=768,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region=self.pinecone_env)
                )
            
            self._pinecone_index = self._pinecone.Index(self.pinecone_index_name)
            logger.info(f"Pinecone connected: {self.pinecone_index_name}")
        except ImportError:
            logger.warning("pinecone-client not installed")
        except Exception as e:
            logger.warning(f"Pinecone init failed: {e}")

    def _sync_to_pinecone(self, skill: Skill) -> bool:
        """同步到 Pinecone (如果配置了)"""
        if not self._pinecone_index:
            return False
        
        if not skill.vector:
            # 生成向量
            if self.vectorizer_fn:
                skill.vector = self.vectorizer_fn(skill.name + " " + skill.description)
            else:
                return False  # 没有向量，跳过
        
        try:
            self._pinecone_index.upsert(vectors=[{
                "id": skill.id,
                "values": skill.vector,
                "metadata": {
                    "name": skill.name,
                    "description": skill.description,
                    "category": skill.category,
                    "level": skill.level
                }
            }])
            return True
        except Exception as e:
            logger.error(f"Pinecone sync error: {e}")
            return False

    def _search_pinecone(
        self,
        query_vector: List[float],
        top_k: int = 10
    ) -> List[Tuple[Skill, float]]:
        """Pinecone 向量搜索"""
        if not self._pinecone_index:
            return []
        
        try:
            result = self._pinecone_index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True
            )
            
            skills = []
            for match in result.matches:
                skill = Skill(
                    id=match.id,
                    name=match.metadata.get("name", ""),
                    description=match.metadata.get("description", ""),
                    category=match.metadata.get("category", ""),
                    level=match.metadata.get("level", "beginner"),
                    confidence=match.score
                )
                skills.append((skill, match.score))
            
            return skills
        except Exception as e:
            logger.error(f"Pinecone search error: {e}")
            return []

    def is_pinecone_enabled(self) -> bool:
        """检查 Pinecone 是否启用"""
        return self._pinecone_index is not None

    # ============================================================
    # 技能 CRUD
    # ============================================================

    def add_skill(
        self,
        skill_id: str,
        name: str,
        content: str,
        description: str = "",
        category: str = "general",
        level: str = "beginner",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        sync_pinecone: bool = True
    ) -> bool:
        """
        添加技能
        
        Args:
            skill_id: 技能ID (用于文件名)
            name: 技能名
            content: 技能内容
            description: 描述
            category: 分类
            level: 等级
            tags: 标签
            metadata: 额外元数据
            sync_pinecone: 是否同步到 Pinecone
            
        Returns:
            是否成功
        """
        try:
            skill = Skill(
                id=skill_id,
                name=name,
                content=content,
                description=description,
                category=category,
                level=level,
                tags=tags or [],
                metadata=metadata or {},
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            # 生成向量 (如果有函数)
            if self.vectorizer_fn:
                skill.vector = self.vectorizer_fn(content)
            
            # 保存到本地
            self._save_skill_file(skill)
            
            # 同步到 Pinecone
            if sync_pinecone:
                self._sync_to_pinecone(skill)
            
            logger.debug(f"L3 add_skill: {skill_id}")
            return True
        except Exception as e:
            logger.error(f"L3 add_skill error: {e}")
            return False

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """获取技能"""
        file_path = self.base_dir / f"{skill_id}.md"
        
        if not file_path.exists():
            return None
        
        try:
            content = file_path.read_text(encoding="utf-8")
            return self._parse_skill_file(skill_id, content)
        except Exception as e:
            logger.error(f"L3 get_skill error: {e}")
            return None

    def update_skill(
        self,
        skill_id: str,
        content: Optional[str] = None,
        description: Optional[str] = None,
        level: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        sync_pinecone: bool = True
    ) -> bool:
        """更新技能"""
        skill = self.get_skill(skill_id)
        if not skill:
            return False
        
        try:
            if content is not None:
                skill.content = content
            if description is not None:
                skill.description = description
            if level is not None:
                skill.level = level
            if tags is not None:
                skill.tags = tags
            if metadata is not None:
                skill.metadata.update(metadata)
            
            skill.updated_at = datetime.now().isoformat()
            
            # 重新生成向量
            if self.vectorizer_fn and content:
                skill.vector = self.vectorizer_fn(content)
            
            self._save_skill_file(skill)
            
            if sync_pinecone:
                self._sync_to_pinecone(skill)
            
            return True
        except Exception as e:
            logger.error(f"L3 update_skill error: {e}")
            return False

    def delete_skill(self, skill_id: str) -> bool:
        """删除技能"""
        file_path = self.base_dir / f"{skill_id}.md"
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            
            # 从 Pinecone 删除
            if self._pinecone_index:
                try:
                    self._pinecone_index.delete(ids=[skill_id])
                except Exception:
                    pass
            
            return True
        except Exception as e:
            logger.error(f"L3 delete_skill error: {e}")
            return False

    def _save_skill_file(self, skill: Skill):
        """保存技能到文件"""
        file_path = self.base_dir / f"{skill.id}.md"
        
        # Frontmatter
        frontmatter = {
            "id": skill.id,
            "name": skill.name,
            "description": skill.description,
            "category": skill.category,
            "level": skill.level,
            "tags": skill.tags,
            "created_at": skill.created_at,
            "updated_at": skill.updated_at,
            **skill.metadata
        }
        
        # 写入
        content = "---\n"
        content += yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)
        content += "---\n\n"
        content += skill.content
        
        file_path.write_text(content, encoding="utf-8")

    def _parse_skill_file(self, skill_id: str, content: str) -> Skill:
        """解析技能文件"""
        # 分离 Frontmatter 和内容
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
            else:
                frontmatter = {}
                body = content
        else:
            frontmatter = {}
            body = content
        
        return Skill(
            id=skill_id,
            name=frontmatter.get("name", skill_id),
            description=frontmatter.get("description", ""),
            category=frontmatter.get("category", "general"),
            level=frontmatter.get("level", "beginner"),
            tags=frontmatter.get("tags", []),
            content=body,
            metadata={k: v for k, v in frontmatter.items() 
                     if k not in ["id", "name", "description", "category", "level", "tags", "created_at", "updated_at"]},
            created_at=frontmatter.get("created_at"),
            updated_at=frontmatter.get("updated_at")
        )

    # ============================================================
    # 搜索
    # ============================================================

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Skill]:
        """
        搜索技能
        
        Args:
            query: 搜索关键词
            category: 分类过滤
            tags: 标签过滤
            limit: 返回数量
            
        Returns:
            技能列表
        """
        results = []
        query_lower = query.lower()
        
        for file_path in self.base_dir.glob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                skill = self._parse_skill_file(file_path.stem, content)
                
                # 分类过滤
                if category and skill.category != category:
                    continue
                
                # 标签过滤
                if tags and not any(t in skill.tags for t in tags):
                    continue
                
                # 关键词匹配
                if query:
                    if (query_lower in skill.name.lower() or
                        query_lower in skill.description.lower() or
                        query_lower in skill.content.lower()):
                        results.append(skill)
                else:
                    results.append(skill)
                
                if len(results) >= limit:
                    break
            except Exception:
                continue
        
        return results

    def search_by_category(self, category: str) -> List[Skill]:
        """按分类搜索"""
        return self.search("", category=category)

    def search_by_tags(self, tags: List[str]) -> List[Skill]:
        """按标签搜索"""
        return self.search("", tags=tags)

    def search_similar(
        self,
        query_vector: List[float],
        category: Optional[str] = None,
        top_k: int = 10
    ) -> List[Tuple[Skill, float]]:
        """
        向量相似搜索 (Pinecone)
        """
        # 先尝试 Pinecone
        if self._pinecone_index:
            results = self._search_pinecone(query_vector, top_k)
            if results:
                return results
        
        # 降级: 本地简单搜索
        return self._local_vector_search(query_vector, category, top_k)

    def _local_vector_search(
        self,
        query_vector: List[float],
        category: Optional[str],
        top_k: int
    ) -> List[Tuple[Skill, float]]:
        """本地伪向量搜索 (基于关键词)"""
        skills = self.search("", category=category)
        
        # 简单评分
        scored = []
        for skill in skills:
            if skill.vector and len(skill.vector) == len(query_vector):
                # 计算余弦相似度
                dot = sum(a * b for a, b in zip(query_vector, skill.vector))
                norm1 = sum(a * a for a in query_vector) ** 0.5
                norm2 = sum(a * a for a in skill.vector) ** 0.5
                similarity = dot / (norm1 * norm2) if norm1 and norm2 else 0
                scored.append((skill, similarity))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    # ============================================================
    # 冲突检测
    # ============================================================

    def detect_conflict(
        self,
        new_skill_content: str,
        new_skill_name: str = "",
        threshold: float = 0.85
    ) -> ConflictResult:
        """
        检测技能冲突
        
        Args:
            new_skill_content: 新技能内容
            new_skill_name: 新技能名
            threshold: 冲突阈值
            
        Returns:
            ConflictResult
        """
        conflicts = []
        suggestions = []
        
        # 关键词冲突检测
        keywords = self._extract_keywords(new_skill_content)
        
        existing = self.search(new_skill_name)
        for skill in existing:
            existing_keywords = self._extract_keywords(skill.name + " " + skill.description)
            
            # 计算重叠
            overlap = keywords & existing_keywords
            if len(overlap) >= 3:
                conflict_type = "duplicate" if len(overlap) >= 5 else "overlap"
                
                conflicts.append(Conflict(
                    skill_a=skill.id,
                    skill_b=new_skill_name,
                    type=conflict_type,
                    similarity=len(overlap) / max(len(keywords), len(existing_keywords)),
                    details=f"关键词重叠: {overlap}"
                ))
                
                suggestions.append(f"考虑合并 '{skill.name}' 和 '{new_skill_name}'")
        
        return ConflictResult(
            has_conflicts=len(conflicts) > 0,
            conflicts=conflicts,
            suggestions=suggestions
        )

    def _extract_keywords(self, text: str) -> set:
        """提取关键词"""
        # 简单分词
        words = re.findall(r'\w+', text.lower())
        # 过滤停用词
        stopwords = {"的", "是", "在", "和", "了", "我", "你", "他", "她", "它", "这", "那", "有", "是", "个"}
        return {w for w in words if len(w) >= 2 and w not in stopwords}

    # ============================================================
    # 分类管理
    # ============================================================

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        
        for file_path in self.base_dir.glob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                skill = self._parse_skill_file(file_path.stem, content)
                if skill.category:
                    categories.add(skill.category)
            except Exception:
                continue
        
        return sorted(list(categories))

    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        tags = set()
        
        for file_path in self.base_dir.glob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                skill = self._parse_skill_file(file_path.stem, content)
                tags.update(skill.tags)
            except Exception:
                continue
        
        return sorted(list(tags))

    # ============================================================
    # 工具
    # ============================================================

    def list_all(self) -> List[Skill]:
        """列出所有技能"""
        skills = []
        
        for file_path in self.base_dir.glob("*.md"):
            try:
                skill = self._parse_skill_file(file_path.stem, file_path.read_text(encoding="utf-8"))
                skills.append(skill)
            except Exception:
                continue
        
        return sorted(skills, key=lambda s: s.name)

    def count(self) -> int:
        """统计技能数量"""
        return len(list(self.base_dir.glob("*.md")))

    def get_path(self) -> str:
        """获取 skills 目录路径"""
        return str(self.base_dir)

    def export_index(self) -> str:
        """导出索引 (JSON)"""
        skills = self.list_all()
        return json.dumps([
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "level": s.level,
                "tags": s.tags
            }
            for s in skills
        ], ensure_ascii=False, indent=2)

    def ping(self) -> bool:
        """检查状态"""
        return self.base_dir.exists() and self.base_dir.is_dir()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        skills = self.list_all()
        
        categories = {}
        levels = {}
        
        for skill in skills:
            categories[skill.category] = categories.get(skill.category, 0) + 1
            levels[skill.level] = levels.get(skill.level, 0) + 1
        
        return {
            "total": len(skills),
            "categories": categories,
            "levels": levels,
            "pinecone_enabled": self.is_pinecone_enabled(),
            "path": str(self.base_dir)
        }
