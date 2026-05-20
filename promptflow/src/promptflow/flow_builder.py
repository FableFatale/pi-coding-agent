"""
流程构建器
从解析结果构建可执行的流程图
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from enum import Enum

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

from .parser import ParsedPrompt, NodeDefinition


class EdgeType(Enum):
    NORMAL = "normal"
    CONDITIONAL = "conditional"
    ENDING = "ending"


@dataclass
class FlowEdge:
    """流程边"""
    source: str
    target: str
    condition: str = ""
    edge_type: EdgeType = EdgeType.NORMAL


@dataclass
class FlowGraph:
    """流程图"""
    nodes: Dict[str, NodeDefinition]
    edges: List[FlowEdge]
    graph: Optional['nx.DiGraph'] = None
    total_paths: int = 0
    max_depth: int = 0
    
    def __post_init__(self):
        if HAS_NETWORKX:
            self._build_nx_graph()
            self._analyze()
    
    def _build_nx_graph(self):
        """构建 NetworkX 图"""
        self.graph = nx.DiGraph()
        
        for node_id, node in self.nodes.items():
            self.graph.add_node(
                node_id,
                name=node.name,
                is_ending=node.is_ending
            )
        
        for edge in self.edges:
            self.graph.add_edge(
                edge.source,
                edge.target,
                condition=edge.condition,
                edge_type=edge.edge_type.value
            )
    
    def _analyze(self):
        """分析流程图"""
        if not self.graph or not self.graph.nodes():
            return
        
        try:
            start_nodes = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
            if not start_nodes:
                start_nodes = list(self.graph.nodes())[:1]
            
            end_nodes = [n for n in self.graph.nodes() 
                        if self.graph.out_degree(n) == 0 or self.nodes.get(n, None) and self.nodes[n].is_ending]
            
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
            pass
    
    def get_all_paths(self) -> List[List[str]]:
        """获取所有路径"""
        if not self.graph or not self.graph.nodes():
            return []
        
        start_nodes = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
        if not start_nodes:
            start_nodes = list(self.graph.nodes())[:1]
        
        end_nodes = [n for n in self.graph.nodes() 
                    if self.graph.out_degree(n) == 0 or self.nodes.get(n, None) and self.nodes[n].is_ending]
        
        all_paths = []
        for start in start_nodes:
            for end in end_nodes:
                try:
                    paths = list(nx.all_simple_paths(self.graph, start, end))
                    all_paths.extend(paths)
                except nx.NetworkXNoPath:
                    continue
        
        return all_paths


class FlowBuilder:
    """流程构建器"""
    
    def __init__(self):
        self.start_node_id: Optional[str] = None
    
    def build(self, parsed: ParsedPrompt) -> FlowGraph:
        """从解析结果构建流程图"""
        edges = []
        
        self._identify_start_node(parsed.nodes)
        self._extract_edges(parsed.nodes, edges)
        self._infer_implicit_edges(parsed.nodes, edges)
        
        return FlowGraph(nodes=parsed.nodes, edges=edges)
    
    def _identify_start_node(self, nodes: Dict[str, NodeDefinition]):
        """识别起始节点"""
        if 'A' in nodes:
            self.start_node_id = 'A'
        elif nodes:
            self.start_node_id = list(nodes.keys())[0]
    
    def _extract_edges(self, nodes: Dict[str, NodeDefinition], edges: List[FlowEdge]):
        """从节点定义提取边"""
        for node_id, node in nodes.items():
            for condition, target in node.next_nodes.items():
                edges.append(FlowEdge(
                    source=node_id,
                    target=target,
                    condition=condition,
                    edge_type=EdgeType.CONDITIONAL if condition != 'default' else EdgeType.NORMAL
                ))
    
    def _infer_implicit_edges(self, nodes: Dict[str, NodeDefinition], edges: List[FlowEdge]):
        """推断隐含边"""
        node_ids = list(nodes.keys())
        
        for i, node_id in enumerate(node_ids):
            node = nodes[node_id]
            has_out_edge = any(e.source == node_id for e in edges)
            
            if not has_out_edge and not node.is_ending:
                if i + 1 < len(node_ids):
                    next_node = node_ids[i + 1]
                    edges.append(FlowEdge(
                        source=node_id,
                        target=next_node,
                        condition='',
                        edge_type=EdgeType.NORMAL
                    ))
