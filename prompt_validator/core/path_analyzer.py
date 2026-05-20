"""
路径分析器
分析流程中的所有可能路径和覆盖率
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

from .flow_builder import FlowGraph, FlowEdge
from .parser import ParsedPrompt, ExtractedNode


@dataclass
class Path:
    """对话路径"""
    id: str
    nodes: List[str]
    conditions: List[str] = field(default_factory=list)
    is_ending_path: bool = False
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
    branch_coverage: Dict[str, float]  # 节点ID -> 覆盖率
    critical_paths: List[Path]  # 关键路径（高风险）


class PathAnalyzer:
    """路径分析器"""
    
    def __init__(self):
        self.flow_graph: Optional[FlowGraph] = None
        self.all_paths: List[Path] = []
        self.branch_points: List[BranchPoint] = []
        self.coverage: Optional[PathCoverage] = None
    
    def analyze(self, flow_graph: FlowGraph, parsed: ParsedPrompt) -> PathCoverage:
        """
        分析流程路径
        
        Args:
            flow_graph: 流程图
            parsed: 解析结果
            
        Returns:
            PathCoverage: 覆盖率分析结果
        """
        self.flow_graph = flow_graph
        
        # 1. 收集所有路径
        self._collect_all_paths()
        
        # 2. 识别分支点
        self._identify_branch_points()
        
        # 3. 计算覆盖率
        self.coverage = self._calculate_coverage()
        
        return self.coverage
    
    def _collect_all_paths(self):
        """收集所有可能路径"""
        self.all_paths = []
        
        if not self.flow_graph or not self.flow_graph.graph.nodes():
            return
        
        # 获取起始节点
        start_nodes = [n for n in self.flow_graph.graph.nodes() 
                      if self.flow_graph.graph.in_degree(n) == 0]
        if not start_nodes:
            start_nodes = [list(self.flow_graph.graph.nodes())[0]]
        
        # 获取结束节点
        end_nodes = self._get_end_nodes()
        
        path_id = 0
        for start in start_nodes:
            for end in end_nodes:
                try:
                    import networkx as nx
                    paths = list(nx.all_simple_paths(self.flow_graph.graph, start, end))
                    
                    for nodes in paths:
                        is_ending = end in [n.value for n in ['H', 'I', 'J', 'T', 'U', 'END'] 
                                           if hasattr(n, 'value')] or \
                                   self.flow_graph.nodes.get(end, None) and \
                                   self.flow_graph.nodes[end].node_type.value == 'ending'
                        
                        self.all_paths.append(Path(
                            id=f"path_{path_id}",
                            nodes=nodes,
                            is_ending_path=is_ending,
                            ending_node=end
                        ))
                        path_id += 1
                        
                except Exception:
                    continue
        
        # 如果没找到路径，尝试简化分析
        if not self.all_paths:
            self._collect_simple_paths()
    
    def _collect_simple_paths(self):
        """简化路径收集"""
        nodes = list(self.flow_graph.graph.nodes())
        
        # 假设线性流程
        all_paths_set = []
        for i, node in enumerate(nodes):
            path_nodes = nodes[:i+1]
            if path_nodes not in all_paths_set:
                all_paths_set.append(path_nodes)
        
        for idx, nodes in enumerate(all_paths_set):
            self.all_paths.append(Path(
                id=f"path_{idx}",
                nodes=nodes,
                is_ending_path=nodes[-1] in ['H', 'I', 'J', 'T', 'U', 'END']
            ))
    
    def _get_end_nodes(self) -> List[str]:
        """获取结束节点"""
        end_nodes = []
        
        for node_id, node in self.flow_graph.nodes.items():
            if node.node_type.value == 'ending':
                end_nodes.append(node_id)
        
        # 如果没有明确的结束节点，使用出度为0的节点
        if not end_nodes:
            for node_id in self.flow_graph.graph.nodes():
                if self.flow_graph.graph.out_degree(node_id) == 0:
                    end_nodes.append(node_id)
        
        # 如果还是没有，取最后一个节点
        if not end_nodes:
            end_nodes = [list(self.flow_graph.graph.nodes())[-1]]
        
        return end_nodes
    
    def _identify_branch_points(self):
        """识别所有分支点"""
        self.branch_points = []
        
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
        # 默认覆盖率为0%
        branch_coverage = {bp.node_id: 0.0 for bp in self.branch_points}
        
        # 分析的关键路径（这里先标记为全路径）
        critical_paths = self.all_paths[:5] if len(self.all_paths) > 5 else self.all_paths
        
        return PathCoverage(
            total_paths=len(self.all_paths),
            analyzed_paths=0,  # 待测试后更新
            coverage_rate=0.0,
            uncovered_paths=self.all_paths.copy(),
            branch_coverage=branch_coverage,
            critical_paths=critical_paths
        )
    
    def get_critical_paths(self) -> List[Path]:
        """获取关键路径（需要优先测试的）"""
        # 关键路径定义：
        # 1. 包含结束节点的路径
        # 2. 路径较长的路径
        # 3. 包含分支点的路径
        
        critical = []
        
        for path in self.all_paths:
            score = 0
            
            # 长度得分
            score += len(path.nodes) * 0.1
            
            # 结束路径
            if path.is_ending_path:
                score += 0.5
            
            # 包含分支
            branch_count = sum(1 for bp in self.branch_points if bp.node_id in path.nodes)
            score += branch_count * 0.3
            
            if score >= 1.0:
                critical.append((score, path))
        
        # 按得分排序
        critical.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in critical[:10]]
    
    def get_untested_paths(self, tested_paths: List[List[str]]) -> List[Path]:
        """获取未测试的路径"""
        tested_set = set(tuple(p) for p in tested_paths)
        untested = []
        
        for path in self.all_paths:
            if tuple(path.nodes) not in tested_set:
                untested.append(path)
        
        return untested
    
    def suggest_next_test(self, tested_paths: List[List[str]]) -> Optional[Path]:
        """建议下一个测试路径"""
        untested = self.get_untested_paths(tested_paths)
        
        if not untested:
            return None
        
        # 优先测试关键路径
        critical = self.get_critical_paths()
        for path in critical:
            if path in untested:
                return path
        
        # 否则返回最短路径
        return min(untested, key=lambda p: len(p.nodes))
