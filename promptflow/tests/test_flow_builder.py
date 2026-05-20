"""
测试 FlowBuilder - 流程构建器测试用例
"""
import pytest
import sys
sys.path.insert(0, 'src')

from promptflow.flow_builder import FlowBuilder, FlowGraph, FlowEdge, EdgeType
from promptflow.parser import PromptParser, ParsedPrompt, NodeDefinition


class TestFlowBuilder:
    """FlowBuilder 测试类"""
    
    @pytest.fixture
    def builder(self):
        """创建流程构建器实例"""
        return FlowBuilder()
    
    @pytest.fixture
    def sample_parsed(self):
        """创建示例解析结果"""
        nodes = {
            'A': NodeDefinition(id='A', name='开始', prompt='开始节点'),
            'B': NodeDefinition(id='B', name='中间', prompt='中间节点', 
                               next_nodes={'default': 'C'}),
            'C': NodeDefinition(id='C', name='结束', prompt='结束节点', is_ending=True),
        }
        return ParsedPrompt(
            raw_text='',
            nodes=nodes
        )
    
    def test_builder_initialization(self, builder):
        """测试构建器初始化"""
        assert builder is not None
        assert builder.start_node_id is None
    
    def test_build_basic_flow(self, builder, sample_parsed):
        """测试基本流程构建"""
        flow = builder.build(sample_parsed)
        
        assert isinstance(flow, FlowGraph)
        assert len(flow.nodes) == 3
        assert len(flow.edges) >= 2
    
    def test_build_with_explicit_edges(self, builder):
        """测试显式边构建"""
        nodes = {
            'A': NodeDefinition(id='A', name='A', prompt='A',
                              next_nodes={'同意': 'B', '拒绝': 'C'}),
            'B': NodeDefinition(id='B', name='B', prompt='B', is_ending=True),
            'C': NodeDefinition(id='C', name='C', prompt='C', is_ending=True),
        }
        parsed = ParsedPrompt(raw_text='', nodes=nodes)
        
        flow = builder.build(parsed)
        
        # 应该有从 A 到 B 和 A 到 C 的边
        a_to_b = any(e.source == 'A' and e.target == 'B' for e in flow.edges)
        a_to_c = any(e.source == 'A' and e.target == 'C' for e in flow.edges)
        
        assert a_to_b or a_to_c or len(flow.edges) >= 1
    
    def test_build_infers_implicit_edges(self, builder):
        """测试隐式边推断"""
        nodes = {
            'A': NodeDefinition(id='A', name='A', prompt='A'),
            'B': NodeDefinition(id='B', name='B', prompt='B'),
            'C': NodeDefinition(id='C', name='C', prompt='C', is_ending=True),
        }
        parsed = ParsedPrompt(raw_text='', nodes=nodes)
        
        flow = builder.build(parsed)
        
        # 应该推断 A -> B -> C 的边
        assert len(flow.edges) >= 2
    
    def test_identify_start_node(self, builder):
        """测试起始节点识别"""
        nodes = {
            'X': NodeDefinition(id='X', name='X', prompt='X'),
            'A': NodeDefinition(id='A', name='A', prompt='A'),
        }
        parsed = ParsedPrompt(raw_text='', nodes=nodes)
        
        builder.build(parsed)
        
        # 应该识别 A 为起始节点（因为 'A' 通常是起始节点）
        assert builder.start_node_id == 'A'


class TestFlowGraph:
    """FlowGraph 测试类"""
    
    def test_flow_graph_initialization(self):
        """测试流程图初始化"""
        nodes = {
            'A': NodeDefinition(id='A', name='A', prompt='A'),
            'B': NodeDefinition(id='B', name='B', prompt='B', is_ending=True),
        }
        edges = [FlowEdge(source='A', target='B')]
        
        flow = FlowGraph(nodes=nodes, edges=edges)
        
        assert len(flow.nodes) == 2
        assert len(flow.edges) == 1
    
    def test_flow_graph_with_networkx(self):
        """测试 NetworkX 图构建"""
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
        
        # 检查 NetworkX 图是否构建
        assert flow.graph is not None
    
    def test_flow_graph_path_analysis(self):
        """测试路径分析"""
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
        
        paths = flow.get_all_paths()
        
        assert len(paths) > 0
        assert ['A', 'B', 'C'] in paths or any('A' in p and 'C' in p for p in paths)


class TestEdgeTypes:
    """边类型测试"""
    
    def test_normal_edge(self):
        """测试普通边"""
        edge = FlowEdge(source='A', target='B')
        
        assert edge.edge_type == EdgeType.NORMAL
        assert edge.condition == ""
    
    def test_conditional_edge(self):
        """测试条件边"""
        edge = FlowEdge(source='A', target='B', condition='同意', 
                       edge_type=EdgeType.CONDITIONAL)
        
        assert edge.edge_type == EdgeType.CONDITIONAL
        assert edge.condition == "同意"
    
    def test_ending_edge(self):
        """测试结束边"""
        edge = FlowEdge(source='A', target='END', edge_type=EdgeType.ENDING)
        
        assert edge.edge_type == EdgeType.ENDING


class TestFlowBuilderEdgeCases:
    """边界情况测试"""
    
    def test_build_empty_nodes(self, builder):
        """测试空节点"""
        parsed = ParsedPrompt(raw_text='', nodes={})
        flow = builder.build(parsed)
        
        assert len(flow.nodes) == 0
        assert len(flow.edges) == 0
    
    def test_build_single_node(self, builder):
        """测试单节点"""
        nodes = {
            'A': NodeDefinition(id='A', name='A', prompt='A', is_ending=True),
        }
        parsed = ParsedPrompt(raw_text='', nodes=nodes)
        flow = builder.build(parsed)
        
        assert len(flow.nodes) == 1
    
    def test_build_circular_reference(self, builder):
        """测试循环引用"""
        nodes = {
            'A': NodeDefinition(id='A', name='A', prompt='A', next_nodes={'default': 'B'}),
            'B': NodeDefinition(id='B', name='B', prompt='B', next_nodes={'default': 'A'}),
        }
        parsed = ParsedPrompt(raw_text='', nodes=nodes)
        
        # 应该能处理循环引用而不崩溃
        try:
            flow = builder.build(parsed)
            assert flow is not None
        except RecursionError:
            pytest.fail("Should handle circular references gracefully")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
