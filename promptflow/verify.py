#!/usr/bin/env python
"""
简单验证脚本 - 直接导入并测试模块
"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def test_parser():
    """测试解析器模块"""
    print("\n📦 测试 PromptParser...")
    from promptflow.parser import PromptParser, ParsedPrompt, NodeDefinition
    
    parser = PromptParser()
    assert parser is not None
    
    prompt = """
# 角色
你是智能客服

# 节点 A
欢迎

# 节点 B
处理

# 节点 H - 结束
结束
"""
    result = parser.parse(prompt)
    assert isinstance(result, ParsedPrompt)
    print(f"  ✅ 解析器工作正常，找到 {len(result.nodes)} 个节点")
    return True


def test_flow_builder():
    """测试流程构建器模块"""
    print("\n📦 测试 FlowBuilder...")
    from promptflow.flow_builder import FlowBuilder, FlowGraph, FlowEdge
    from promptflow.parser import NodeDefinition
    
    nodes = {
        'A': NodeDefinition(id='A', name='A', prompt='A'),
        'B': NodeDefinition(id='B', name='B', prompt='B'),
        'C': NodeDefinition(id='C', name='C', prompt='C', is_ending=True),
    }
    edges = [
        FlowEdge(source='A', target='B'),
        FlowEdge(source='B', target='C'),
    ]
    
    builder = FlowBuilder()
    flow = builder.build(type('ParsedPrompt', (), {'nodes': nodes, 'raw_text': ''})())
    
    assert isinstance(flow, FlowGraph)
    print(f"  ✅ 流程构建器工作正常，构建了 {len(flow.nodes)} 个节点")
    return True


def test_path_analyzer():
    """测试路径分析器模块"""
    print("\n📦 测试 PathAnalyzer...")
    from promptflow.path_analyzer import PathAnalyzer, Path, PathCoverage
    from promptflow.flow_builder import FlowGraph, FlowEdge
    from promptflow.parser import NodeDefinition
    
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
    
    assert isinstance(coverage, PathCoverage)
    print(f"  ✅ 路径分析器工作正常，分析了 {len(analyzer.all_paths)} 条路径")
    return True


def test_test_generator():
    """测试测试生成器模块"""
    print("\n📦 测试 TestGenerator...")
    from promptflow.test_generator import TestGenerator, TestCase, TestSuite, TestType
    from promptflow.flow_builder import FlowGraph, FlowEdge
    from promptflow.parser import NodeDefinition
    from promptflow.path_analyzer import PathAnalyzer
    
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
    
    assert isinstance(suite, TestSuite)
    print(f"  ✅ 测试生成器工作正常，生成了 {len(suite.test_cases)} 个测试用例")
    return True


def test_scenario_runner():
    """测试场景运行器模块"""
    print("\n📦 测试 ScenarioRunner...")
    from promptflow.scenario_runner import ScenarioRunner, TestRunResult, TestRunSummary, TestResult
    from promptflow.test_generator import TestCase, TestSuite, TestType, TestInput
    
    def handler(node, user_input, context):
        return (f"Response to {user_input}", 'END')
    
    runner = ScenarioRunner()
    runner.set_flow_handler(handler)
    
    suite = TestSuite(
        name="Test",
        description="Test",
        test_cases=[
            TestCase(
                id='tc_0001',
                name='Test',
                description='D',
                test_type=TestType.NORMAL,
                path=['A'],
                user_inputs=[TestInput(node='A', text='Hello')]
            )
        ]
    )
    
    summary = runner.run(suite)
    assert isinstance(summary, TestRunSummary)
    print(f"  ✅ 场景运行器工作正常，运行了 {summary.total_tests} 个测试")
    return True


def test_result_analyzer():
    """测试结果分析器模块"""
    print("\n📦 测试 ResultAnalyzer...")
    from promptflow.result_analyzer import ResultAnalyzer, AnalysisReport
    from promptflow.scenario_runner import TestRunResult, TestRunSummary, TestResult
    from promptflow.test_generator import TestCase, TestType
    from datetime import datetime
    
    results = [
        TestRunResult(
            test_case=TestCase(id='tc_0001', name='T', desc='D',
                             test_type=TestType.NORMAL, path=['A']),
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
    
    assert isinstance(report, AnalysisReport)
    print(f"  ✅ 结果分析器工作正常，发现 {len(report.issues)} 个问题")
    return True


def test_tags():
    """测试标签系统模块"""
    print("\n📦 测试 TagEngine...")
    from promptflow.tags import TagEngine, TagResult, LabelDefinition
    
    engine = TagEngine()
    engine.register_label(LabelDefinition(
        id='A', name='测试', category='intent', priority=50
    ))
    engine.register_label(LabelDefinition(
        id='positive', name='正面', category='personal',
        trigger_keywords=['好的', '谢谢']
    ))
    
    engine.process_turn('好的，谢谢', turn=1)
    result = engine.get_result()
    
    assert isinstance(result, TagResult)
    print(f"  ✅ 标签系统工作正常，收集了 {len(engine._collected_tags)} 个标签")
    return True


def test_cli():
    """测试 CLI 模块"""
    print("\n📦 测试 PromptFlow CLI...")
    from promptflow.cli import PromptFlow
    
    pf = PromptFlow()
    assert pf.parser is not None
    assert pf.flow_builder is not None
    assert pf.path_analyzer is not None
    assert pf.test_generator is not None
    assert pf.runner is not None
    assert pf.result_analyzer is not None
    print("  ✅ CLI 模块工作正常")
    return True


def main():
    print("=" * 60)
    print("PromptFlow 模块验证测试")
    print("=" * 60)
    
    tests = [
        ("解析器 (PromptParser)", test_parser),
        ("流程构建器 (FlowBuilder)", test_flow_builder),
        ("路径分析器 (PathAnalyzer)", test_path_analyzer),
        ("测试生成器 (TestGenerator)", test_test_generator),
        ("场景运行器 (ScenarioRunner)", test_scenario_runner),
        ("结果分析器 (ResultAnalyzer)", test_result_analyzer),
        ("标签系统 (TagEngine)", test_tags),
        ("CLI 模块", test_cli),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  ❌ {name} 测试失败: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
