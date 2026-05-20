"""
通用标签系统
从 Prompt 中自动提取标签定义，支持意向标签和个性标签
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple, Protocol
from enum import Enum
import re


class MatcherProtocol(Protocol):
    """匹配器协议"""
    def match(self, text: str, context: Dict) -> Tuple[bool, List[str]]:
        """匹配文本，返回 (是否匹配, 匹配到的标签)"""
        ...


@dataclass
class LabelDefinition:
    """标签定义"""
    id: str
    name: str
    category: str
    trigger_keywords: List[str] = field(default_factory=list)
    trigger_pattern: Optional[str] = None
    conditions: List[str] = field(default_factory=list)
    count_rules: str = "once"
    priority: int = 0
    exclusive: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TagResult:
    """标签结果"""
    intent_label: str
    intent_label_name: str
    personal_tags: List[str] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "intent_label": self.intent_label,
            "intent_label_name": self.intent_label_name,
            "personal_tags": self.personal_tags,
            "counts": self.counts,
            "metadata": self.metadata
        }


class KeywordMatcher:
    """关键词匹配器"""
    
    def __init__(self, keywords: List[str], case_sensitive: bool = False):
        self.keywords = keywords
        self.case_sensitive = case_sensitive
    
    def match(self, text: str, context: Dict) -> Tuple[bool, List[str]]:
        if not self.case_sensitive:
            text = text.lower()
        matched = [kw for kw in self.keywords if kw.lower() in text]
        return len(matched) > 0, matched


class RegexMatcher:
    """正则匹配器"""
    
    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern, re.IGNORECASE)
    
    def match(self, text: str, context: Dict) -> Tuple[bool, List[str]]:
        matches = self.pattern.findall(text)
        return len(matches) > 0, matches


class CompositeMatcher:
    """组合匹配器"""
    
    def __init__(self, matchers: List[MatcherProtocol], mode: str = "any"):
        self.matchers = matchers
        self.mode = mode
    
    def match(self, text: str, context: Dict) -> Tuple[bool, List[str]]:
        results = [m.match(text, context) for m in self.matchers]
        
        if self.mode == "any":
            return any(r[0] for r in results), [k for r in results for k in r[1]]
        return all(r[0] for r in results), [k for r in results for k in r[1]]


class ConditionMatcher:
    """条件匹配器"""
    
    def __init__(self, conditions: Dict[str, Any]):
        self.conditions = conditions
    
    def match(self, text: str, context: Dict) -> Tuple[bool, List[str]]:
        matched = []
        
        if "min_count" in self.conditions:
            label_id = self.conditions.get("label_id", "")
            count = context.get("counts", {}).get(label_id, 0)
            if count >= self.conditions["min_count"]:
                matched.append(f"count>={self.conditions['min_count']}")
        
        if "call_duration_lt" in self.conditions:
            duration = context.get("call_duration", float('inf'))
            if duration < self.conditions["call_duration_lt"]:
                matched.append("duration_check")
        
        return len(matched) > 0, matched


class TagEngine:
    """
    通用标签引擎
    
    用法:
        engine = TagEngine()
        engine.register_label(LabelDefinition(...))
        engine.process_turn("好的，可以", turn=1)
        result = engine.get_result()
    """
    
    def __init__(self):
        self.intent_labels: Dict[str, LabelDefinition] = {}
        self.personal_labels: Dict[str, LabelDefinition] = {}
        self._counts: Dict[str, int] = {}
        self._collected_tags: Set[str] = set()
        self._records: List[Dict] = []
        self._call_start_time: Optional[float] = None
        self._call_end_time: Optional[float] = None
        self._matchers: Dict[str, MatcherProtocol] = {}
    
    def register_label(self, label: LabelDefinition):
        """注册标签"""
        if label.category == "intent":
            self.intent_labels[label.id] = label
        else:
            self.personal_labels[label.id] = label
        
        self._build_matcher(label)
    
    def register_labels_from_dict(self, labels: List[Dict]):
        """从字典批量注册"""
        for label_dict in labels:
            label = LabelDefinition(**label_dict)
            self.register_label(label)
    
    def _build_matcher(self, label: LabelDefinition):
        """构建匹配器"""
        matchers = []
        
        if label.trigger_keywords:
            matchers.append(KeywordMatcher(label.trigger_keywords))
        
        if label.trigger_pattern:
            matchers.append(RegexMatcher(label.trigger_pattern))
        
        if matchers:
            if len(matchers) == 1:
                self._matchers[label.id] = matchers[0]
            else:
                self._matchers[label.id] = CompositeMatcher(matchers)
    
    def process_turn(self, user_input: str, node: str = "", turn: int = 0):
        """处理一轮对话"""
        self._records.append({"turn": turn, "node": node, "user_input": user_input})
        context = self._build_context()
        
        for label_id, label in self.personal_labels.items():
            matcher = self._matchers.get(label_id)
            if matcher:
                matched, _ = matcher.match(user_input, context)
                if matched:
                    if label.count_rules == "accumulate":
                        self._counts[label_id] = self._counts.get(label_id, 0) + 1
                    
                    full_tag = f"{label.category}-{label.name}"
                    if full_tag not in self._collected_tags or label.count_rules == "accumulate":
                        self._collected_tags.add(full_tag)
    
    def set_call_time(self, start: float = None, end: float = None):
        """设置通话时间"""
        if start is not None:
            self._call_start_time = start
        if end is not None:
            self._call_end_time = end
    
    def _build_context(self) -> Dict:
        import time
        
        call_duration = 0
        if self._call_start_time and self._call_end_time:
            call_duration = self._call_end_time - self._call_start_time
        elif self._call_start_time:
            call_duration = time.time() - self._call_start_time
        
        return {
            "counts": self._counts.copy(),
            "tags": list(self._collected_tags),
            "turn_count": len(self._records),
            "call_duration": call_duration,
            "last_node": self._records[-1]["node"] if self._records else ""
        }
    
    def determine_intent(self) -> TagResult:
        """判定意向标签"""
        context = self._build_context()
        
        sorted_labels = sorted(
            self.intent_labels.values(),
            key=lambda x: x.priority,
            reverse=True
        )
        
        for label in sorted_labels:
            if label.conditions:
                matcher = ConditionMatcher(label.conditions)
                matched, _ = matcher.match("", context)
                if matched:
                    return self._create_result(label)
            else:
                matcher = self._matchers.get(label.id)
                if matcher:
                    for tag in self._collected_tags:
                        matched, _ = matcher.match(tag, context)
                        if matched:
                            return self._create_result(label)
        
        default_label = self.intent_labels.get("C")
        return self._create_result(default_label) if default_label else TagResult(
            intent_label="C",
            intent_label_name="待定",
            personal_tags=sorted(self._collected_tags),
            counts=self._counts.copy()
        )
    
    def _create_result(self, label: LabelDefinition) -> TagResult:
        return TagResult(
            intent_label=label.id,
            intent_label_name=label.name,
            personal_tags=sorted(self._collected_tags),
            counts=self._counts.copy()
        )
    
    def get_result(self) -> TagResult:
        """获取最终结果"""
        return self.determine_intent()
    
    def reset(self):
        """重置状态"""
        self._counts.clear()
        self._collected_tags.clear()
        self._records.clear()
        self._call_start_time = None
        self._call_end_time = None


class TagParser:
    """标签解析器 - 从 Prompt 提取标签定义"""
    
    def parse_from_markdown(self, text: str) -> Tuple[List[Dict], List[Dict]]:
        """从 Markdown 解析标签"""
        intent_labels = []
        personal_labels = []
        
        intent_section = self._extract_section(text, "意向标签", "个性标签")
        if intent_section:
            intent_labels = self._parse_table(intent_section, "intent")
        
        personal_section = self._extract_section(text, "个性标签", None)
        if personal_section:
            personal_labels = self._parse_table(personal_section, "personal")
        
        return intent_labels, personal_labels
    
    def _extract_section(self, text: str, start: str, end: str) -> str:
        start_idx = text.find(start)
        if start_idx == -1:
            return ""
        
        if end:
            end_idx = text.find(end, start_idx)
            if end_idx == -1:
                return text[start_idx:]
            return text[start_idx:end_idx]
        
        return text[start_idx:]
    
    def _parse_table(self, section: str, category: str) -> List[Dict]:
        labels = []
        lines = section.split("\n")
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("---"):
                continue
            
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) >= 2:
                label = self._parse_row(cells, category)
                if label:
                    labels.append(label)
        
        return labels
    
    def _parse_row(self, cells: List[str], category: str) -> Optional[Dict]:
        try:
            if category == "intent":
                return {
                    "id": cells[0].strip(),
                    "name": cells[1].strip(),
                    "category": "intent",
                    "conditions": self._extract_conditions(cells[2] if len(cells) > 2 else ""),
                    "priority": self._parse_priority(cells[0])
                }
            else:
                return {
                    "id": self._sanitize_id(cells[0]),
                    "name": cells[0].strip(),
                    "category": "personal",
                    "trigger_keywords": self._extract_keywords(cells[1] if len(cells) > 1 else ""),
                    "priority": 1
                }
        except Exception:
            return None
    
    def _extract_conditions(self, text: str) -> List[str]:
        conditions = []
        count_matches = re.findall(r">?=\s*(\d+)", text)
        for match in count_matches:
            conditions.append(f"count>={match}")
        semantic_matches = re.findall(r'[""'']([^""'']+)[""'']', text)
        conditions.extend(semantic_matches)
        return conditions
    
    def _extract_keywords(self, text: str) -> List[str]:
        keywords = []
        quoted = re.findall(r'[""'']([^""'']+)[""'']', text)
        keywords.extend(quoted)
        split_words = re.split(r'[,，、]', text)
        for word in split_words:
            word = word.strip()
            if word and len(word) > 1:
                keywords.append(word)
        return list(set(keywords))
    
    def _parse_priority(self, label_id: str) -> int:
        priority_map = {
            "M": 100, "N": 90, "I": 85, "J": 85, "E": 80,
            "L": 70, "K": 70, "A": 50, "B": 40, "C": 30, "D": 20,
        }
        return priority_map.get(label_id, 10)
    
    def _sanitize_id(self, name: str) -> str:
        return name.replace(" ", "_").replace("/", "_").lower()


def create_tag_engine_from_prompt(prompt_text: str) -> Tuple[TagEngine, List[Dict], List[Dict]]:
    """从 Prompt 文本创建标签引擎"""
    parser = TagParser()
    intent_labels, personal_labels = parser.parse_from_markdown(prompt_text)
    
    engine = TagEngine()
    engine.register_labels_from_dict(intent_labels)
    engine.register_labels_from_dict(personal_labels)
    
    return engine, intent_labels, personal_labels
