"""
测试 TestGenerator - 测试生成器测试用例
"""
import pytest
import sys
sys.path.insert(0, 'src')

from promptflow.test_generator import (
    TestGenerator, TestCase, TestSuite, TestInput, TestType
)
from promptflow.flow_builder import FlowGraph, FlowEdge
from promptflow.parser import NodeDefinition
from promptflow.path_analyzer import PathAnalyzer, Path, BranchPoint


class TestTestGenerator:
    """TestGenerator 测试类"""
    
    @pytest.fixture
    def generator(self):
        """创建测试生成器实例"""
        return TestGenerator()
    
    @pytest.fixture
    def sample_flow(self):
        """创建示例流程图"""
        nodes = {
            'A': NodeDefinition(id='A', name='开始', prompt='开始'),
            'B': NodeDefinition(id='B', name='中间', prompt='中间'),
            'C': NodeDefinition(id='C', name='结束', prompt='结束', is_ending=True),
        }
        edges = [
            FlowEdge(source='A', target='B'),
            FlowEdge(source='B', target='C'),
        ]
        return FlowGraph(nodes=nodes, edges=edges)
    
    @pytest.fixture
    def sample_analyzer(self, sample_flow):
        """创建示例路径分析器"""
        analyzer = PathAnalyzer()
        analyzer.analyze(sample_flow, None)
        return analyzer
    
    def test_generator_initialization(self, generator):
        """测试生成器初始化"""
        assert generator is not None
        assert generator.path_analyzer is None
        assert generator.flow_graph is None
        assert generator._test_id_counter == 0
    
    def test_generate_returns_test_suite(self, generator, sample_flow, sample_analyzer):
        """测试生成返回测试套件"""
        suite = generator.generate(sample_flow, sample_analyzer)
        
        assert isinstance(suite, TestSuite)
        assert suite.name == "Prompt Flow Test Suite"
    
    def test_generate_creates_test_cases(self, generator, sample_flow, sample_analyzer):
        """测试生成创建测试用例"""
        suite = generator.generate(sample_flow, sample_analyzer)
        
        assert len(suite.test_cases) > 0
        assert all(isinstance(tc, TestCase) for tc in suite.test_cases)
    
    def test_generate_includes_metadata(self, generator, sample_flow, sample_analyzer):
        """测试生成包含元数据"""
        suite = generator.generate(sample_flow, sample_analyzer)
        
        assert 'total_paths' in suite.metadata
        assert 'total_nodes' in suite.metadata
        assert suite.metadata['total_nodes'] == 3


class TestGeneratePathTests:
    """路径测试生成测试"""
    
    def test_generate_path_tests_exists(self):
        """测试路径测试生成方法存在"""
        generator = TestGenerator()
        
        assert hasattr(generator, '_generate_path_tests')
        assert callable(generator._generate_path_tests)
    
    def test_path_tests_have_normal_type(self):
        """测试路径测试用例类型"""
        generator = TestGenerator()
        flow = self._create_simple_flow()
        analyzer = PathAnalyzer()
        analyzer.analyze(flow, None)
        generator.flow_graph = flow
        generator.path_analyzer = analyzer
        
        tests = generator._generate_path_tests()
        
        assert all(tc.test_type == TestType.NORMAL for tc in tests)


class TestGenerateEdgeTests:
    """边界测试生成测试"""
    
    def test_generate_edge_tests_exists(self):
        """测试边界测试生成方法存在"""
        generator = TestGenerator()
        
        assert hasattr(generator, '_generate_edge_tests')
        assert callable(generator._generate_edge_tests)
    
    def test_edge_tests_have_edge_type(self):
        """测试边界测试用例类型"""
        generator = TestGenerator()
        flow = self._create_branch_flow()
        analyzer = PathAnalyzer()
        analyzer.analyze(flow, None)
        generator.flow_graph = flow
        generator.path_analyzer = analyzer
        
        tests = generator._generate_edge_tests()
        
        assert all(tc.test_type == TestType.EDGE for tc in tests)
    
    def _create_branch_flow(self):
        """创建分支流程"""
        nodes = {
            'A': NodeDefinition(id='A', name='A', prompt='A', 
                              next_nodes={'是': 'B', '否': 'C'}),
            'B': NodeDefinition(id='B', name='B', prompt='B', is_ending=True),
            'C': NodeDefinition(id='C', name='C', prompt='C', is_ending=True),
        }
        edges = [
            FlowEdge(source='A', target='B', condition='是'),
            FlowEdge(source='A', target='C', condition='否'),
        ]
        return FlowGraph(nodes=nodes, edges=edges)


class TestGenerateCriticalTests:
    """关键场景测试生成测试"""
    
    def test_generate_critical_tests_exists(self):
        """测试关键场景测试生成方法存在"""
        generator = TestGenerator()
        
        assert hasattr(generator, '_generate_critical_tests')
        assert callable(generator._generate_critical_tests)
    
    def _create_simple_flow(self):
        """创建简单流程"""
        nodes = {
            'A': NodeDefinition(id='A', name='A', prompt='A'),
            'B': NodeDefinition(id='B', name='B', prompt='B', is_ending=True),
        }
        edges = [FlowEdge(source='A', target='B')]
        return FlowGraph(nodes=nodes, edges=edges)


class TestCreateTest:
    """创建测试用例测试"""
    
    def test_create_test_increments_id(self):
        """测试创建测试用例递增ID"""
        generator = TestGenerator()
        
        tc1 = generator._create_test(
            name="Test 1",
            description="Desc 1",
            test_type=TestType.NORMAL,
            path=['A', 'B']
        )
        
        tc2 = generator._create_test(
            name="Test 2",
            description="Desc 2",
            test_type=TestType.NORMAL,
            path=['A', 'B']
        )
        
        # 第二个测试的ID应该大于第一个
        id1 = int(tc1.id.split('_')[1])
        id2 = int(tc2.id.split('_')[1])
        assert id2 > id1
    
    def test_create_test_with_user_inputs(self):
        """测试创建带用户输入的测试用例"""
        generator = TestGenerator()
        user_inputs = [
            TestInput(node='A', text='你好'),
            TestInput(node='B', text='好的'),
        ]
        
        tc = generator._create_test(
            name="Test with inputs",
            description="Test with user inputs",
            test_type=TestType.NORMAL,
            path=['A', 'B'],
            user_inputs=user_inputs
        )
        
        assert len(tc.user_inputs) == 2
        assert tc.user_inputs[0].text == '你好'
    
    def test_create_test_with_expected_ending(self):
        """测试创建带期望结束节点的测试用例"""
        generator = TestGenerator()
        
        tc = generator._create_test(
            name="Test with ending",
            description="Test with expected ending",
            test_type=TestType.NORMAL,
            path=['A', 'B', 'C'],
            expected_ending='C'
        )
        
        assert tc.expected_ending == 'C'


class TestTestCase:
    """测试用例类测试"""
    
    def test_test_case_to_dict(self):
        """测试测试用例转换为字典"""
        tc = TestCase(
            id='tc_0001',
            name='Test Case',
            description='Description',
            test_type=TestType.NORMAL,
            path=['A', 'B', 'C'],
            user_inputs=[TestInput(node='A', text='输入1')],
            expected_ending='C'
        )
        
        result = tc.to_dict()
        
        assert result['id'] == 'tc_0001'
        assert result['name'] == 'Test Case'
        assert result['test_type'] == 'normal'
        assert len(result['path']) == 3
        assert len(result['user_inputs']) == 1
        assert result['expected_ending'] == 'C'


class TestTestSuite:
    """测试套件类测试"""
    
    def test_test_suite_to_dict(self):
        """测试测试套件转换为字典"""
        suite = TestSuite(
            name='Test Suite',
            description='Test suite description',
            test_cases=[
                TestCase(
                    id='tc_0001',
                    name='Test 1',
                    description='Desc 1',
                    test_type=TestType.NORMAL,
                    path=['A']
                ),
                TestCase(
                    id='tc_0002',
                    name='Test 2',
                    description='Desc 2',
                    test_type=TestType.EDGE,
                    path=['A', 'B']
                ),
            ],
            metadata={'total_paths': 5}
        )
        
        result = suite.to_dict()
        
        assert result['name'] == 'Test Suite'
        assert result['total_tests'] == 2
        assert len(result['test_cases']) == 2


class TestTestInput:
    """测试输入类测试"""
    
    def test_test_input_creation(self):
        """测试测试输入创建"""
        ti = TestInput(
            node='A',
            text='用户输入',
            input_type=TestType.NORMAL
        )
        
        assert ti.node == 'A'
        assert ti.text == '用户输入'
        assert ti.input_type == TestType.NORMAL
    
    def test_test_input_default_type(self):
        """测试测试输入默认类型"""
        ti = TestInput(node='A', text='输入')
        
        assert ti.input_type == TestType.NORMAL


class TestTestTypes:
    """测试类型枚举测试"""
    
    def test_all_test_types_exist(self):
        """测试所有测试类型存在"""
        assert TestType.NORMAL.value == 'normal'
        assert TestType.EDGE.value == 'edge'
        assert TestType.ERROR.value == 'error'
        assert TestType.NEGATIVE.value == 'negative'
    
    def test_test_types_are_unique(self):
        """测试测试类型唯一性"""
        values = [t.value for t in TestType]
        assert len(values) == len(set(values))


class TestTestGeneratorEdgeCases:
    """边界情况测试"""
    
    def test_generate_with_empty_flow(self, generator):
        """测试空流程图"""
        flow = FlowGraph(nodes={}, edges=[])
        analyzer = PathAnalyzer()
        analyzer.analyze(flow, None)
        
        suite = generator.generate(flow, analyzer)
        
        assert suite is not None
        assert len(suite.test_cases) >= 0
    
    def test_generate_with_single_node(self, generator):
        """测试单节点流程"""
        nodes = {
            'A': NodeDefinition(id='A', name='A', prompt='A', is_ending=True),
        }
        flow = FlowGraph(nodes=nodes, edges=[])
        analyzer = PathAnalyzer()
        analyzer.analyze(flow, None)
        
        suite = generator.generate(flow, analyzer)
        
        assert suite is not None
    
    def _create_simple_flow(self):
        """创建简单流程"""
        nodes = {
            'A': NodeDefinition(id='A', name='A', prompt='A'),
            'B': NodeDefinition(id='B', name='B', prompt='B', is_ending=True),
        }
        edges = [FlowEdge(source='A', target='B')]
        return FlowGraph(nodes=nodes, edges=edges)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
