"""
PromptFlow 测试
"""
import pytest
from promptflow import (
    PromptParser,
    FlowBuilder,
    PathAnalyzer,
    TestGenerator,
    TagEngine,
    LabelDefinition,
)


class TestPromptParser:
    """测试 Prompt 解析器"""
    
    def test_parse_basic_nodes(self):
        """测试基本节点解析"""
        text = """
# 节点 A
确认身份

# 节点 B
处理请求

# 节点 C
结束
"""
        parser = PromptParser()
        result = parser.parse(text)
        
        assert len(result.nodes) == 3
        assert 'A' in result.nodes
        assert 'B' in result.nodes
        assert 'C' in result.nodes
    
    def test_extract_variables(self):
        """测试变量提取"""
        text = """
您的姓名是 {name}，日期是 {date}
"""
        parser = PromptParser()
        result = parser.parse(text)
        
        assert 'name' in result.variables
        assert 'date' in result.variables
    
    def test_parse_flow_edges(self):
        """测试流程边解析"""
        text = """
# A
A -->|是| B

# B
B --> C
"""
        parser = PromptParser()
        result = parser.parse(text)
        
        assert 'A' in result.nodes
        assert 'B' in result.nodes


class TestFlowBuilder:
    """测试流程构建器"""
    
    def test_build_simple_flow(self):
        """测试简单流程构建"""
        from promptflow.parser import ParsedPrompt, NodeDefinition
        
        nodes = {
            'A': NodeDefinition(id='A', name='Start', prompt='Start'),
            'B': NodeDefinition(id='B', name='Middle', prompt='Middle'),
            'C': NodeDefinition(id='C', name='End', prompt='End', is_ending=True),
        }
        
        parsed = ParsedPrompt(raw_text="", nodes=nodes)
        
        builder = FlowBuilder()
        flow = builder.build(parsed)
        
        assert len(flow.nodes) == 3
        assert flow.start_node_id == 'A'


class TestPathAnalyzer:
    """测试路径分析器"""
    
    def test_analyze_paths(self):
        """测试路径分析"""
        from promptflow.parser import ParsedPrompt, NodeDefinition
        from promptflow.flow_builder import FlowGraph, FlowEdge
        
        nodes = {
            'A': NodeDefinition(id='A', name='Start', prompt='Start'),
            'B': NodeDefinition(id='B', name='End', prompt='End', is_ending=True),
        }
        edges = [FlowEdge(source='A', target='B')]
        
        flow = FlowGraph(nodes=nodes, edges=edges)
        
        analyzer = PathAnalyzer()
        coverage = analyzer.analyze(flow, None)
        
        assert coverage.total_paths >= 1


class TestTagEngine:
    """测试标签引擎"""
    
    def test_register_label(self):
        """测试标签注册"""
        engine = TagEngine()
        
        engine.register_label(LabelDefinition(
            id="A",
            name="高意向",
            category="intent",
            priority=50
        ))
        
        assert "A" in engine.intent_labels
    
    def test_process_turn(self):
        """测试对话处理"""
        engine = TagEngine()
        
        engine.register_label(LabelDefinition(
            id="ask_interest",
            name="询问利息",
            category="personal",
            trigger_keywords=["利息", "利率"]
        ))
        
        engine.process_turn("你们利息多少？", node="test", turn=1)
        
        assert len(engine._collected_tags) >= 1
    
    def test_accumulate_count(self):
        """测试累加计数"""
        engine = TagEngine()
        
        engine.register_label(LabelDefinition(
            id="accept",
            name="接受邀约",
            category="personal",
            trigger_keywords=["行", "可以", "好的"],
            count_rules="accumulate"
        ))
        
        engine.process_turn("好的", turn=1)
        engine.process_turn("可以", turn=2)
        
        assert engine._counts.get("accept", 0) == 2


class TestIntegration:
    """集成测试"""
    
    def test_full_pipeline(self):
        """测试完整流程"""
        text = """
# 角色
你是客服。

## 节点 A
确认身份

## 节点 B
处理请求

## 节点 C
结束
"""
        parser = PromptParser()
        parsed = parser.parse(text)
        
        assert len(parsed.nodes) == 3
        
        builder = FlowBuilder()
        flow = builder.build(parsed)
        
        assert flow.start_node_id == 'A'
        
        analyzer = PathAnalyzer()
        analyzer.analyze(flow, parsed)
        
        assert len(analyzer.all_paths) >= 1
