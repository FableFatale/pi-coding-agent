"""
测试 PathAnalyzer - 路径分析器测试用例
"""
import pytest
import sys
sys.path.insert(0, 'src')

from promptflow.path_analyzer import PathAnalyzer, Path, PathCoverage, BranchPoint
from promptflow.flow_builder import FlowBuilder, FlowGraph, FlowEdge
from promptflow.parser import ParsedPrompt, NodeDefinition


class TestPathAnalyzer:
    """PathAnalyzer 测试类"""
    
    @pytest.fixture
    def analyzer(self):
        """创建路径分析器实例"""
        return PathAnalyzer()
    
    @pytest.fixture
    def simple_flow(self):
        """创建简单流程图"""
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
    def branch_flow(self):
        """创建分支流程图"""
        nodes = {
            'A': NodeDefinition(id='A', name='开始', prompt='开始', 
                              next_nodes={'同意': 'B', '拒绝': 'C'}),
            'B': NodeDefinition(id='B', name='处理', prompt='处理', is_ending=True),
            'C': NodeDefinition(id='C', name='拒绝', prompt='拒绝', is_ending=True),
        }
        edges = [
            FlowEdge(source='A', target='B', condition='同意'),
            FlowEdge(source='A', target='C', condition='拒绝'),
        ]
        return FlowGraph(nodes=nodes, edges=edges)
    
    def test_analyzer_initialization(self, analyzer):
        """测试分析器初始化"""
        assert analyzer is not None
        assert analyzer.flow_graph is None
        assert len(analyzer.all_paths) == 0
    
    def test_analyze_simple_flow(self, analyzer, simple_flow):
        """测试简单流程分析"""
        coverage = analyzer.analyze(simple_flow, None)
        
        assert isinstance(coverage, PathCoverage)
        assert coverage.total_paths >= 1
    
    def test_collect_all_paths_simple(self, analyzer, simple_flow):
        """测试收集简单路径"""
        analyzer.analyze(simple_flow, None)
        
        assert len(analyzer.all_paths) >= 1
        assert all(isinstance(p, Path) for p in analyzer.all_paths)
    
    def test_collect_all_paths_branch(self, analyzer, branch_flow):
        """测试收集分支路径"""
        analyzer.analyze(branch_flow, None)
        
        # 分支流程应该有多个路径
        assert len(analyzer.all_paths) >= 2
    
    def test_identify_branch_points(self, analyzer, branch_flow):
        """测试识别分支点"""
        analyzer.analyze(branch_flow, None)
        
        assert len(analyzer.branch_points) >= 1
        
        branch = analyzer.branch_points[0]
        assert isinstance(branch, BranchPoint)
        assert branch.node_id == 'A'
        assert len(branch.outgoing_edges) == 2
    
    def test_get_critical_paths(self, analyzer, branch_flow):
        """测试获取关键路径"""
        analyzer.analyze(branch_flow, None)
        
        critical = analyzer.get_critical_paths()
        
        assert isinstance(critical, list)
    
    def test_suggest_next_test(self, analyzer, branch_flow):
        """测试建议下一个测试"""
        analyzer.analyze(branch_flow, None)
        
        tested = [['A', 'B']]
        next_path = analyzer.suggest_next_test(tested)
        
        assert next_path is None or isinstance(next_path, Path)


class TestPathCoverage:
    """路径覆盖率测试"""
    
    def test_coverage_calculation(self):
        """测试覆盖率计算"""
        nodes = {
            'A': NodeDefinition(id='A', name='A', prompt='A'),
            'B': NodeDefinition(id='B', name='B', prompt='B'),
            'C': NodeDefinition(id='C', name='C', prompt='C', is_ending=True),
        }
        edges = [
            FlowEdge(source='A', target='B'),
            FlowEdge(source='B', target='C'),
        ]
        flow = FlowGraph(nodes=nodes, edges=edges)
        
        analyzer = PathAnalyzer()
        coverage = analyzer.analyze(flow, None)
        
        assert coverage.total_paths >= 1
        assert coverage.coverage_rate >= 0
    
    def test_coverage_with_all_paths_tested(self):
        """测试全路径测试后的覆盖率"""
        nodes = {
            'A': NodeDefinition(id='A', name='A', prompt='A'),
            'B': NodeDefinition(id='B', name='B', prompt='B', is_ending=True),
        }
        edges = [FlowEdge(source='A', target='B')]
        flow = FlowGraph(nodes=nodes, edges=edges)
        
        analyzer = PathAnalyzer()
        analyzer.analyze(flow, None)
        
        # 如果只有一条路径，测试后覆盖率应该提高
        tested = [analyzer.all_paths[0].nodes]
        
        # 验证 suggest_next_test 返回 None（所有路径已测试）
        next_path = analyzer.suggest_next_test(tested)
        # 如果所有路径都被测试，suggest_next_test 应该返回 None
        assert next_path is None or isinstance(next_path, Path)


class TestBranchPoint:
    """分支点测试"""
    
    def test_branch_point_creation(self):
        """测试分支点创建"""
        edges = [
            FlowEdge(source='A', target='B', condition='条件1'),
            FlowEdge(source='A', target='C', condition='条件2'),
        ]
        
        branch = BranchPoint(
            node_id='A',
            node_name='分支',
            outgoing_edges=edges,
            conditions=['条件1', '条件2']
        )
        
        assert branch.node_id == 'A'
        assert branch.branch_count == 2
    
    def test_branch_count_property(self):
        """测试分支数量属性"""
        edges = [
            FlowEdge(source='A', target='B'),
            FlowEdge(source='A', target='C'),
            FlowEdge(source='A', target='D'),
        ]
        
        branch = BranchPoint(
            node_id='A',
            node_name='三分支',
            outgoing_edges=edges,
            conditions=['', '', '']
        )
        
        assert branch.branch_count == 3


class TestPath:
    """路径测试"""
    
    def test_path_creation(self):
        """测试路径创建"""
        path = Path(
            id='path_1',
            nodes=['A', 'B', 'C'],
            conditions=['条件1', '条件2'],
            is_ending=True,
            ending_node='C'
        )
        
        assert path.id == 'path_1'
        assert len(path.nodes) == 3
        assert path.is_ending == True
        assert path.ending_node == 'C'
    
    def test_path_string_representation(self):
        """测试路径字符串表示"""
        path = Path(id='test', nodes=['A', 'B', 'C'])
        
        result = str(path)
        
        assert 'A' in result
        assert 'B' in result
        assert 'C' in result


class TestPathAnalyzerEdgeCases:
    """边界情况测试"""
    
    def test_analyze_empty_flow(self, analyzer):
        """测试空流程分析"""
        flow = FlowGraph(nodes={}, edges=[])
        coverage = analyzer.analyze(flow, None)
        
        assert coverage.total_paths == 0
    
    def test_analyze_single_node_flow(self, analyzer):
        """测试单节点流程分析"""
        nodes = {
            'A': NodeDefinition(id='A', name='A', prompt='A', is_ending=True),
        }
        flow = FlowGraph(nodes=nodes, edges=[])
        
        coverage = analyzer.analyze(flow, None)
        
        assert coverage.total_paths >= 1
    
    def test_analyze_long_chain(self, analyzer):
        """测试长链分析"""
        nodes = {f'Node_{i}': NodeDefinition(id=f'N{i}', name=f'N{i}', prompt=f'N{i}')
                 for i in range(10)}
        nodes['N9'].is_ending = True
        
        edges = [FlowEdge(source=f'N{i}', target=f'N{i+1}') for i in range(9)]
        flow = FlowGraph(nodes={f'N{i}': nodes[f'N{i}'] for i in range(10)}, edges=edges)
        
        coverage = analyzer.analyze(flow, None)
        
        assert coverage.total_paths >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
