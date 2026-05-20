"""
Prompt 解析器
从 Prompt 文本中提取结构化信息
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum


class NodeType(Enum):
    """节点类型"""
    NORMAL = "normal"
    ENDING = "ending"
    BRANCH = "branch"
    GLOBAL = "global"


@dataclass
class ExtractedNode:
    """提取的节点"""
    id: str
    name: str
    prompt: str
    example_dialogue: Optional[str] = None
    node_type: NodeType = NodeType.NORMAL
    next_nodes: Dict[str, str] = field(default_factory=dict)  # 条件 -> 节点ID
    rules: List[str] = field(default_factory=list)


@dataclass
class ExtractedRule:
    """提取的规则"""
    name: str
    content: str
    applies_to: List[str] = field(default_factory=list)  # 应用的节点


@dataclass
class ExtractedVariable:
    """提取的变量"""
    name: str
    placeholder: str
    description: str
    example: Optional[str] = None


@dataclass
class ParsedPrompt:
    """解析结果"""
    raw_text: str
    role: str
    goal: str
    nodes: Dict[str, ExtractedNode] = field(default_factory=dict)
    rules: List[ExtractedRule] = field(default_factory=list)
    variables: Dict[str, ExtractedVariable] = field(default_factory=dict)
    global_rules: List[str] = field(default_factory=list)
    product_library: Optional[Dict] = None


class PromptParser:
    """Prompt 解析器"""
    
    def __init__(self):
        self._patterns = self._init_patterns()
    
    def _init_patterns(self) -> Dict[str, re.Pattern]:
        """初始化正则模式"""
        return {
            # 节点标题 (如 #### A, ### 节点A)
            'node_header': re.compile(r'#{1,6}\s*([A-Z0-9]+)\s*[节点]?.*?(?=\n#|\Z)', re.DOTALL),
            
            # 对话示例
            'dialogue_example': re.compile(r'#####\s*对话示例\s*>\s*(.+?)(?=#####|\Z)', re.DOTALL),
            
            # 节点prompt
            'node_prompt': re.compile(r'#####\s*节点prompt\s*(.+?)(?=#####|\Z)', re.DOTALL),
            
            # 变量占位符 {xxx}
            'variable': re.compile(r'\{([^}]+)\}'),
            
            # 条件分支 if/else
            'branch_if': re.compile(r'如果(.+?)，转到(.+?)[；;。]', re.DOTALL),
            'branch_condition': re.compile(r'\|([^|]+)\|([^|]+)\|'),
            
            # 流程节点跳转
            'node_jump': re.compile(r'转到[结束]?[节点]?\s*([A-Z0-9]+)', re.IGNORECASE),
            'node_ref': re.compile(r'(?:Node|节点)\s*([A-Z0-9]+)', re.IGNORECASE),
            
            # 全局规则
            'global_rules': re.compile(r'【全局[规则执行]*】(.+?)(?=【|\Z)', re.DOTALL),
            
            # 商品库/规则库
            'library': re.compile(r'##?\s*([^库]+库)[：:]\s*(.+?)(?=##|\Z)', re.DOTALL),
        }
    
    def parse(self, prompt_text: str) -> ParsedPrompt:
        """
        解析 Prompt 文本
        
        Args:
            prompt_text: 原始 prompt 文本
            
        Returns:
            ParsedPrompt: 解析结果
        """
        result = ParsedPrompt(raw_text=prompt_text)
        
        # 1. 提取角色定义
        result.role = self._extract_role(prompt_text)
        
        # 2. 提取目标
        result.goal = self._extract_goal(prompt_text)
        
        # 3. 提取变量
        result.variables = self._extract_variables(prompt_text)
        
        # 4. 提取节点
        result.nodes = self._extract_nodes(prompt_text)
        
        # 5. 提取规则
        result.rules = self._extract_rules(prompt_text)
        
        # 6. 提取全局规则
        result.global_rules = self._extract_global_rules(prompt_text)
        
        # 7. 提取商品库
        result.product_library = self._extract_libraries(prompt_text)
        
        return result
    
    def _extract_role(self, text: str) -> str:
        """提取角色定义"""
        patterns = [
            re.compile(r'你是(.+?)[，,。\n]', re.DOTALL),
            re.compile(r'角色定位[：:]\s*(.+?)(?=\n\n|\Z)', re.DOTALL),
        ]
        for p in patterns:
            match = p.search(text)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_goal(self, text: str) -> str:
        """提取目标"""
        patterns = [
            re.compile(r'##\s*总目标[：:]\s*(.+?)(?=##|\n\n|\Z)', re.DOTALL),
            re.compile(r'核心目标[：:]\s*(.+?)(?=\n|。|\Z)', re.DOTALL),
            re.compile(r'目标[：:]\s*(.+?)(?=\n\n|\Z)', re.DOTALL),
        ]
        for p in patterns:
            match = p.search(text)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_variables(self, text: str) -> Dict[str, ExtractedVariable]:
        """提取变量"""
        variables = {}
        for match in self._patterns['variable'].finditer(text):
            var_name = match.group(1)
            if var_name not in variables:
                variables[var_name] = ExtractedVariable(
                    name=var_name,
                    placeholder=f"{{{var_name}}}",
                    description=f"变量: {var_name}"
                )
        return variables
    
    def _extract_nodes(self, text: str) -> Dict[str, ExtractedNode]:
        """提取所有节点"""
        nodes = {}
        
        # 匹配所有节点标题
        node_headers = re.finditer(r'(#{1,6})\s*([A-Z0-9]+)\s*(.*?)(?=\n)', text)
        
        for i, match in enumerate(node_headers):
            level = len(match.group(1))
            node_id = match.group(2).strip()
            node_name = match.group(3).strip().strip('()【】[]')
            
            # 找到该节点的内容范围
            start = match.end()
            # 找下一个同级或更高级标题
            next_match = list(re.finditer(r'#{1,6}\s*[A-Z]', text[start:]))
            if next_match:
                end = start + next_match[0].start()
            else:
                end = len(text)
            
            node_content = text[start:end]
            
            # 提取对话示例
            dialogue_match = re.search(r'对话示例.*?>\s*(.+?)(?=<|#####|\Z)', node_content, re.DOTALL)
            dialogue = dialogue_match.group(1).strip() if dialogue_match else None
            
            # 提取节点prompt
            prompt_match = re.search(r'节点prompt\s*(.+?)(?=##|\Z)', node_content, re.DOTALL)
            node_prompt = prompt_match.group(1).strip() if prompt_match else node_content.strip()
            
            # 判断是否为结束节点
            is_ending = '挂机' in node_id or '结束' in node_id or node_id in ['T', 'U', 'H', 'I', 'J', 'END']
            
            # 提取跳转关系
            next_nodes = {}
            for jump_match in re.finditer(r'转到[节点]?\s*([A-Z0-9]+)', node_content):
                next_nodes['default'] = jump_match.group(1)
            for cond_match in re.finditer(r'如果(.+?)[,，].*?转到(.+?)[。;；]', node_content):
                next_nodes[cond_match.group(1).strip()] = cond_match.group(2).strip()
            
            nodes[node_id] = ExtractedNode(
                id=node_id,
                name=node_name,
                prompt=node_prompt,
                example_dialogue=dialogue,
                node_type=NodeType.ENDING if is_ending else NodeType.NORMAL,
                next_nodes=next_nodes
            )
        
        return nodes
    
    def _extract_rules(self, text: str) -> List[ExtractedRule]:
        """提取规则"""
        rules = []
        
        # 提取各种规则块
        rule_patterns = [
            (r'##\s*绝对执行规则[：:]\s*(.+?)(?=##|\Z)', '绝对执行规则'),
            (r'##\s*语义规则[：:]\s*(.+?)(?=##|\Z)', '语义规则'),
            (r'##\s*禁止行为[：:]\s*(.+?)(?=##|\Z)', '禁止行为'),
            (r'##\s*特别[注意规则][：:]\s*(.+?)(?=##|\Z)', '特别注意'),
        ]
        
        for pattern, rule_name in rule_patterns:
            for match in re.finditer(pattern, text, re.DOTALL):
                rules.append(ExtractedRule(
                    name=rule_name,
                    content=match.group(1).strip()
                ))
        
        return rules
    
    def _extract_global_rules(self, text: str) -> List[str]:
        """提取全局规则"""
        global_rules = []
        
        # 查找全局规则章节
        patterns = [
            r'【全流程通用全局执行规则】(.+?)(?=【|\Z)',
            r'全局规则[：:]\s*(.+?)(?=##|\Z)',
        ]
        
        for p in patterns:
            for match in re.finditer(p, text, re.DOTALL):
                global_rules.append(match.group(1).strip())
        
        return global_rules
    
    def _extract_libraries(self, text: str) -> Optional[Dict]:
        """提取商品库/规则库"""
        libraries = {}
        
        # 匹配库内容
        for match in re.finditer(r'###?\s*([^#\n]+库)[：:]\s*([^\n]+(?:\n[^\n#]+)*)', text):
            lib_name = match.group(1).strip()
            lib_content = match.group(2).strip()
            
            # 提取关键词列表
            keywords = [k.strip() for k in re.split(r'[,，、\n]', lib_content) if k.strip()]
            libraries[lib_name] = keywords
        
        return libraries if libraries else None
