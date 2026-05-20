"""
PromptFlow - 通用 Prompt 工作流验证框架
"""
__version__ = "0.1.0"

from .parser import PromptParser, ParsedPrompt
from .flow_builder import FlowBuilder, FlowGraph
from .path_analyzer import PathAnalyzer, Path, PathCoverage
from .test_generator import TestGenerator, TestCase, TestSuite
from .scenario_runner import ScenarioRunner, TestRunSummary
from .result_analyzer import ResultAnalyzer, AnalysisReport
from .tags import TagEngine, TagParser, TagResult, LabelDefinition
from .cli import PromptFlow

__all__ = [
    # 版本
    "__version__",
    # 解析
    "PromptParser",
    "ParsedPrompt",
    # 流程
    "FlowBuilder",
    "FlowGraph",
    # 路径
    "PathAnalyzer",
    "Path",
    "PathCoverage",
    # 测试
    "TestGenerator",
    "TestCase",
    "TestSuite",
    # 运行
    "ScenarioRunner",
    "TestRunSummary",
    # 分析
    "ResultAnalyzer",
    "AnalysisReport",
    # 标签
    "TagEngine",
    "TagParser",
    "TagResult",
    "LabelDefinition",
    # CLI
    "PromptFlow",
]
