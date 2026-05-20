"""
场景运行器
执行测试用例并记录结果
"""
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum

from .test_generator import TestCase, TestSuite, TestType


class TestResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    PENDING = "pending"


@dataclass
class TurnResult:
    """单轮对话结果"""
    turn: int
    node: str
    user_input: str
    agent_response: str
    next_node: Optional[str]
    duration_ms: float
    result: TestResult = TestResult.PENDING
    error: Optional[str] = None


@dataclass
class TestRunResult:
    """测试运行结果"""
    test_case: TestCase
    start_time: datetime
    end_time: Optional[datetime] = None
    turns: List[TurnResult] = field(default_factory=list)
    final_result: TestResult = TestResult.PENDING
    expected_ending: Optional[str] = None
    actual_ending: Optional[str] = None
    error_message: Optional[str] = None
    
    @property
    def passed(self) -> bool:
        return self.final_result == TestResult.PASS
    
    def to_dict(self) -> Dict:
        return {
            "test_id": self.test_case.id,
            "test_name": self.test_case.name,
            "test_type": self.test_case.test_type.value,
            "path": self.test_case.path,
            "result": self.final_result.value,
            "expected_ending": self.expected_ending,
            "actual_ending": self.actual_ending,
            "duration_ms": self._duration_ms,
            "error": self.error_message
        }
    
    @property
    def _duration_ms(self) -> float:
        if not self.end_time:
            return 0
        return (self.end_time - self.start_time).total_seconds() * 1000


@dataclass
class TestRunSummary:
    """测试运行摘要"""
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    errors: int
    total_duration_ms: float
    results: List[TestRunResult] = field(default_factory=list)
    
    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0
        return self.passed / self.total_tests
    
    def to_dict(self) -> Dict:
        return {
            "suite_name": self.suite_name,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "pass_rate": f"{self.pass_rate:.1%}",
            "total_duration_ms": self.total_duration_ms,
            "results": [r.to_dict() for r in self.results]
        }


class ScenarioRunner:
    """
    场景运行器
    
    使用方式:
        runner = ScenarioRunner()
        runner.set_llm_client(your_llm_client)
        runner.set_flow_handler(your_flow_handler)
        summary = runner.run(test_suite)
    """
    
    def __init__(self):
        self._llm_client: Optional[Any] = None
        self._flow_handler: Optional[Callable] = None
        self.timeout_per_turn_ms: int = 30000
        self.max_turns: int = 20
        self.verbose: bool = False
    
    def set_llm_client(self, client: Any):
        """
        设置 LLM 客户端
        client 需要实现 call(prompt, context) -> str 方法
        """
        self._llm_client = client
    
    def set_flow_handler(self, handler: Callable):
        """
        设置流程处理器
        handler(current_node, user_input, context) -> (response, next_node)
        """
        self._flow_handler = handler
    
    def run(self, test_suite: TestSuite, 
            variables: Optional[Dict[str, Any]] = None) -> TestRunSummary:
        """运行测试套件"""
        variables = variables or {}
        results = []
        
        print(f"Running test suite: {test_suite.name}")
        print(f"Total test cases: {len(test_suite.test_cases)}\n")
        
        for i, test_case in enumerate(test_suite.test_cases):
            result = self._run_single_test(test_case, variables)
            results.append(result)
            
            status = "PASS" if result.passed else "FAIL" if result.final_result == TestResult.FAIL else "ERROR"
            print(f"[{i+1}/{len(test_suite.test_cases)}] {test_case.name}: {status}")
        
        summary = TestRunSummary(
            suite_name=test_suite.name,
            total_tests=len(results),
            passed=sum(1 for r in results if r.passed),
            failed=sum(1 for r in results if r.final_result == TestResult.FAIL),
            errors=sum(1 for r in results if r.final_result == TestResult.ERROR),
            total_duration_ms=sum(r._duration_ms for r in results),
            results=results
        )
        
        print(f"\n{'='*50}")
        print(f"Summary: {summary.passed}/{summary.total_tests} passed ({summary.pass_rate:.1%})")
        
        return summary
    
    def _run_single_test(self, test_case: TestCase, 
                        variables: Dict[str, Any]) -> TestRunResult:
        """运行单个测试用例"""
        result = TestRunResult(
            test_case=test_case,
            start_time=datetime.now(),
            expected_ending=test_case.expected_ending
        )
        
        try:
            for i, test_input in enumerate(test_case.user_inputs):
                if i >= self.max_turns:
                    break
                
                turn_result = self._execute_turn(
                    test_input.node,
                    test_input.text,
                    variables,
                    i + 1
                )
                result.turns.append(turn_result)
                
                if turn_result.result == TestResult.ERROR:
                    result.final_result = TestResult.ERROR
                    result.error_message = turn_result.error
                    break
                
                if turn_result.next_node:
                    result.actual_ending = turn_result.next_node
            
            if result.final_result != TestResult.ERROR:
                if result.expected_ending and result.actual_ending != result.expected_ending:
                    result.final_result = TestResult.FAIL
                else:
                    result.final_result = TestResult.PASS
        
        except Exception as e:
            result.final_result = TestResult.ERROR
            result.error_message = str(e)
        
        result.end_time = datetime.now()
        return result
    
    def _execute_turn(self, node: str, user_input: str, 
                     variables: Dict[str, Any], turn: int) -> TurnResult:
        """执行单轮对话"""
        start_time = time.time()
        
        try:
            if self._flow_handler:
                response, next_node = self._flow_handler(node, user_input, variables)
            elif self._llm_client:
                response = self._llm_client.call(
                    prompt=f"Node: {node}\nUser: {user_input}",
                    context=variables
                )
                if "|" in response:
                    response, next_node = response.split("|", 1)
                else:
                    next_node = None
            else:
                raise ValueError("No LLM client or flow handler configured")
            
            return TurnResult(
                turn=turn,
                node=node,
                user_input=user_input,
                agent_response=response,
                next_node=next_node,
                duration_ms=(time.time() - start_time) * 1000,
                result=TestResult.PASS
            )
            
        except Exception as e:
            return TurnResult(
                turn=turn,
                node=node,
                user_input=user_input,
                agent_response="",
                next_node=None,
                duration_ms=(time.time() - start_time) * 1000,
                result=TestResult.ERROR,
                error=str(e)
            )
    
    def export_results(self, summary: TestRunSummary, 
                      output_path: str, format: str = "json"):
        """导出测试结果"""
        if format == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary.to_dict(), f, ensure_ascii=False, indent=2)
        elif format == "html":
            self._export_html(summary, output_path)
    
    def _export_html(self, summary: TestRunSummary, output_path: str):
        """导出 HTML 报告"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Test Report - {summary.suite_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
    </style>
</head>
<body>
    <h1>Test Report: {summary.suite_name}</h1>
    <p>Total: {summary.total_tests} | Passed: {summary.passed} | Failed: {summary.failed}</p>
    <p>Pass Rate: {summary.pass_rate:.1%}</p>
</body>
</html>"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
