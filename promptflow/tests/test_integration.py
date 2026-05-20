"""
集成测试 - 完整流程测试
"""
import pytest
import sys
sys.path.insert(0, 'src')

from promptflow import (
    PromptParser, FlowBuilder, PathAnalyzer, 
    TestGenerator, ScenarioRunner, ResultAnalyzer
)


class TestEndToEndPipeline:
    """端到端流程测试"""
    
    @pytest.fixture
    def sample_prompt_text(self):
        """示例 Prompt 文本"""
        return """
# 角色
你是智能客服助手小Q。

## 总目标
高效准确地解答用户问题。

# 节点 A - 欢迎
您好，我是小Q，请问有什么可以帮您？

> 用户：你好
> 小Q：您好

节点prompt：简单问候

# 节点 B - 问题确认
请问具体是什么问题呢？

> 用户：想咨询产品
> 小Q：好的，请问是哪方面的问题？

节点prompt：确认用户问题

# 节点 C - 问题解答
我来帮您解答。

节点prompt：提供解答

# 节点 H - 问题解决
很高兴帮到您，还有其他问题吗？

节点prompt：确认问题解决
结束节点

# 节点 I - 转人工
您的问题需要人工处理，请稍等。

节点prompt：转接人工
结束节点

## 全流程通用全局执行规则
1. 保持友好态度
2. 及时响应
3. 复杂问题转人工
"""
    
    @pytest.fixture
    def mock_flow_handler(self):
        """模拟流程处理器"""
        def handler(node, user_input, context):
            if node == 'A':
                return ('您好，请问有什么可以帮您？', 'B')
            elif node == 'B':
                return ('请问具体是什么问题？', 'C')
            elif node == 'C':
                return ('我来帮您解答。', 'H')
            elif node == 'H':
                return ('还有其他问题吗？', None)
            elif node == 'I':
                return ('正在转接...', None)
            return ('结束', None)
        return handler
    
    def test_complete_pipeline(self, sample_prompt_text, mock_flow_handler):
        """测试完整流程"""
        # 1. 解析
        parser = PromptParser()
        parsed = parser.parse(sample_prompt_text)
        
        assert len(parsed.nodes) >= 4
        assert parsed.role == "智能客服助手小Q"
        
        # 2. 构建流程
        builder = FlowBuilder()
        flow = builder.build(parsed)
        
        assert len(flow.nodes) >= 4
        
        # 3. 分析路径
        path_analyzer = PathAnalyzer()
        coverage = path_analyzer.analyze(flow, parsed)
        
        assert coverage.total_paths >= 1
        assert len(path_analyzer.all_paths) >= 1
        
        # 4. 生成测试
        test_generator = TestGenerator()
        test_suite = test_generator.generate(flow, path_analyzer)
        
        assert len(test_suite.test_cases) > 0
        assert isinstance(test_suite.metadata, dict)
        
        # 5. 运行测试
        runner = ScenarioRunner()
        runner.set_flow_handler(mock_flow_handler)
        summary = runner.run(test_suite)
        
        assert summary.total_tests > 0
        assert isinstance(summary.results, list)
        
        # 6. 分析结果
        analyzer = ResultAnalyzer()
        report = analyzer.analyze(summary)
        
        assert report is not None
        assert hasattr(report, 'issues')
        assert hasattr(report, 'recommendations')


class TestPromptFlowClass:
    """PromptFlow 类测试"""
    
    def test_prompt_flow_workflow(self):
        """测试 PromptFlow 工作流类"""
        from promptflow.cli import PromptFlow
        
        pf = PromptFlow()
        
        assert pf.parser is not None
        assert pf.flow_builder is not None
        assert pf.path_analyzer is not None
        assert pf.test_generator is not None
        assert pf.runner is not None
        assert pf.result_analyzer is not None


class TestComponentIntegration:
    """组件集成测试"""
    
    def test_parser_to_flow_builder(self):
        """测试解析器到流程构建器的集成"""
        prompt = """
# 角色
测试角色

# 节点 A
开始

# 节点 B
结束
结束节点
"""
        
        parser = PromptParser()
        parsed = parser.parse(prompt)
        
        builder = FlowBuilder()
        flow = builder.build(parsed)
        
        assert len(flow.nodes) == len(parsed.nodes)
    
    def test_flow_to_path_analyzer(self):
        """测试流程到路径分析器的集成"""
        from promptflow.parser import NodeDefinition
        from promptflow.flow_builder import FlowGraph, FlowEdge
        
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
    
    def test_analyzer_to_generator(self):
        """测试分析器到生成器的集成"""
        from promptflow.parser import NodeDefinition
        from promptflow.flow_builder import FlowGraph, FlowEdge
        
        nodes = {
            'A': NodeDefinition(id='A', name='A', prompt='A'),
            'B': NodeDefinition(id='B', name='B', prompt='B', is_ending=True),
        }
        edges = [FlowEdge(source='A', target='B')]
        flow = FlowGraph(nodes=nodes, edges=edges)
        
        analyzer = PathAnalyzer()
        analyzer.analyze(flow, None)
        
        generator = TestGenerator()
        suite = generator.generate(flow, analyzer)
        
        assert len(suite.test_cases) > 0
    
    def test_generator_to_runner(self):
        """测试生成器到运行器的集成"""
        from promptflow.parser import NodeDefinition
        from promptflow.flow_builder import FlowGraph, FlowEdge
        from promptflow.test_generator import TestCase, TestSuite, TestType, TestInput
        
        # 创建测试套件
        suite = TestSuite(
            name="Integration Test",
            description="Test generator to runner",
            test_cases=[
                TestCase(
                    id='tc_0001',
                    name='Test 1',
                    description='Integration test',
                    test_type=TestType.NORMAL,
                    path=['A'],
                    user_inputs=[TestInput(node='A', text='输入')]
                )
            ]
        )
        
        def handler(node, user_input, context):
            return ('响应', 'END')
        
        runner = ScenarioRunner()
        runner.set_flow_handler(handler)
        summary = runner.run(suite)
        
        assert summary.total_tests == 1
    
    def test_runner_to_analyzer(self):
        """测试运行器到分析器的集成"""
        from promptflow.test_generator import TestCase, TestSuite, TestType
        from promptflow.scenario_runner import TestRunResult, TestRunSummary, TestResult
        from datetime import datetime
        
        results = [
            TestRunResult(
                test_case=TestCase(
                    id='tc_0001', name='Pass', description='D',
                    test_type=TestType.NORMAL, path=['A']
                ),
                start_time=datetime.now(),
                end_time=datetime.now(),
                final_result=TestResult.PASS
            )
        ]
        
        summary = TestRunSummary(
            suite_name="Test",
            total_tests=1,
            passed=1,
            failed=0,
            errors=0,
            total_duration_ms=100,
            results=results
        )
        
        analyzer = ResultAnalyzer()
        report = analyzer.analyze(summary)
        
        assert len(report.issues) == 0


class TestEdgeCasesIntegration:
    """边界情况集成测试"""
    
    def test_minimal_prompt(self):
        """测试最小 Prompt"""
        prompt = """
# 角色
测试

# 节点 A
开始
"""
        
        parser = PromptParser()
        parsed = parser.parse(prompt)
        
        assert len(parsed.nodes) >= 1
        
        builder = FlowBuilder()
        flow = builder.build(parsed)
        
        assert flow is not None
    
    def test_complex_branching_flow(self):
        """测试复杂分支流程"""
        from promptflow.parser import NodeDefinition
        from promptflow.flow_builder import FlowGraph, FlowEdge
        
        nodes = {
            'A': NodeDefinition(id='A', name='A', prompt='A',
                              next_nodes={'是': 'B', '否': 'C'}),
            'B': NodeDefinition(id='B', name='B', prompt='B',
                              next_nodes={'继续': 'D', '结束': 'E'}),
            'C': NodeDefinition(id='C', name='C', prompt='C',
                              next_nodes={'返回': 'A', '结束': 'E'}),
            'D': NodeDefinition(id='D', name='D', prompt='D', is_ending=True),
            'E': NodeDefinition(id='E', name='E', prompt='E', is_ending=True),
        }
        edges = [
            FlowEdge(source='A', target='B', condition='是'),
            FlowEdge(source='A', target='C', condition='否'),
            FlowEdge(source='B', target='D', condition='继续'),
            FlowEdge(source='B', target='E', condition='结束'),
            FlowEdge(source='C', target='A', condition='返回'),
            FlowEdge(source='C', target='E', condition='结束'),
        ]
        flow = FlowGraph(nodes=nodes, edges=edges)
        
        analyzer = PathAnalyzer()
        coverage = analyzer.analyze(flow, None)
        
        # 复杂流程应该有多个路径
        assert coverage.total_paths >= 1
        assert len(analyzer.branch_points) >= 1
        
        generator = TestGenerator()
        suite = generator.generate(flow, analyzer)
        
        assert len(suite.test_cases) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
