"""
路径分析器
分析流程中的所有可能路径和覆盖率
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional

from .flow_builder import FlowGraph, FlowEdge


@dataclass
class Path:
    """对话路径"""
    id: str
    nodes: List[str]
    conditions: List[str] = field(default_factory=list)
    is_ending: bool = False
    ending_node: Optional[str] = None
    
    def __str__(self):
        return " -> ".join(self.nodes)


@dataclass
class BranchPoint:
    """分支点"""
    node_id: str
    node_name: str
    outgoing_edges: List[FlowEdge]
    conditions: List[str]
    
    @property
    def branch_count(self) -> int:
        return len(self.outgoing_edges)


@dataclass
class PathCoverage:
    """路径覆盖率"""
    total_paths: int
    analyzed_paths: int
    coverage_rate: float
    uncovered_paths: List[Path]
    branch_coverage: Dict[str, float]


class PathAnalyzer:
    """路径分析器"""
    
    def __init__(self):
        self.flow_graph: Optional[FlowGraph] = None
        self.all_paths: List[Path] = []
        self.branch_points: List[BranchPoint] = []
        self.coverage: Optional[PathCoverage] = None
    
    def analyze(self, flow_graph: FlowGraph, parsed) -> PathCoverage:
        """分析流程路径"""
        self.flow_graph = flow_graph
        
        self._collect_all_paths()
        self._identify_branch_points()
        self.coverage = self._calculate_coverage()
        
        return self.coverage
    
    def _collect_all_paths(self):
        """收集所有可能路径"""
        self.all_paths = []
        
        if not self.flow_graph or not self.flow_graph.graph:
            self._collect_simple_paths()
            return
        
        try:
            import networkx as nx
            
            start_nodes = [n for n in self.flow_graph.graph.nodes() 
                          if self.flow_graph.graph.in_degree(n) == 0]
            if not start_nodes:
                start_nodes = list(self.flow_graph.graph.nodes())[:1]
            
            end_nodes = self._get_end_nodes()
            
            path_id = 0
            for start in start_nodes:
                for end in end_nodes:
                    try:
                        paths = list(nx.all_simple_paths(self.flow_graph.graph, start, end))
                        for nodes in paths:
                            self.all_paths.append(Path(
                                id=f"path_{path_id}",
                                nodes=nodes,
                                is_ending=end in ['H', 'I', 'J', 'T', 'U', 'END'],
                                ending_node=end
                            ))
                            path_id += 1
                    except nx.NetworkXNoPath:
                        continue
        except Exception:
            self._collect_simple_paths()
    
    def _collect_simple_paths(self):
        """简化路径收集"""
        if not self.flow_graph:
            return
        
        nodes = list(self.flow_graph.nodes.keys())
        for i in range(len(nodes)):
            path_nodes = nodes[:i+1]
            self.all_paths.append(Path(
                id=f"path_{i}",
                nodes=path_nodes,
                is_ending=nodes[i] in ['H', 'I', 'J', 'T', 'U', 'END']
            ))
    
    def _get_end_nodes(self) -> List[str]:
        """获取结束节点"""
        end_nodes = []
        
        for node_id, node in self.flow_graph.nodes.items():
            if node.is_ending:
                end_nodes.append(node_id)
        
        if self.flow_graph and self.flow_graph.graph:
            for node_id in self.flow_graph.graph.nodes():
                if self.flow_graph.graph.out_degree(node_id) == 0:
                    if node_id not in end_nodes:
                        end_nodes.append(node_id)
        
        if not end_nodes and self.flow_graph:
            end_nodes = [list(self.flow_graph.nodes.keys())[-1]]
        
        return end_nodes
    
    def _identify_branch_points(self):
        """识别所有分支点"""
        self.branch_points = []
        
        if not self.flow_graph:
            return
        
        for node_id, node in self.flow_graph.nodes.items():
            out_edges = [e for e in self.flow_graph.edges if e.source == node_id]
            
            if len(out_edges) > 1:
                conditions = [e.condition for e in out_edges if e.condition]
                
                self.branch_points.append(BranchPoint(
                    node_id=node_id,
                    node_name=node.name,
                    outgoing_edges=out_edges,
                    conditions=conditions
                ))
    
    def _calculate_coverage(self) -> PathCoverage:
        """计算覆盖率"""
        branch_coverage = {bp.node_id: 0.0 for bp in self.branch_points}
        
        return PathCoverage(
            total_paths=len(self.all_paths),
            analyzed_paths=0,
            coverage_rate=0.0,
            uncovered_paths=self.all_paths.copy(),
            branch_coverage=branch_coverage
        )
    
    def get_critical_paths(self) -> List[Path]:
        """获取关键路径"""
        critical = []
        
        for path in self.all_paths:
            score = len(path.nodes) * 0.1
            if path.is_ending:
                score += 0.5
            branch_count = sum(1 for bp in self.branch_points if bp.node_id in path.nodes)
            score += branch_count * 0.3
            
            if score >= 1.0:
                critical.append((score, path))
        
        critical.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in critical[:10]]
    
    def suggest_next_test(self, tested_paths: List[List[str]]) -> Optional[Path]:
        """建议下一个测试路径"""
        tested_set = set(tuple(p) for p in tested_paths)
        untested = [p for p in self.all_paths if tuple(p.nodes) not in tested_set]
        
        if not untested:
            return None
        
        critical = self.get_critical_paths()
        for path in critical:
            if path in untested:
                return path
        
        return min(untested, key=lambda p: len(p.nodes))
