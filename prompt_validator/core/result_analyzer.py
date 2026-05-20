"""
结果分析器
分析测试结果，生成报告
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from datetime import datetime

from .scenario_runner import TestRunResult, TestRunSummary, TestResult
from .path_analyzer import Path


@dataclass
class Issue:
    """发现的问题"""
    issue_id: str
    severity: str  # critical, high, medium, low
    category: str  # flow, logic, response, coverage
    title: str
    description: str
    affected_nodes: List[str] = field(default_factory=list)
    affected_tests: List[str] = field(default_factory=list)
    suggestion: str = ""


@dataclass
class CoverageReport:
    """覆盖率报告"""
    path_coverage: float
    node_coverage: float
    branch_coverage: float
    uncovered_paths: List[Path] = field(default_factory=list)
    uncovered_nodes: List[str] = field(default_factory=list)
    low_coverage_branches: Dict[str, float] = field(default_factory=dict)


@dataclass
class AnalysisReport:
    """分析报告"""
    timestamp: datetime
    summary: TestRunSummary
    coverage: Optional[CoverageReport]
    issues: List[Issue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "summary": {
                "total": self.summary.total_tests,
                "passed": self.summary.passed,
                "failed": self.summary.failed,
                "errors": self.summary.errors,
                "pass_rate": self.summary.pass_rate
            },
            "coverage": {
                "path_coverage": self.coverage.path_coverage if self.coverage else 0,
                "node_coverage": self.coverage.node_coverage if self.coverage else 0,
                "branch_coverage": self.coverage.branch_coverage if self.coverage else 0,
            } if self.coverage else {},
            "issues": [
                {
                    "id": i.issue_id,
                    "severity": i.severity,
                    "category": i.category,
                    "title": i.title,
                    "description": i.description,
                    "affected_nodes": i.affected_nodes,
                    "suggestion": i.suggestion
                }
                for i in self.issues
            ],
            "recommendations": self.recommendations
        }


class ResultAnalyzer:
    """结果分析器"""
    
    def __init__(self):
        self._issue_counter = 0
    
    def analyze(self, summary: TestRunSummary, 
                coverage_info: Optional[Dict] = None) -> AnalysisReport:
        """
        分析测试结果
        
        Args:
            summary: 测试运行摘要
            coverage_info: 覆盖率信息（可选）
            
        Returns:
            AnalysisReport: 分析报告
        """
        issues = []
        
        # 1. 分析失败测试
        issues.extend(self._analyze_failures(summary))
        
        # 2. 分析错误测试
        issues.extend(self._analyze_errors(summary))
        
        # 3. 分析覆盖率
        coverage = self._analyze_coverage(summary, coverage_info) if coverage_info else None
        
        # 4. 生成建议
        recommendations = self._generate_recommendations(issues, coverage)
        
        return AnalysisReport(
            timestamp=datetime.now(),
            summary=summary,
            coverage=coverage,
            issues=issues,
            recommendations=recommendations
        )
    
    def _analyze_failures(self, summary: TestRunSummary) -> List[Issue]:
        """分析失败测试"""
        issues = []
        failed_results = [r for r in summary.results if not r.passed]
        
        # 按节点分组
        node_failures = defaultdict(list)
        for result in failed_results:
            for turn in result.turns:
                if turn.result == TestResult.FAIL:
                    node_failures[turn.node].append(result)
        
        for node_id, failures in node_failures.items():
            self._issue_counter += 1
            issues.append(Issue(
                issue_id=f"ISSUE-{self._issue_counter:03d}",
                severity="high" if len(failures) > 2 else "medium",
                category="logic",
                title=f"节点 {node_id} 逻辑问题",
                description=f"该节点在 {len(failures)} 个测试中出现失败",
                affected_nodes=[node_id],
                affected_tests=[r.test_case.id for r in failures],
                suggestion=f"检查节点 {node_id} 的处理逻辑和分支条件"
            ))
        
        return issues
    
    def _analyze_errors(self, summary: TestRunSummary) -> List[Issue]:
        """分析错误测试"""
        issues = []
        error_results = [r for r in summary.results 
                        if r.final_result == TestResult.ERROR]
        
        # 按错误类型分组
        error_types = defaultdict(list)
        for result in error_results:
            error_msg = result.error_message or "Unknown"
            error_types[error_msg[:50]].append(result)
        
        for error_msg, results in error_types.items():
            self._issue_counter += 1
            issues.append(Issue(
                issue_id=f"ISSUE-{self._issue_counter:03d}",
                severity="critical",
                category="error",
                title=f"系统错误: {error_msg[:30]}...",
                description=f"发现 {len(results)} 个测试出现同类错误",
                affected_tests=[r.test_case.id for r in results],
                suggestion="检查错误日志，修复系统问题"
            ))
        
        return issues
    
    def _analyze_coverage(self, summary: TestRunSummary,
                          coverage_info: Dict) -> CoverageReport:
        """分析覆盖率"""
        # 获取已测试的路径
        tested_paths = [r.test_case.path for r in summary.results]
        tested_nodes = set()
        for path in tested_paths:
            tested_nodes.update(path)
        
        # 计算节点覆盖率
        total_nodes = coverage_info.get("total_nodes", 1)
        coverage_report = CoverageReport(
            path_coverage=coverage_info.get("path_coverage", 0),
            node_coverage=len(tested_nodes) / total_nodes if total_nodes > 0 else 0,
            branch_coverage=coverage_info.get("branch_coverage", 0),
            uncovered_nodes=list(set(coverage_info.get("all_nodes", [])) - tested_nodes)
        )
        
        # 检查低覆盖率分支
        branch_coverage = coverage_info.get("branch_coverage", {})
        coverage_report.low_coverage_branches = {
            node: rate for node, rate in branch_coverage.items()
            if rate < 0.5
        }
        
        # 添加覆盖率问题
        if coverage_report.node_coverage < 0.8:
            self._issue_counter += 1
            
        return coverage_report
    
    def _generate_recommendations(self, issues: List[Issue],
                                  coverage: Optional[CoverageReport]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 基于问题生成建议
        critical_issues = [i for i in issues if i.severity == "critical"]
        if critical_issues:
            recommendations.append(
                f"⚠️ 发现 {len(critical_issues)} 个严重问题，请优先处理"
            )
        
        # 基于覆盖率生成建议
        if coverage:
            if coverage.node_coverage < 0.7:
                recommendations.append(
                    f"📊 节点覆盖率仅 {coverage.node_coverage:.1%}，"
                    f"建议补充以下节点的测试: {', '.join(coverage.uncovered_nodes[:5])}"
                )
            
            if coverage.path_coverage < 0.5:
                recommendations.append(
                    f"📊 路径覆盖率仅 {coverage.path_coverage:.1%}，"
                    "建议增加边界场景测试用例"
                )
            
            low_branches = coverage.low_coverage_branches
            if low_branches:
                recommendations.append(
                    f"📊 以下分支覆盖率较低: {', '.join(low_branches.keys())}"
                )
        
        # 通用建议
        if not recommendations:
            recommendations.append("✅ 测试结果良好，建议持续运行回归测试")
        
        return recommendations
    
    def generate_focus_areas(self, issues: List[Issue]) -> List[str]:
        """
        生成需要重点关注的领域
        
        Returns:
            List[str]: 节点ID列表
        """
        focus_nodes = []
        
        for issue in issues:
            if issue.severity in ["critical", "high"]:
                focus_nodes.extend(issue.affected_nodes)
        
        return list(set(focus_nodes))
    
    def suggest_next_tests(self, summary: TestRunSummary,
                          uncovered_paths: List[Path]) -> List[str]:
        """
        建议下一个要测试的场景
        
        Returns:
            List[str]: 测试用例名称列表
        """
        # 获取已测试的路径
        tested_paths = set(tuple(r.test_case.path) for r in summary.results)
        
        # 找出未覆盖的关键路径
        suggestions = []
        for path in uncovered_paths[:5]:
            if tuple(path.nodes) not in tested_paths:
                suggestions.append(f"建议测试: {'->'.join(path.nodes)}")
        
        return suggestions
    
    def compare_runs(self, run1: TestRunSummary, 
                    run2: TestRunSummary) -> Dict:
        """
        比较两次测试运行
        
        Returns:
            Dict: 差异报告
        """
        return {
            "run1": {
                "total": run1.total_tests,
                "passed": run1.passed,
                "pass_rate": run1.pass_rate
            },
            "run2": {
                "total": run2.total_tests,
                "passed": run2.passed,
                "pass_rate": run2.pass_rate
            },
            "delta": {
                "pass_rate_change": run2.pass_rate - run1.pass_rate,
                "new_failures": self._find_new_failures(run1, run2),
                "fixed_tests": self._find_fixed_tests(run1, run2)
            }
        }
    
    def _find_new_failures(self, old: TestRunSummary, 
                          new: TestRunSummary) -> List[str]:
        """找出新失败的测试"""
        old_passed = {r.test_case.id for r in old.results if r.passed}
        new_failed_ids = [r.test_case.id for r in new.results if not r.passed]
        return [tid for tid in new_failed_ids if tid in old_passed]
    
    def _find_fixed_tests(self, old: TestRunSummary, 
                         new: TestRunSummary) -> List[str]:
        """找出修复的测试"""
        old_failed = {r.test_case.id for r in old.results if not r.passed}
        new_passed_ids = [r.test_case.id for r in new.results if r.passed]
        return [tid for tid in new_passed_ids if tid in old_failed]
