"""
测试 ScenarioRunner - 场景运行器测试用例
"""
import pytest
import sys
from datetime import datetime
sys.path.insert(0, 'src')

from promptflow.scenario_runner import (
    ScenarioRunner, TestRunResult, TestRunSummary, TurnResult, TestResult
)
from promptflow.test_generator import TestCase, TestSuite, TestType, TestInput


class TestScenarioRunner:
    """ScenarioRunner 测试类"""
    
    @pytest.fixture
    def runner(self):
        """创建场景运行器实例"""
        return ScenarioRunner()
    
    @pytest.fixture
    def sample_suite(self):
        """创建示例测试套件"""
        return TestSuite(
            name="Sample Suite",
            description="A sample test suite",
            test_cases=[
                TestCase(
                    id='tc_0001',
                    name='Test 1',
                    description='First test',
                    test_type=TestType.NORMAL,
                    path=['A', 'B'],
                    user_inputs=[TestInput(node='A', text='输入1')],
                    expected_ending='B'
                ),
                TestCase(
                    id='tc_0002',
                    name='Test 2',
                    description='Second test',
                    test_type=TestType.EDGE,
                    path=['A', 'C']
                ),
            ]
        )
    
    @pytest.fixture
    def mock_flow_handler(self):
        """创建模拟流程处理器"""
        def handler(node, user_input, context):
            return (f"Response to {user_input} at {node}", 'END')
        return handler
    
    def test_runner_initialization(self, runner):
        """测试运行器初始化"""
        assert runner is not None
        assert runner._llm_client is None
        assert runner._flow_handler is None
        assert runner.timeout_per_turn_ms == 30000
        assert runner.max_turns == 20
    
    def test_set_llm_client(self, runner):
        """测试设置 LLM 客户端"""
        class MockLLM:
            def call(self, prompt, context):
                return "Mock response"
        
        mock_llm = MockLLM()
        runner.set_llm_client(mock_llm)
        
        assert runner._llm_client is not None
    
    def test_set_flow_handler(self, runner, mock_flow_handler):
        """测试设置流程处理器"""
        runner.set_flow_handler(mock_flow_handler)
        
        assert runner._flow_handler is not None
    
    def test_run_requires_handler_or_client(self, runner, sample_suite):
        """测试运行需要处理器或客户端"""
        # 没有设置处理器或客户端应该失败
        with pytest.raises((ValueError, Exception)):
            runner.run(sample_suite)
    
    def test_run_with_flow_handler(self, runner, sample_suite, mock_flow_handler):
        """测试使用流程处理器运行"""
        runner.set_flow_handler(mock_flow_handler)
        
        summary = runner.run(sample_suite)
        
        assert isinstance(summary, TestRunSummary)
        assert summary.total_tests == 2
    
    def test_run_respects_max_turns(self, runner):
        """测试运行遵守最大轮数限制"""
        suite = TestSuite(
            name="Max Turns Test",
            description="Test max turns",
            test_cases=[
                TestCase(
                    id='tc_0001',
                    name='Many Turns',
                    description='Test with many turns',
                    test_type=TestType.NORMAL,
                    path=['A'],
                    user_inputs=[TestInput(node='A', text=f'输入{i}') for i in range(25)]
                )
            ]
        )
        
        def handler(node, user_input, context):
            return (f"Response", 'END')
        
        runner.set_flow_handler(handler)
        runner.max_turns = 5
        
        summary = runner.run(suite)
        
        # 应该只执行 max_turns 次
        result = summary.results[0]
        assert len(result.turns) <= 5


class TestRunSingleTest:
    """运行单个测试用例测试"""
    
    def test_run_single_test_creates_result(self):
        """测试运行单个测试创建结果"""
        runner = ScenarioRunner()
        
        def handler(node, user_input, context):
            if node == 'END':
                return ("Done", None)
            return (f"Response at {node}", 'END')
        
        runner.set_flow_handler(handler)
        
        test_case = TestCase(
            id='tc_0001',
            name='Single Test',
            description='Single test case',
            test_type=TestType.NORMAL,
            path=['A', 'B'],
            user_inputs=[TestInput(node='A', text='输入')],
            expected_ending='B'
        )
        
        result = runner._run_single_test(test_case, {})
        
        assert isinstance(result, TestRunResult)
        assert result.test_case == test_case
        assert result.start_time is not None
        assert result.end_time is not None
    
    def test_run_single_test_with_error(self):
        """测试运行单个测试处理错误"""
        runner = ScenarioRunner()
        
        def failing_handler(node, user_input, context):
            raise RuntimeError("Handler failed")
        
        runner.set_flow_handler(failing_handler)
        
        test_case = TestCase(
            id='tc_0001',
            name='Failing Test',
            description='Test that fails',
            test_type=TestType.NORMAL,
            path=['A'],
            user_inputs=[TestInput(node='A', text='输入')]
        )
        
        result = runner._run_single_test(test_case, {})
        
        assert result.final_result == TestResult.ERROR
        assert result.error_message is not None


class TestExecuteTurn:
    """执行单轮测试"""
    
    def test_execute_turn_with_handler(self):
        """测试使用处理器执行单轮"""
        runner = ScenarioRunner()
        
        def handler(node, user_input, context):
            return (f"Response to {user_input}", 'NEXT')
        
        runner.set_flow_handler(handler)
        
        result = runner._execute_turn('A', 'User input', {}, 1)
        
        assert isinstance(result, TurnResult)
        assert result.turn == 1
        assert result.node == 'A'
        assert result.user_input == 'User input'
        assert result.result == TestResult.PASS
    
    def test_execute_turn_with_llm_client(self):
        """测试使用 LLM 客户端执行单轮"""
        runner = ScenarioRunner()
        
        class MockLLM:
            def call(self, prompt, context):
                return "LLM Response"
        
        runner.set_llm_client(MockLLM())
        
        result = runner._execute_turn('A', 'User input', {}, 1)
        
        assert result.result == TestResult.PASS
        assert result.agent_response == "LLM Response"
    
    def test_execute_turn_handles_exception(self):
        """测试执行单轮处理异常"""
        runner = ScenarioRunner()
        
        def bad_handler(node, user_input, context):
            raise ValueError("Bad input")
        
        runner.set_flow_handler(bad_handler)
        
        result = runner._execute_turn('A', 'Bad input', {}, 1)
        
        assert result.result == TestResult.ERROR
        assert result.error is not None


class TestTestRunResult:
    """测试运行结果类测试"""
    
    def test_passed_property(self):
        """测试 passed 属性"""
        result = TestRunResult(
            test_case=TestCase(
                id='tc_0001', name='T', desc='D',
                test_type=TestType.NORMAL, path=['A']
            ),
            start_time=datetime.now(),
            final_result=TestResult.PASS
        )
        
        assert result.passed == True
        
        result.final_result = TestResult.FAIL
        assert result.passed == False
    
    def test_to_dict(self):
        """测试转换为字典"""
        result = TestRunResult(
            test_case=TestCase(
                id='tc_0001',
                name='Test',
                description='Description',
                test_type=TestType.NORMAL,
                path=['A', 'B']
            ),
            start_time=datetime.now(),
            end_time=datetime.now(),
            final_result=TestResult.PASS,
            expected_ending='B',
            actual_ending='B'
        )
        
        d = result.to_dict()
        
        assert d['test_id'] == 'tc_0001'
        assert d['test_name'] == 'Test'
        assert d['result'] == 'pass'


class TestTestRunSummary:
    """测试运行摘要类测试"""
    
    def test_pass_rate_calculation(self):
        """测试通过率计算"""
        summary = TestRunSummary(
            suite_name="Test",
            total_tests=10,
            passed=7,
            failed=2,
            errors=1,
            total_duration_ms=1000
        )
        
        assert summary.pass_rate == 0.7
    
    def test_pass_rate_with_zero_tests(self):
        """测试零测试的通过率"""
        summary = TestRunSummary(
            suite_name="Empty",
            total_tests=0,
            passed=0,
            failed=0,
            errors=0,
            total_duration_ms=0
        )
        
        assert summary.pass_rate == 0
    
    def test_to_dict(self):
        """测试转换为字典"""
        summary = TestRunSummary(
            suite_name="Test Suite",
            total_tests=5,
            passed=4,
            failed=1,
            errors=0,
            total_duration_ms=500,
            results=[]
        )
        
        d = summary.to_dict()
        
        assert d['suite_name'] == "Test Suite"
        assert d['total_tests'] == 5
        assert d['passed'] == 4
        assert '50.0%' in d['pass_rate'] or '50.0' in d['pass_rate']


class TestTurnResult:
    """单轮对话结果测试"""
    
    def test_turn_result_creation(self):
        """测试单轮结果创建"""
        result = TurnResult(
            turn=1,
            node='A',
            user_input='你好',
            agent_response='您好',
            next_node='B',
            duration_ms=100,
            result=TestResult.PASS
        )
        
        assert result.turn == 1
        assert result.node == 'A'
        assert result.duration_ms == 100
        assert result.result == TestResult.PASS
    
    def test_turn_result_with_error(self):
        """测试带错误的单轮结果"""
        result = TurnResult(
            turn=1,
            node='A',
            user_input='你好',
            agent_response='',
            next_node=None,
            duration_ms=50,
            result=TestResult.ERROR,
            error='Connection timeout'
        )
        
        assert result.result == TestResult.ERROR
        assert result.error == 'Connection timeout'


class TestScenarioRunnerEdgeCases:
    """边界情况测试"""
    
    def test_run_empty_suite(self, runner, mock_flow_handler):
        """测试运行空测试套件"""
        runner.set_flow_handler(mock_flow_handler)
        
        suite = TestSuite(name="Empty", description="Empty suite", test_cases=[])
        summary = runner.run(suite)
        
        assert summary.total_tests == 0
        assert summary.pass_rate == 0
    
    def test_run_with_timeout(self, runner):
        """测试超时设置"""
        runner.timeout_per_turn_ms = 1000
        
        assert runner.timeout_per_turn_ms == 1000
    
    def test_export_results_json(self, runner, tmp_path, mock_flow_handler):
        """测试导出 JSON 结果"""
        runner.set_flow_handler(mock_flow_handler)
        
        suite = TestSuite(
            name="Export Test",
            description="Test export",
            test_cases=[
                TestCase(
                    id='tc_0001',
                    name='Test',
                    description='D',
                    test_type=TestType.NORMAL,
                    path=['A']
                )
            ]
        )
        
        summary = runner.run(suite)
        
        output_file = tmp_path / "results.json"
        runner.export_results(summary, str(output_file), "json")
        
        assert output_file.exists()
    
    def _get_mock_handler(self):
        """获取模拟处理器"""
        def handler(node, user_input, context):
            return ("Response", "END")
        return handler


class TestTestResults:
    """测试结果枚举测试"""
    
    def test_all_result_types(self):
        """测试所有结果类型"""
        assert TestResult.PASS.value == 'pass'
        assert TestResult.FAIL.value == 'fail'
        assert TestResult.ERROR.value == 'error'
        assert TestResult.PENDING.value == 'pending'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
