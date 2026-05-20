"""
结果分析器
分析测试结果，生成报告
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime

from .scenario_runner import TestRunResult, TestRunSummary, TestResult


@dataclass
class Issue:
    """发现的问题"""
    issue_id: str
    severity: str
    category: str
    title: str
    description: str
    affected_nodes: List[str] = field(default_factory=list)
    affected_tests: List[str] = field(default_factory=list)
    suggestion: str = ""


@dataclass
class AnalysisReport:
    """分析报告"""
    timestamp: datetime
    summary: TestRunSummary
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
            "issues": [
                {
                    "id": i.issue_id,
                    "severity": i.severity,
                    "title": i.title,
                    "description": i.description,
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
    
    def analyze(self, summary: TestRunSummary) -> AnalysisReport:
        """分析测试结果"""
        issues = []
        
        issues.extend(self._analyze_failures(summary))
        issues.extend(self._analyze_errors(summary))
        recommendations = self._generate_recommendations(issues, summary)
        
        return AnalysisReport(
            timestamp=datetime.now(),
            summary=summary,
            issues=issues,
            recommendations=recommendations
        )
    
    def _analyze_failures(self, summary: TestRunSummary) -> List[Issue]:
        """分析失败测试"""
        issues = []
        failed_results = [r for r in summary.results if not r.passed]
        
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
                title=f"Node {node_id} has failures",
                description=f"Found {len(failures)} failures at this node",
                affected_nodes=[node_id],
                affected_tests=[r.test_case.id for r in failures],
                suggestion=f"Check the logic at node {node_id}"
            ))
        
        return issues
    
    def _analyze_errors(self, summary: TestRunSummary) -> List[Issue]:
        """分析错误测试"""
        issues = []
        error_results = [r for r in summary.results 
                        if r.final_result == TestResult.ERROR]
        
        error_types = defaultdict(list)
        for result in error_results:
            msg = result.error_message or "Unknown"
            error_types[msg[:50]].append(result)
        
        for msg, results in error_types.items():
            self._issue_counter += 1
            issues.append(Issue(
                issue_id=f"ISSUE-{self._issue_counter:03d}",
                severity="critical",
                category="error",
                title=f"System error: {msg[:30]}...",
                description=f"Found {len(results)} tests with this error",
                affected_tests=[r.test_case.id for r in results],
                suggestion="Check system logs and fix the issue"
            ))
        
        return issues
    
    def _generate_recommendations(self, issues: List[Issue], 
                                  summary: TestRunSummary) -> List[str]:
        """生成建议"""
        recommendations = []
        
        critical = [i for i in issues if i.severity == "critical"]
        if critical:
            recommendations.append(f"Found {len(critical)} critical issues, please fix first")
        
        if summary.pass_rate < 0.7:
            recommendations.append(f"Pass rate is low ({summary.pass_rate:.1%}), consider improving test coverage")
        
        if not recommendations:
            recommendations.append("Test results look good, consider running regression tests periodically")
        
        return recommendations
