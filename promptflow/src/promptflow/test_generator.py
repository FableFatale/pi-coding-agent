"""
测试用例生成器
根据路径分析生成测试用例
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from .path_analyzer import Path, PathAnalyzer, BranchPoint
from .flow_builder import FlowGraph


class TestType(Enum):
    NORMAL = "normal"
    EDGE = "edge"
    ERROR = "error"
    NEGATIVE = "negative"


@dataclass
class TestInput:
    """测试输入"""
    node: str
    text: str
    input_type: TestType = TestType.NORMAL


@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    description: str
    test_type: TestType
    path: List[str]
    user_inputs: List[TestInput] = field(default_factory=list)
    expected_ending: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "test_type": self.test_type.value,
            "path": self.path,
            "user_inputs": [{"node": i.node, "input": i.text} for i in self.user_inputs],
            "expected_ending": self.expected_ending,
            "variables": self.variables
        }


@dataclass
class TestSuite:
    """测试套件"""
    name: str
    description: str
    test_cases: List[TestCase] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "total_tests": len(self.test_cases),
            "test_cases": [tc.to_dict() for tc in self.test_cases]
        }


class TestGenerator:
    """测试用例生成器"""
    
    def __init__(self):
        self.path_analyzer: Optional[PathAnalyzer] = None
        self.flow_graph: Optional[FlowGraph] = None
        self._test_id_counter = 0
    
    def generate(self, flow_graph: FlowGraph, path_analyzer: PathAnalyzer) -> TestSuite:
        """生成测试套件"""
        self.flow_graph = flow_graph
        self.path_analyzer = path_analyzer
        
        test_cases = []
        test_cases.extend(self._generate_path_tests())
        test_cases.extend(self._generate_edge_tests())
        test_cases.extend(self._generate_critical_tests())
        
        return TestSuite(
            name="Prompt Flow Test Suite",
            description=f"Generated from {len(flow_graph.nodes)} nodes, {len(path_analyzer.all_paths)} paths",
            test_cases=test_cases,
            metadata={
                "total_paths": len(path_analyzer.all_paths),
                "total_nodes": len(flow_graph.nodes),
                "branch_points": len(path_analyzer.branch_points)
            }
        )
    
    def _generate_path_tests(self) -> List[TestCase]:
        """生成路径测试用例"""
        test_cases = []
        critical_paths = self.path_analyzer.get_critical_paths()
        
        for path in critical_paths[:5]:
            tc = self._create_test(
                name=f"Path: {'->'.join(path.nodes)}",
                description=f"Test path: {path.id}",
                test_type=TestType.NORMAL,
                path=path.nodes,
                expected_ending=path.ending_node
            )
            test_cases.append(tc)
        
        return test_cases
    
    def _generate_edge_tests(self) -> List[TestCase]:
        """生成边界测试用例"""
        test_cases = []
        
        # 分支边界测试
        for bp in self.path_analyzer.branch_points:
            for edge in bp.outgoing_edges:
                tc = self._create_test(
                    name=f"Edge: {bp.node_id} -> {edge.target}",
                    description=f"Test condition: {edge.condition or 'default'}",
                    test_type=TestType.EDGE,
                    path=[bp.node_id, edge.target],
                    expected_ending=edge.target if edge.target in ['H', 'I', 'J', 'T', 'U', 'END'] else None
                )
                test_cases.append(tc)
        
        # 边界输入测试
        for node_id in list(self.flow_graph.nodes.keys())[:3]:
            for text, desc in [("嗯", "中性"), ("不知道", "否定"), ("?", "疑问")]:
                tc = self._create_test(
                    name=f"Edge Input @ {node_id}: {desc}",
                    description=f"Test {desc} at node {node_id}",
                    test_type=TestType.EDGE,
                    path=[node_id],
                    user_inputs=[TestInput(node=node_id, text=text)]
                )
                test_cases.append(tc)
        
        return test_cases
    
    def _generate_critical_tests(self) -> List[TestCase]:
        """生成关键场景测试"""
        test_cases = []
        
        # 最佳路径
        if self.flow_graph and self.flow_graph.nodes:
            node_ids = list(self.flow_graph.nodes.keys())
            happy_path = node_ids[:min(6, len(node_ids))]
            
            tc = self._create_test(
                name="Happy Path",
                description="Test complete flow with positive responses",
                test_type=TestType.NORMAL,
                path=happy_path,
                expected_ending=happy_path[-1] if happy_path else None,
                user_inputs=[TestInput(n, "好的") for n in happy_path]
            )
            test_cases.append(tc)
        
        return test_cases
    
    def _create_test(self, name: str, description: str, test_type: TestType,
                    path: List[str], expected_ending: Optional[str] = None,
                    user_inputs: Optional[List[TestInput]] = None) -> TestCase:
        """创建测试用例"""
        self._test_id_counter += 1
        
        return TestCase(
            id=f"tc_{self._test_id_counter:04d}",
            name=name,
            description=description,
            test_type=test_type,
            path=path,
            expected_ending=expected_ending,
            user_inputs=user_inputs or []
        )
