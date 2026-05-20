"""
测试 ResultAnalyzer - 结果分析器测试用例
"""
import pytest
import sys
from datetime import datetime
sys.path.insert(0, 'src')

from promptflow.result_analyzer import ResultAnalyzer, AnalysisReport, Issue
from promptflow.scenario_runner import (
    TestRunResult, TestRunSummary, TurnResult, TestResult
)
from promptflow.test_generator import TestCase, TestSuite, TestType


class TestResultAnalyzer:
    """ResultAnalyzer 测试类"""
    
    @pytest.fixture
    def analyzer(self):
        """创建结果分析器实例"""
        return ResultAnalyzer()
    
    @pytest.fixture
    def sample_summary(self):
        """创建示例测试摘要"""
        results = [
            TestRunResult(
                test_case=TestCase(
                    id='tc_0001', name='Pass Test', description='D',
                    test_type=TestType.NORMAL, path=['A', 'B']
                ),
                start_time=datetime.now(),
                end_time=datetime.now(),
                final_result=TestResult.PASS,
                expected_ending='B',
                actual_ending='B'
            ),
            TestRunResult(
                test_case=TestCase(
                    id='tc_0002', name='Fail Test', description='D',
                    test_type=TestType.NORMAL, path=['A', 'C']
                ),
                start_time=datetime.now(),
                end_time=datetime.now(),
                final_result=TestResult.FAIL,
                expected_ending='B',
                actual_ending='C'
            ),
            TestRunResult(
                test_case=TestCase(
                    id='tc_0003', name='Error Test', description='D',
                    test_type=TestType.EDGE, path=['A']
                ),
                start_time=datetime.now(),
                end_time=datetime.now(),
                final_result=TestResult.ERROR,
                error_message='Connection timeout'
            ),
        ]
        
        return TestRunSummary(
            suite_name="Sample Suite",
            total_tests=3,
            passed=1,
            failed=1,
            errors=1,
            total_duration_ms=500,
            results=results
        )
    
    def test_analyzer_initialization(self, analyzer):
        """测试分析器初始化"""
        assert analyzer is not None
        assert analyzer._issue_counter == 0
    
    def test_analyze_returns_report(self, analyzer, sample_summary):
        """测试分析返回报告"""
        report = analyzer.analyze(sample_summary)
        
        assert isinstance(report, AnalysisReport)
        assert report.timestamp is not None
    
    def test_analyze_generates_issues(self, analyzer, sample_summary):
        """测试分析生成问题"""
        report = analyzer.analyze(sample_summary)
        
        assert len(report.issues) > 0
    
    def test_analyze_generates_recommendations(self, analyzer, sample_summary):
        """测试分析生成建议"""
        report = analyzer.analyze(sample_summary)
        
        assert len(report.recommendations) > 0


class TestAnalyzeFailures:
    """分析失败测试"""
    
    def test_analyze_failures_detects_failures(self):
        """测试分析检测失败"""
        analyzer = ResultAnalyzer()
        
        results = [
            TestRunResult(
                test_case=TestCase(
                    id='tc_0001', name='Fail', description='D',
                    test_type=TestType.NORMAL, path=['A']
                ),
                start_time=datetime.now(),
                end_time=datetime.now(),
                final_result=TestResult.FAIL,
                expected_ending='B',
                actual_ending='C'
            )
        ]
        
        summary = TestRunSummary(
            suite_name="Fail Test",
            total_tests=1,
            passed=0,
            failed=1,
            errors=0,
            total_duration_ms=100,
            results=results
        )
        
        report = analyzer.analyze(summary)
        
        assert len(report.issues) > 0
        assert any(i.category == 'logic' for i in report.issues)
    
    def test_analyze_failures_high_severity(self):
        """测试分析失败高严重性"""
        analyzer = ResultAnalyzer()
        
        results = [
            TestRunResult(
                test_case=TestCase(
                    id=f'tc_{i:04d}', name=f'Fail {i}', description='D',
                    test_type=TestType.NORMAL, path=['A']
                ),
                start_time=datetime.now(),
                end_time=datetime.now(),
                final_result=TestResult.FAIL,
                expected_ending='B',
                actual_ending='C'
            )
            for i in range(3)
        ]
        
        summary = TestRunSummary(
            suite_name="Multiple Failures",
            total_tests=3,
            passed=0,
            failed=3,
            errors=0,
            total_duration_ms=300,
            results=results
        )
        
        report = analyzer.analyze(summary)
        
        # 应该有高严重性问题
        high_severity = [i for i in report.issues if i.severity == 'high']
        assert len(high_severity) > 0


class TestAnalyzeErrors:
    """分析错误测试"""
    
    def test_analyze_errors_detects_errors(self):
        """测试分析检测错误"""
        analyzer = ResultAnalyzer()
        
        results = [
            TestRunResult(
                test_case=TestCase(
                    id='tc_0001', name='Error', description='D',
                    test_type=TestType.NORMAL, path=['A']
                ),
                start_time=datetime.now(),
                end_time=datetime.now(),
                final_result=TestResult.ERROR,
                error_message='Connection timeout'
            )
        ]
        
        summary = TestRunSummary(
            suite_name="Error Test",
            total_tests=1,
            passed=0,
            failed=0,
            errors=1,
            total_duration_ms=100,
            results=results
        )
        
        report = analyzer.analyze(summary)
        
        # 应该有关键严重性问题
        critical = [i for i in report.issues if i.severity == 'critical']
        assert len(critical) > 0
    
    def test_analyze_errors_groups_same_errors(self):
        """测试分析分组相同错误"""
        analyzer = ResultAnalyzer()
        
        results = [
            TestRunResult(
                test_case=TestCase(
                    id=f'tc_{i:04d}', name=f'Error {i}', description='D',
                    test_type=TestType.NORMAL, path=['A']
                ),
                start_time=datetime.now(),
                end_time=datetime.now(),
                final_result=TestResult.ERROR,
                error_message='Same error message'
            )
            for i in range(3)
        ]
        
        summary = TestRunSummary(
            suite_name="Same Error Test",
            total_tests=3,
            passed=0,
            failed=0,
            errors=3,
            total_duration_ms=300,
            results=results
        )
        
        report = analyzer.analyze(summary)
        
        # 应该检测到系统错误
        error_issues = [i for i in report.issues if i.category == 'error']
        assert len(error_issues) > 0


class TestGenerateRecommendations:
    """生成建议测试"""
    
    def test_recommendations_for_critical_issues(self):
        """测试关键问题建议"""
        analyzer = ResultAnalyzer()
        
        results = [
            TestRunResult(
                test_case=TestCase(
                    id='tc_0001', name='Error', description='D',
                    test_type=TestType.NORMAL, path=['A']
                ),
                start_time=datetime.now(),
                end_time=datetime.now(),
                final_result=TestResult.ERROR,
                error_message='Critical error'
            )
        ]
        
        summary = TestRunSummary(
            suite_name="Critical",
            total_tests=1,
            passed=0,
            failed=0,
            errors=1,
            total_duration_ms=100,
            results=results
        )
        
        report = analyzer.analyze(summary)
        
        assert any('critical' in r.lower() for r in report.recommendations)
    
    def test_recommendations_for_low_pass_rate(self):
        """测试低通过率建议"""
        analyzer = ResultAnalyzer()
        
        results = [
            TestRunResult(
                test_case=TestCase(
                    id=f'tc_{i:04d}', name=f'Test {i}', description='D',
                    test_type=TestType.NORMAL, path=['A']
                ),
                start_time=datetime.now(),
                end_time=datetime.now(),
                final_result=TestResult.FAIL if i < 7 else TestResult.PASS
            )
            for i in range(10)
        ]
        
        summary = TestRunSummary(
            suite_name="Low Pass",
            total_tests=10,
            passed=3,
            failed=7,
            errors=0,
            total_duration_ms=1000,
            results=results
        )
        
        report = analyzer.analyze(summary)
        
        # 通过率 30% 应该低于 70%
        assert summary.pass_rate < 0.7
        assert any('coverage' in r.lower() or 'low' in r.lower() for r in report.recommendations)
    
    def test_recommendations_for_good_results(self):
        """测试良好结果建议"""
        analyzer = ResultAnalyzer()
        
        results = [
            TestRunResult(
                test_case=TestCase(
                    id=f'tc_{i:04d}', name=f'Pass {i}', description='D',
                    test_type=TestType.NORMAL, path=['A']
                ),
                start_time=datetime.now(),
                end_time=datetime.now(),
                final_result=TestResult.PASS
            )
            for i in range(5)
        ]
        
        summary = TestRunSummary(
            suite_name="Good",
            total_tests=5,
            passed=5,
            failed=0,
            errors=0,
            total_duration_ms=500,
            results=results
        )
        
        report = analyzer.analyze(summary)
        
        assert len(report.issues) == 0


class TestAnalysisReport:
    """分析报告测试"""
    
    def test_report_to_dict(self):
        """测试报告转换为字典"""
        results = [
            TestRunResult(
                test_case=TestCase(
                    id='tc_0001', name='Test', description='D',
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
        
        report = AnalysisReport(
            timestamp=datetime.now(),
            summary=summary,
            issues=[],
            recommendations=['Good job']
        )
        
        d = report.to_dict()
        
        assert 'timestamp' in d
        assert 'summary' in d
        assert 'issues' in d
        assert 'recommendations' in d
        assert d['summary']['passed'] == 1


class TestIssue:
    """问题类测试"""
    
    def test_issue_creation(self):
        """测试问题创建"""
        issue = Issue(
            issue_id='ISSUE-001',
            severity='high',
            category='logic',
            title='Test failure',
            description='Test failed at node A',
            affected_nodes=['A'],
            affected_tests=['tc_0001'],
            suggestion='Check the logic'
        )
        
        assert issue.issue_id == 'ISSUE-001'
        assert issue.severity == 'high'
        assert issue.category == 'logic'
        assert 'A' in issue.affected_nodes
    
    def test_issue_to_dict(self):
        """测试问题转换为字典"""
        issue = Issue(
            issue_id='ISSUE-001',
            severity='high',
            category='logic',
            title='Test failure',
            description='Test failed'
        )
        
        d = issue.__dict__
        
        assert d['issue_id'] == 'ISSUE-001'
        assert d['severity'] == 'high'


class TestResultAnalyzerEdgeCases:
    """边界情况测试"""
    
    def test_analyze_empty_summary(self, analyzer):
        """测试分析空摘要"""
        summary = TestRunSummary(
            suite_name="Empty",
            total_tests=0,
            passed=0,
            failed=0,
            errors=0,
            total_duration_ms=0,
            results=[]
        )
        
        report = analyzer.analyze(summary)
        
        assert report is not None
        assert len(report.issues) == 0
    
    def test_analyze_all_pass(self, analyzer):
        """测试分析全通过"""
        results = [
            TestRunResult(
                test_case=TestCase(
                    id=f'tc_{i:04d}', name=f'Pass {i}', description='D',
                    test_type=TestType.NORMAL, path=['A']
                ),
                start_time=datetime.now(),
                end_time=datetime.now(),
                final_result=TestResult.PASS
            )
            for i in range(5)
        ]
        
        summary = TestRunSummary(
            suite_name="All Pass",
            total_tests=5,
            passed=5,
            failed=0,
            errors=0,
            total_duration_ms=500,
            results=results
        )
        
        report = analyzer.analyze(summary)
        
        assert len(report.issues) == 0
        assert len(report.recommendations) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
