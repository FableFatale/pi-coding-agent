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
    """测试结果"""
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
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def passed(self) -> bool:
        return self.final_result == TestResult.PASS
    
    @property
    def duration_ms(self) -> float:
        if not self.end_time:
            return 0
        return (self.end_time - self.start_time).total_seconds() * 1000
    
    def to_dict(self) -> Dict:
        return {
            "test_id": self.test_case.id,
            "test_name": self.test_case.name,
            "test_type": self.test_case.test_type.value,
            "path": self.test_case.path,
            "result": self.final_result.value,
            "expected_ending": self.expected_ending,
            "actual_ending": self.actual_ending,
            "turns_count": len(self.turns),
            "duration_ms": self.duration_ms,
            "error": self.error_message,
            "turns": [
                {
                    "turn": t.turn,
                    "node": t.node,
                    "user_input": t.user_input,
                    "agent_response": t.agent_response[:100] + "..." if len(t.agent_response) > 100 else t.agent_response,
                    "next_node": t.next_node,
                    "result": t.result.value
                }
                for t in self.turns
            ]
        }


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
        self._output_handler: Optional[Callable] = None
        
        # 配置
        self.timeout_per_turn_ms: int = 30000
        self.max_turns: int = 20
        self.verbose: bool = False
    
    def set_llm_client(self, client: Any):
        """
        设置 LLM 客户端
        
        Args:
            client: 实现 call(prompt, context) -> str 的客户端
        """
        self._llm_client = client
    
    def set_flow_handler(self, handler: Callable):
        """
        设置流程处理器
        
        Args:
            handler: 函数(current_node, user_input, context) -> (response, next_node)
        """
        self._flow_handler = handler
    
    def set_output_handler(self, handler: Callable):
        """
        设置输出处理器（可选）
        
        用于自定义响应验证或格式化
        """
        self._output_handler = handler
    
    def run(self, test_suite: TestSuite, 
            variables: Optional[Dict[str, Any]] = None) -> TestRunSummary:
        """
        运行测试套件
        
        Args:
            test_suite: 测试套件
            variables: 测试变量（替换 prompt 中的占位符）
            
        Returns:
            TestRunSummary: 运行结果摘要
        """
        variables = variables or {}
        results = []
        
        print(f"🚀 开始运行测试套件: {test_suite.name}")
        print(f"   共 {len(test_suite.test_cases)} 个测试用例\n")
        
        for i, test_case in enumerate(test_suite.test_cases):
            result = self._run_single_test(test_case, variables)
            results.append(result)
            
            # 打印进度
            status_icon = "✅" if result.passed else "❌" if result.final_result == TestResult.FAIL else "⚠️"
            print(f"   {status_icon} [{i+1}/{len(test_suite.test_cases)}] {test_case.name}")
            
            if self.verbose and not result.passed:
                print(f"      预期结束: {result.expected_ending}, 实际: {result.actual_ending}")
        
        # 生成摘要
        summary = TestRunSummary(
            suite_name=test_suite.name,
            total_tests=len(results),
            passed=sum(1 for r in results if r.passed),
            failed=sum(1 for r in results if r.final_result == TestResult.FAIL),
            errors=sum(1 for r in results if r.final_result == TestResult.ERROR),
            total_duration_ms=sum(r.duration_ms for r in results),
            results=results
        )
        
        # 打印总结
        print(f"\n📊 测试完成:")
        print(f"   通过: {summary.passed}/{summary.total_tests} ({summary.pass_rate:.1%})")
        print(f"   失败: {summary.failed}")
        print(f"   错误: {summary.errors}")
        print(f"   总耗时: {summary.total_duration_ms:.0f}ms")
        
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
            # 执行每一轮对话
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
                
                # 检查是否有错误
                if turn_result.result == TestResult.ERROR:
                    result.final_result = TestResult.ERROR
                    result.error_message = turn_result.error
                    break
                
                # 检查节点是否匹配预期
                if test_case.path and i < len(test_case.path):
                    expected_node = test_case.path[i]
                    if turn_result.node != expected_node:
                        turn_result.result = TestResult.FAIL
                        turn_result.error = f"Expected node {expected_node}, got {turn_result.node}"
                
                # 更新当前节点
                if turn_result.next_node:
                    result.actual_ending = turn_result.next_node
            
            # 检查最终结果
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
                # 使用流程处理器
                response, next_node = self._flow_handler(node, user_input, variables)
            elif self._llm_client:
                # 使用 LLM 客户端
                response = self._llm_client.call(
                    prompt=f"Node: {node}\nUser: {user_input}",
                    context=variables
                )
                # 假设响应格式为 "response|next_node"
                if "|" in response:
                    response, next_node = response.split("|", 1)
                else:
                    next_node = None
            else:
                raise ValueError("No LLM client or flow handler configured")
            
            duration = (time.time() - start_time) * 1000
            
            return TurnResult(
                turn=turn,
                node=node,
                user_input=user_input,
                agent_response=response,
                next_node=next_node,
                duration_ms=duration,
                result=TestResult.PASS
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TurnResult(
                turn=turn,
                node=node,
                user_input=user_input,
                agent_response="",
                next_node=None,
                duration_ms=duration,
                result=TestResult.ERROR,
                error=str(e)
            )
    
    def export_results(self, summary: TestRunSummary, 
                      output_path: str, format: str = "json"):
        """
        导出测试结果
        
        Args:
            summary: 测试运行摘要
            output_path: 输出路径
            format: 输出格式 (json, html, csv)
        """
        if format == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary.to_dict(), f, ensure_ascii=False, indent=2)
        elif format == "html":
            self._export_html(summary, output_path)
        elif format == "csv":
            self._export_csv(summary, output_path)
    
    def _export_html(self, summary: TestRunSummary, output_path: str):
        """导出 HTML 报告"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Test Report - {summary.suite_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        .test-case {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; }}
        .turn {{ margin-left: 20px; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <h1>Test Report: {summary.suite_name}</h1>
    <div class="summary">
        <p>Total: {summary.total_tests} | 
           <span class="pass">Passed: {summary.passed}</span> | 
           <span class="fail">Failed: {summary.failed}</span> |
           Errors: {summary.errors}</p>
        <p>Pass Rate: {summary.pass_rate:.1%}</p>
    </div>
    <h2>Test Cases</h2>
    {''.join(f'''
    <div class="test-case">
        <h3>{tc.test_case.name} - <span class="{"pass" if tc.passed else "fail"}">{tc.final_result.value}</span></h3>
        <p>{tc.test_case.description}</p>
        <p>Path: {" -> ".join(tc.test_case.path)}</p>
        <p>Expected: {tc.expected_ending} | Actual: {tc.actual_ending}</p>
    </div>
    ''' for tc in summary.results)}
</body>
</html>
"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def _export_csv(self, summary: TestRunSummary, output_path: str):
        """导出 CSV 报告"""
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Test ID', 'Name', 'Type', 'Path', 'Expected', 'Actual', 'Result'])
            
            for tc in summary.results:
                writer.writerow([
                    tc.test_case.id,
                    tc.test_case.name,
                    tc.test_case.test_type.value,
                    ' -> '.join(tc.test_case.path),
                    tc.expected_ending,
                    tc.actual_ending,
                    tc.final_result.value
                ])
