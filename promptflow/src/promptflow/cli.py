"""
PromptFlow CLI
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from . import (
    PromptParser,
    FlowBuilder,
    PathAnalyzer,
    TestGenerator,
    ScenarioRunner,
    ResultAnalyzer,
    TagParser,
)


class PromptFlow:
    """PromptFlow 工作流"""
    
    def __init__(self):
        self.parser = PromptParser()
        self.flow_builder = FlowBuilder()
        self.path_analyzer = PathAnalyzer()
        self.test_generator = TestGenerator()
        self.runner = ScenarioRunner()
        self.result_analyzer = ResultAnalyzer()
        self.tag_parser = TagParser()
        
        self.parsed = None
        self.flow_graph = None
        self.test_suite = None
        self.test_summary = None
        self.analysis_report = None
    
    def load_prompt(self, path: str) -> str:
        """加载 Prompt 文件"""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def run_pipeline(self, prompt_path: str, run_tests: bool = False,
                    llm_client=None, flow_handler=None) -> dict:
        """运行完整流程"""
        prompt_text = self.load_prompt(prompt_path)
        
        # 1. 解析
        print("Parsing prompt...")
        self.parsed = self.parser.parse(prompt_text)
        print(f"  Found {len(self.parsed.nodes)} nodes")
        print(f"  Found {len(self.parsed.rules)} rules")
        print(f"  Found {len(self.parsed.variables)} variables")
        
        # 2. 构建流程
        print("\nBuilding flow...")
        self.flow_graph = self.flow_builder.build(self.parsed)
        print(f"  Flow has {len(self.flow_graph.nodes)} nodes")
        print(f"  Flow has {len(self.flow_graph.edges)} edges")
        
        # 3. 分析路径
        print("\nAnalyzing paths...")
        coverage = self.path_analyzer.analyze(self.flow_graph, self.parsed)
        print(f"  Found {len(self.path_analyzer.all_paths)} paths")
        print(f"  Found {len(self.path_analyzer.branch_points)} branch points")
        
        # 4. 生成测试
        print("\nGenerating tests...")
        self.test_generator.flow_graph = self.flow_graph
        self.test_generator.path_analyzer = self.path_analyzer
        self.test_suite = self.test_generator.generate(self.flow_graph, self.path_analyzer)
        print(f"  Generated {len(self.test_suite.test_cases)} test cases")
        
        # 5. 运行测试
        if run_tests and (llm_client or flow_handler):
            print("\nRunning tests...")
            if llm_client:
                self.runner.set_llm_client(llm_client)
            if flow_handler:
                self.runner.set_flow_handler(flow_handler)
            self.test_summary = self.runner.run(self.test_suite)
            
            # 6. 分析结果
            print("\nAnalyzing results...")
            self.analysis_report = self.result_analyzer.analyze(self.test_summary)
        
        return self._build_report()
    
    def _build_report(self) -> dict:
        """构建报告"""
        return {
            "nodes": list(self.parsed.nodes.keys()),
            "rules_count": len(self.parsed.rules),
            "variables": list(self.parsed.variables.keys()),
            "paths": {
                "total": len(self.path_analyzer.all_paths),
                "critical": [str(p) for p in self.path_analyzer.get_critical_paths()]
            },
            "test_cases_count": len(self.test_suite.test_cases) if self.test_suite else 0,
            "analysis": self.analysis_report.to_dict() if self.analysis_report else None
        }
    
    def export_tests(self, output_path: str):
        """导出测试用例"""
        if not self.test_suite:
            return
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_suite.to_dict(), f, ensure_ascii=False, indent=2)
    
    def export_report(self, output_path: str, format: str = "json"):
        """导出报告"""
        if format == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_report.to_dict() if self.analysis_report else {}, 
                         f, ensure_ascii=False, indent=2)
        elif format == "html" and self.test_summary:
            self.runner.export_results(self.test_summary, output_path, "html")


def main():
    parser = argparse.ArgumentParser(description="PromptFlow - Prompt workflow validator")
    parser.add_argument('prompt', help='Prompt file path')
    parser.add_argument('--run-tests', '-r', action='store_true', help='Run tests')
    parser.add_argument('--export', '-e', choices=['json', 'html'], help='Export format')
    parser.add_argument('--output', '-o', default='report.json', help='Output file')
    parser.add_argument('--tests', '-t', default='tests.json', help='Tests output file')
    
    args = parser.parse_args()
    
    pf = PromptFlow()
    
    try:
        result = pf.run_pipeline(args.prompt, run_tests=args.run_tests)
        
        pf.export_tests(args.tests)
        print(f"\nTests exported to: {args.tests}")
        
        if args.export:
            pf.export_report(args.output, args.export)
            print(f"Report exported to: {args.output}")
        
        print("\nDone!")
        
    except FileNotFoundError:
        print(f"Error: File not found: {args.prompt}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
