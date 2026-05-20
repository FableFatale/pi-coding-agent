"""
测试用例生成器
根据路径分析生成测试用例
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from .path_analyzer import Path, PathAnalyzer
from .flow_builder import FlowGraph


class TestType(Enum):
    """测试类型"""
    NORMAL = "normal"           # 正常流程
    EDGE = "edge"              # 边界条件
    ERROR = "error"            # 异常处理
    NEGATIVE = "negative"       # 负面测试


@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    description: str
    test_type: TestType
    path: List[str]  # 经过的节点序列
    user_inputs: List[TestInput] = field(default_factory=list)
    expected_outputs: List[str] = field(default_factory=list)
    expected_ending: Optional[str] = None  # 期望的结束节点
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "test_type": self.test_type.value,
            "path": self.path,
            "user_inputs": [{"node": i.node, "input": i.text, "type": i.input_type.value} 
                          for i in self.user_inputs],
            "expected_ending": self.expected_ending,
            "variables": self.variables
        }


@dataclass
class TestInput:
    """测试输入"""
    node: str
    text: str
    input_type: TestType = TestType.NORMAL


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
        self._input_strategies: Dict[str, Callable] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """注册默认输入策略"""
        # 这些策略根据节点类型生成合适的测试输入
        self._input_strategies = {
            # 确认类节点
            'A': self._generate_self_confirmation_inputs,
            'B': self._generate_knows_person_inputs,
            'D': self._generate_permission_inputs,
            
            # 信息核实类节点
            'K': self._generate_contract_inputs,
            'L': self._generate_phone_inputs,
            'M': self._generate_broadband_inputs,
            'O': self._generate_appliance_inputs,
            'P': self._generate_cash_inputs,
            'Q': self._generate_camera_inputs,
            'N': self._generate_installment_inputs,
            
            # 异常处理节点
            'E': self._generate_refusal_inputs,
            'F': self._generate_busy_inputs,
            'G': self._generate_complaint_inputs,
            
            # 默认
            'default': self._generate_default_inputs
        }
    
    def generate(self, flow_graph: FlowGraph, path_analyzer: PathAnalyzer) -> TestSuite:
        """
        生成测试套件
        
        Args:
            flow_graph: 流程图
            path_analyzer: 路径分析器
            
        Returns:
            TestSuite: 测试套件
        """
        self.flow_graph = flow_graph
        self.path_analyzer = path_analyzer
        
        test_cases = []
        
        # 1. 生成路径测试用例
        test_cases.extend(self._generate_path_tests())
        
        # 2. 生成边界测试用例
        test_cases.extend(self._generate_edge_tests())
        
        # 3. 生成异常测试用例
        test_cases.extend(self._generate_error_tests())
        
        # 4. 生成关键场景测试
        test_cases.extend(self._generate_critical_scenario_tests())
        
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
        
        # 获取关键路径
        critical_paths = self.path_analyzer.get_critical_paths()
        
        for path in critical_paths[:10]:  # 最多10个
            tc = self._create_test_case(
                name=f"Path Test: {'->'.join(path.nodes)}",
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
        
        # 1. 测试每个分支点的所有分支
        for bp in self.path_analyzer.branch_points:
            for edge in bp.outgoing_edges:
                path = self._build_path_to_branch(bp.node_id)
                path.append(edge.target)
                
                tc = self._create_test_case(
                    name=f"Edge Test: {bp.node_id} -> {edge.target}",
                    description=f"Test branch: {edge.condition or 'default'}",
                    test_type=TestType.EDGE,
                    path=path,
                    expected_ending=edge.target if edge.target in ['H', 'I', 'J', 'T', 'U', 'END'] else None
                )
                test_cases.append(tc)
        
        # 2. 边界输入测试
        edge_inputs = [
            ("嗯", "中性语气"),
            ("嗯嗯", "重复语气"),
            ("不知道", "否定"),
            ("什么", "疑问"),
            ("", "空输入"),
        ]
        
        # 为关键节点生成边界输入测试
        for node_id in ['K', 'L', 'N']:
            for text, desc in edge_inputs:
                tc = self._create_test_case(
                    name=f"Edge Input @ {node_id}: {desc}",
                    description=f"Test {desc} at node {node_id}",
                    test_type=TestType.EDGE,
                    path=[node_id],
                    user_inputs=[TestInput(node=node_id, text=text)]
                )
                test_cases.append(tc)
        
        return test_cases
    
    def _generate_error_tests(self) -> List[TestCase]:
        """生成异常测试用例"""
        test_cases = []
        
        # 拒绝场景
        refusal_tests = [
            ("不需要", "明确拒绝"),
            ("别打了", "要求停止"),
            ("挂了吧", "要求挂机"),
        ]
        
        for text, desc in refusal_tests:
            tc = self._create_test_case(
                name=f"Refusal Test: {desc}",
                description=f"Test user refusal: {text}",
                test_type=TestType.ERROR,
                path=['E'],
                user_inputs=[TestInput(node='A', text=text)]
            )
            test_cases.append(tc)
        
        # 忙碌场景
        busy_tests = [
            ("现在忙", "正在忙"),
            ("没空", "没时间"),
            ("在开会", "会议中"),
        ]
        
        for text, desc in busy_tests:
            tc = self._create_test_case(
                name=f"Busy Test: {desc}",
                description=f"Test user busy: {text}",
                test_type=TestType.ERROR,
                path=['F'],
                user_inputs=[TestInput(node='D', text=text)]
            )
            test_cases.append(tc)
        
        # 投诉场景
        complaint_tests = [
            ("我要投诉", "明确投诉"),
            ("举报你们", "举报意图"),
        ]
        
        for text, desc in complaint_tests:
            tc = self._create_test_case(
                name=f"Complaint Test: {desc}",
                description=f"Test user complaint: {text}",
                test_type=TestType.ERROR,
                path=['G'],
                user_inputs=[TestInput(node='D', text=text)]
            )
            test_cases.append(tc)
        
        return test_cases
    
    def _generate_critical_scenario_tests(self) -> List[TestCase]:
        """生成关键场景测试"""
        test_cases = []
        
        # 完整流程测试 - 最佳路径
        best_path = ['A', 'D', 'K', 'L', 'N', 'H']
        tc = self._create_test_case(
            name="Happy Path: Complete Flow",
            description="Test complete flow with positive responses",
            test_type=TestType.NORMAL,
            path=best_path,
            expected_ending='H',
            user_inputs=[
                TestInput('A', '是，我是本人'),
                TestInput('D', '好的，可以'),
                TestInput('K', '清楚'),
                TestInput('L', '拿到了手机'),
                TestInput('N', '知道'),
            ]
        )
        test_cases.append(tc)
        
        # 完整流程测试 - 折现场景
        cash_path = ['A', 'D', 'K', 'L', 'M', 'O', 'P', 'N', 'J']
        tc = self._create_test_case(
            name="Cash Conversion Flow",
            description="Test flow when user only received cash",
            test_type=TestType.NORMAL,
            path=cash_path,
            expected_ending='J',
            user_inputs=[
                TestInput('A', '是'),
                TestInput('D', '可以'),
                TestInput('K', '嗯'),
                TestInput('L', '没有'),
                TestInput('M', '也没有'),
                TestInput('O', '都没有'),
                TestInput('P', '折现了'),
                TestInput('N', '不知道'),
            ]
        )
        test_cases.append(tc)
        
        # 非本人场景
        not_self_path = ['A', 'B', 'T']
        tc = self._create_test_case(
            name="Not Self Flow",
            description="Test flow when caller is not the customer",
            test_type=TestType.NORMAL,
            path=not_self_path,
            expected_ending='T',
            user_inputs=[
                TestInput('A', '不是我'),
                TestInput('B', '不认识'),
            ]
        )
        test_cases.append(tc)
        
        return test_cases
    
    def _create_test_case(self, name: str, description: str, test_type: TestType,
                         path: List[str], expected_ending: Optional[str] = None,
                         user_inputs: Optional[List[TestInput]] = None) -> TestCase:
        """创建测试用例"""
        self._test_id_counter += 1
        
        tc = TestCase(
            id=f"tc_{self._test_id_counter:04d}",
            name=name,
            description=description,
            test_type=test_type,
            path=path,
            expected_ending=expected_ending,
            user_inputs=user_inputs or []
        )
        
        # 如果没有提供输入，自动生成
        if not tc.user_inputs:
            tc.user_inputs = self._generate_inputs_for_path(path)
        
        return tc
    
    def _generate_inputs_for_path(self, path: List[str]) -> List[TestInput]:
        """为路径生成测试输入"""
        inputs = []
        
        for node_id in path:
            strategy = self._input_strategies.get(node_id, self._input_strategies['default'])
            generated = strategy(node_id)
            inputs.extend(generated)
        
        return inputs
    
    def _build_path_to_branch(self, node_id: str) -> List[str]:
        """构建到分支点的路径"""
        # 简化：返回 [node_id]
        # 完整实现需要从起始节点追溯
        return [node_id]
    
    # ============ 输入生成策略 ============
    
    def _generate_self_confirmation_inputs(self, node_id: str) -> List[TestInput]:
        return [
            TestInput(node_id, "是，我是本人"),
            TestInput(node_id, "不是我"),
        ]
    
    def _generate_knows_person_inputs(self, node_id: str) -> List[TestInput]:
        return [
            TestInput(node_id, "认识"),
            TestInput(node_id, "不认识"),
        ]
    
    def _generate_permission_inputs(self, node_id: str) -> List[TestInput]:
        return [
            TestInput(node_id, "好的，可以"),
            TestInput(node_id, "不需要"),
            TestInput(node_id, "现在忙"),
        ]
    
    def _generate_contract_inputs(self, node_id: str) -> List[TestInput]:
        return [
            TestInput(node_id, "清楚"),
            TestInput(node_id, "不知道"),
            TestInput(node_id, "嗯"),
        ]
    
    def _generate_phone_inputs(self, node_id: str) -> List[TestInput]:
        return [
            TestInput(node_id, "拿到了手机"),
            TestInput(node_id, "有优惠"),
            TestInput(node_id, "什么都没有"),
        ]
    
    def _generate_broadband_inputs(self, node_id: str) -> List[TestInput]:
        return [
            TestInput(node_id, "有宽带"),
            TestInput(node_id, "没有"),
        ]
    
    def _generate_appliance_inputs(self, node_id: str) -> List[TestInput]:
        return [
            TestInput(node_id, "有小度"),
            TestInput(node_id, "没有家电"),
        ]
    
    def _generate_cash_inputs(self, node_id: str) -> List[TestInput]:
        return [
            TestInput(node_id, "折现了"),
            TestInput(node_id, "没有折现"),
        ]
    
    def _generate_camera_inputs(self, node_id: str) -> List[TestInput]:
        return [
            TestInput(node_id, "拿到了"),
            TestInput(node_id, "没拿到"),
        ]
    
    def _generate_installment_inputs(self, node_id: str) -> List[TestInput]:
        return [
            TestInput(node_id, "知道"),
            TestInput(node_id, "不知道"),
            TestInput(node_id, "什么意思"),
        ]
    
    def _generate_refusal_inputs(self, node_id: str) -> List[TestInput]:
        return [
            TestInput(node_id, "不需要"),
            TestInput(node_id, "算了"),
        ]
    
    def _generate_busy_inputs(self, node_id: str) -> List[TestInput]:
        return [
            TestInput(node_id, "在忙"),
            TestInput(node_id, "没空"),
        ]
    
    def _generate_complaint_inputs(self, node_id: str) -> List[TestInput]:
        return [
            TestInput(node_id, "我要投诉"),
            TestInput(node_id, "要举报"),
        ]
    
    def _generate_default_inputs(self, node_id: str) -> List[TestInput]:
        return [
            TestInput(node_id, "好的"),
            TestInput(node_id, "嗯"),
        ]
