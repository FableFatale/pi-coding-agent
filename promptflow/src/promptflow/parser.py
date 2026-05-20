"""
Prompt 解析器
从 Prompt 文本中提取结构化信息
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
import re


@dataclass
class NodeDefinition:
    """节点定义"""
    id: str
    name: str
    prompt: str
    example_dialogue: Optional[str] = None
    next_nodes: Dict[str, str] = field(default_factory=dict)
    rules: List[str] = field(default_factory=list)
    is_ending: bool = False


@dataclass
class RuleDefinition:
    """规则定义"""
    name: str
    content: str
    applies_to: List[str] = field(default_factory=list)


@dataclass
class VariableDefinition:
    """变量定义"""
    name: str
    placeholder: str
    description: str
    example: Optional[str] = None


@dataclass
class ParsedPrompt:
    """解析结果"""
    raw_text: str
    role: str = ""
    goal: str = ""
    nodes: Dict[str, NodeDefinition] = field(default_factory=dict)
    rules: List[RuleDefinition] = field(default_factory=list)
    variables: Dict[str, VariableDefinition] = field(default_factory=dict)
    global_rules: List[str] = field(default_factory=list)
    libraries: Dict[str, List[str]] = field(default_factory=dict)


class PromptParser:
    """Prompt 解析器"""
    
    def __init__(self):
        self._patterns = self._init_patterns()
    
    def _init_patterns(self) -> Dict[str, re.Pattern]:
        return {
            'node_header': re.compile(r'(#{1,6})\s*([A-Z0-9]+)\s*(.*?)(?=\n#|\Z)', re.DOTALL),
            'dialogue': re.compile(r'对话示例.*?>\s*(.+?)(?=<|#####|\Z)', re.DOTALL),
            'prompt': re.compile(r'节点prompt\s*(.+?)(?=##|\Z)', re.DOTALL),
            'variable': re.compile(r'\{([^}]+)\}'),
            'branch': re.compile(r'如果(.+?)，转到(.+?)[；;。]', re.DOTALL),
            'jump': re.compile(r'转到[结束]?[节点]?\s*([A-Z0-9]+)', re.IGNORECASE),
            'flow_arrow': re.compile(r'([A-Z]+)\s*-->\s*\|?([^|>]+)\|?\s*([A-Z]+)'),
        }
    
    def parse(self, prompt_text: str) -> ParsedPrompt:
        """解析 Prompt 文本"""
        result = ParsedPrompt(raw_text=prompt_text)
        
        result.role = self._extract_role(prompt_text)
        result.goal = self._extract_goal(prompt_text)
        result.variables = self._extract_variables(prompt_text)
        result.nodes = self._extract_nodes(prompt_text)
        result.rules = self._extract_rules(prompt_text)
        result.global_rules = self._extract_global_rules(prompt_text)
        result.libraries = self._extract_libraries(prompt_text)
        
        return result
    
    def _extract_role(self, text: str) -> str:
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
        patterns = [
            re.compile(r'##\s*总目标[：:]\s*(.+?)(?=##|\n\n|\Z)', re.DOTALL),
            re.compile(r'核心目标[：:]\s*(.+?)(?=\n|。|\Z)', re.DOTALL),
        ]
        for p in patterns:
            match = p.search(text)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_variables(self, text: str) -> Dict[str, VariableDefinition]:
        variables = {}
        for match in self._patterns['variable'].finditer(text):
            var_name = match.group(1)
            if var_name not in variables:
                variables[var_name] = VariableDefinition(
                    name=var_name,
                    placeholder=f"{{{var_name}}}",
                    description=f"变量: {var_name}"
                )
        return variables
    
    def _extract_nodes(self, text: str) -> Dict[str, NodeDefinition]:
        nodes = {}
        
        # 查找节点标题
        for match in self._patterns['node_header'].finditer(text):
            level = len(match.group(1))
            node_id = match.group(2).strip()
            node_name = match.group(3).strip().strip('()【】[]')
            
            # 找到节点内容范围
            start = match.end()
            remaining = text[start:]
            next_match = list(re.finditer(r'#{1,6}\s*[A-Z]', remaining))
            end = start + next_match[0].start() if next_match else len(text)
            
            content = text[start:end]
            
            # 提取对话示例
            dialogue_match = self._patterns['dialogue'].search(content)
            dialogue = dialogue_match.group(1).strip() if dialogue_match else None
            
            # 提取节点prompt
            prompt_match = self._patterns['prompt'].search(content)
            node_prompt = prompt_match.group(1).strip() if prompt_match else content.strip()
            
            # 判断是否为结束节点
            is_ending = any(x in node_id for x in ['挂机', '结束', 'H', 'I', 'J', 'T', 'U', 'END'])
            
            # 提取跳转
            next_nodes = {}
            for jump_match in self._patterns['jump'].finditer(content):
                next_nodes['default'] = jump_match.group(1)
            
            nodes[node_id] = NodeDefinition(
                id=node_id,
                name=node_name,
                prompt=node_prompt,
                example_dialogue=dialogue,
                next_nodes=next_nodes,
                is_ending=is_ending
            )
        
        # 从流程图中提取跳转
        self._extract_flow_edges(text, nodes)
        
        return nodes
    
    def _extract_flow_edges(self, text: str, nodes: Dict[str, NodeDefinition]):
        """从流程图提取边"""
        for match in self._patterns['flow_arrow'].finditer(text):
            source = match.group(1)
            condition = match.group(2).strip()
            target = match.group(3)
            
            if source in nodes and target:
                if condition:
                    nodes[source].next_nodes[condition] = target
                elif 'default' not in nodes[source].next_nodes:
                    nodes[source].next_nodes['default'] = target
    
    def _extract_rules(self, text: str) -> List[RuleDefinition]:
        rules = []
        patterns = [
            (r'##\s*绝对执行规则[：:]\s*(.+?)(?=##|\Z)', '绝对执行规则'),
            (r'##\s*语义规则[：:]\s*(.+?)(?=##|\Z)', '语义规则'),
            (r'##\s*禁止行为[：:]\s*(.+?)(?=##|\Z)', '禁止行为'),
        ]
        
        for pattern, name in patterns:
            for match in re.finditer(pattern, text, re.DOTALL):
                rules.append(RuleDefinition(
                    name=name,
                    content=match.group(1).strip()
                ))
        
        return rules
    
    def _extract_global_rules(self, text: str) -> List[str]:
        rules = []
        patterns = [
            r'【全流程通用全局执行规则】(.+?)(?=【|\Z)',
            r'全局规则[：:]\s*(.+?)(?=##|\Z)',
        ]
        
        for p in patterns:
            for match in re.finditer(p, text, re.DOTALL):
                rules.append(match.group(1).strip())
        
        return rules
    
    def _extract_libraries(self, text: str) -> Dict[str, List[str]]:
        libraries = {}
        
        for match in re.finditer(r'###?\s*([^#\n]+库)[：:]\s*([^\n]+(?:\n[^\n#]+)*)', text):
            lib_name = match.group(1).strip()
            lib_content = match.group(2).strip()
            keywords = [k.strip() for k in re.split(r'[,，、\n]', lib_content) if k.strip()]
            libraries[lib_name] = keywords
        
        return libraries
