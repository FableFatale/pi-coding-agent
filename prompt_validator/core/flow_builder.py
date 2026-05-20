"""
流程构建器
从解析结果构建可执行的流程图
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple
from enum import Enum
import networkx as nx

from .parser import ParsedPrompt, ExtractedNode, NodeType


class EdgeType(Enum):
    """边类型"""
    NORMAL = "normal"
    CONDITIONAL = "conditional"
    ENDING = "ending"


@dataclass
class FlowEdge:
    """流程边"""
    source: str
    target: str
    condition: str  # 触发条件
    edge_type: EdgeType = EdgeType.NORMAL


@dataclass
class FlowGraph:
    """流程图"""
    nodes: Dict[str, ExtractedNode]
    edges: List[FlowEdge]
    graph: nx.DiGraph = None
    
    # 统计
    total_paths: int = 0
    max_depth: int = 0
    
    def __post_init__(self):
        self._build_nx_graph()
        self._analyze()
    
    def _build_nx_graph(self):
        """构建 NetworkX 图"""
        self.graph = nx.DiGraph()
        
        # 添加节点
        for node_id, node in self.nodes.items():
            self.graph.add_node(
                node_id,
                name=node.name,
                node_type=node.node_type.value,
                is_ending=node.node_type == NodeType.ENDING
            )
        
        # 添加边
        for edge in self.edges:
            self.graph.add_edge(
                edge.source,
                edge.target,
                condition=edge.condition,
                edge_type=edge.edge_type.value
            )
    
    def _analyze(self):
        """分析流程图"""
        if not self.graph.nodes():
            return
        
        # 计算所有路径
        try:
            # 找起始节点
            start_nodes = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
            if not start_nodes:
                start_nodes = list(self.graph.nodes())[:1]  # 取第一个
            
            end_nodes = [n for n in self.graph.nodes() 
                        if self.graph.out_degree(n) == 0 or 
                        self.nodes.get(n, None) and self.nodes[n].node_type == NodeType.ENDING]
            
            # 计算路径
            all_paths = []
            for start in start_nodes:
                for end in end_nodes:
                    try:
                        paths = list(nx.all_simple_paths(self.graph, start, end))
                        all_paths.extend(paths)
                    except nx.NetworkXNoPath:
                        continue
            
            self.total_paths = len(all_paths)
            self.max_depth = max(len(p) for p in all_paths) if all_paths else 0
            
        except Exception:
            self.total_paths = 0
            self.max_depth = 0
    
    def get_all_paths(self) -> List[List[str]]:
        """获取所有路径"""
        if not self.graph.nodes():
            return []
        
        start_nodes = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
        if not start_nodes:
            start_nodes = list(self.graph.nodes())[:1]
        
        end_nodes = [n for n in self.graph.nodes() 
                    if self.graph.out_degree(n) == 0 or 
                    self.nodes.get(n, None) and self.nodes[n].node_type == NodeType.ENDING]
        
        all_paths = []
        for start in start_nodes:
            for end in end_nodes:
                try:
                    paths = list(nx.all_simple_paths(self.graph, start, end))
                    all_paths.extend(paths)
                except nx.NetworkXNoPath:
                    continue
        
        return all_paths
    
    def get_reachable_nodes(self, from_node: str) -> Set[str]:
        """获取从某节点可达的所有节点"""
        if from_node not in self.graph:
            return set()
        return nx.descendants(self.graph, from_node)
    
    def get_reachable_paths(self, from_node: str, to_node: str) -> List[List[str]]:
        """获取从某节点到某节点的所有路径"""
        try:
            return list(nx.all_simple_paths(self.graph, from_node, to_node))
        except nx.NetworkXNoPath:
            return []


class FlowBuilder:
    """流程构建器"""
    
    def __init__(self):
        self.start_node_id: Optional[str] = None
    
    def build(self, parsed: ParsedPrompt) -> FlowGraph:
        """
        从解析结果构建流程图
        
        Args:
            parsed: 解析结果
            
        Returns:
            FlowGraph: 流程图
        """
        edges = []
        
        # 1. 确定起始节点
        self._identify_start_node(parsed.nodes)
        
        # 2. 从节点定义中提取边
        for node_id, node in parsed.nodes.items():
            self._extract_edges(node, node_id, edges, parsed.nodes)
        
        # 3. 从流程图中提取边（如有）
        self._extract_from_flow_graph(parsed.raw_text, edges)
        
        # 4. 推断隐含边
        self._infer_implicit_edges(parsed.nodes, edges)
        
        return FlowGraph(
            nodes=parsed.nodes,
            edges=edges
        )
    
    def _identify_start_node(self, nodes: Dict[str, ExtractedNode]):
        """识别起始节点"""
        # 通常是 A 或者第一个节点
        if 'A' in nodes:
            self.start_node_id = 'A'
        elif nodes:
            self.start_node_id = list(nodes.keys())[0]
    
    def _extract_edges(self, node: ExtractedNode, node_id: str, 
                      edges: List[FlowEdge], all_nodes: Dict[str, ExtractedNode]):
        """从节点定义中提取边"""
        # 从 next_nodes 提取
        for condition, target in node.next_nodes.items():
            edges.append(FlowEdge(
                source=node_id,
                target=target,
                condition=condition if condition != 'default' else '',
                edge_type=EdgeType.CONDITIONAL if condition != 'default' else EdgeType.NORMAL
            ))
        
        # 检查是否有结束标记
        if node.node_type == NodeType.ENDING:
            # 结束节点不需要出边（但可以加一个虚拟结束节点）
            pass
    
    def _extract_from_flow_graph(self, text: str, edges: List[FlowEdge]):
        """从文本中的流程图提取边"""
        import re
        
        # 匹配 Mermaid 风格或文本风格的流程图
        patterns = [
            # A -->|条件| B
            re.compile(r'([A-Z]+)\s*-->\s*\|([^|]+)\|\s*([A-Z]+)'),
            # A --> B
            re.compile(r'([A-Z]+)\s*-->\s*([A-Z]+)'),
            # A |条件| B |条件| C
            re.compile(r'([A-Z]+)\s*\[([^\]]+)\]\s*\[([^\]]+)\]'),
        ]
        
        for pattern in patterns:
            for match in pattern.finditer(text):
                if len(match.groups()) >= 2:
                    source = match.group(1)
                    condition = match.group(2) if len(match.groups()) > 2 else ''
                    target = match.group(3) if len(match.groups()) > 2 else match.group(2)
                    
                    edges.append(FlowEdge(
                        source=source,
                        target=target,
                        condition=condition,
                        edge_type=EdgeType.CONDITIONAL if condition else EdgeType.NORMAL
                    ))
    
    def _infer_implicit_edges(self, nodes: Dict[str, ExtractedNode], 
                               edges: List[FlowEdge]):
        """推断隐含边（基于节点顺序和流程逻辑）"""
        # 如果节点没有出边，根据节点名称推断
        node_ids = list(nodes.keys())
        
        for i, node_id in enumerate(node_ids):
            node = nodes[node_id]
            
            # 如果没有出边且不是结束节点
            has_out_edge = any(e.source == node_id for e in edges)
            is_ending = node.node_type == NodeType.ENDING
            
            if not has_out_edge and not is_ending:
                # 找到下一个节点
                if i + 1 < len(node_ids):
                    next_node = node_ids[i + 1]
                    edges.append(FlowEdge(
                        source=node_id,
                        target=next_node,
                        condition='',
                        edge_type=EdgeType.NORMAL
                    ))
