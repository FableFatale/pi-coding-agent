"""
Prompt 验证工作流 - 主入口

用法:
    python main.py --prompt path/to/prompt.md
    python main.py --prompt path/to/prompt.md --run-tests
    python main.py --prompt path/to/prompt.md --export json
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from core import (
    PromptParser,
    FlowBuilder,
    PathAnalyzer,
    TestGenerator,
    ScenarioRunner,
    ResultAnalyzer
)


class PromptValidator:
    """Prompt 验证器"""
    
    def __init__(self):
        self.parser = PromptParser()
        self.flow_builder = FlowBuilder()
        self.path_analyzer = PathAnalyzer()
        self.test_generator = TestGenerator()
        self.runner = ScenarioRunner()
        self.result_analyzer = ResultAnalyzer()
        
        # 存储中间结果
        self.parsed = None
        self.flow_graph = None
        self.test_suite = None
        self.test_summary = None
        self.analysis_report = None
    
    def load_prompt(self, path: str) -> str:
        """加载 Prompt 文件"""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def parse(self, prompt_text: str):
        """解析 Prompt"""
        print("📋 解析 Prompt...")
        self.parsed = self.parser.parse(prompt_text)
        print(f"   提取到 {len(self.parsed.nodes)} 个节点")
        print(f"   提取到 {len(self.parsed.rules)} 条规则")
        print(f"   提取到 {len(self.parsed.variables)} 个变量")
        return self.parsed
    
    def build_flow(self):
        """构建流程图"""
        if not self.parsed:
            raise ValueError("请先调用 parse()")
        
        print("🔨 构建流程图...")
        self.flow_graph = self.flow_builder.build(self.parsed)
        print(f"   流程图包含 {len(self.flow_graph.nodes)} 个节点")
        print(f"   流程图包含 {len(self.flow_graph.edges)} 条边")
        print(f"   发现 {len(self.path_analyzer.branch_points)} 个分支点")
        return self.flow_graph
    
    def analyze_paths(self):
        """分析路径"""
        if not self.flow_graph:
            raise ValueError("请先调用 build_flow()")
        
        print("🔍 分析路径...")
        coverage = self.path_analyzer.analyze(self.flow_graph, self.parsed)
        print(f"   发现 {len(self.path_analyzer.all_paths)} 条可能路径")
        print(f"   关键路径: {len(self.path_analyzer.get_critical_paths())} 条")
        return coverage
    
    def generate_tests(self):
        """生成测试用例"""
        if not self.path_analyzer.flow_graph:
            raise ValueError("请先调用 analyze_paths()")
        
        print("📝 生成测试用例...")
        self.test_generator.flow_graph = self.flow_graph
        self.test_generator.path_analyzer = self.path_analyzer
        self.test_suite = self.test_generator.generate(
            self.flow_graph, 
            self.path_analyzer
        )
        print(f"   生成 {len(self.test_suite.test_cases)} 个测试用例")
        return self.test_suite
    
    def run_tests(self, llm_client=None, flow_handler=None):
        """运行测试"""
        if not self.test_suite:
            raise ValueError("请先调用 generate_tests()")
        
        if llm_client:
            self.runner.set_llm_client(llm_client)
        if flow_handler:
            self.runner.set_flow_handler(flow_handler)
        
        print("🚀 运行测试...")
        self.test_summary = self.runner.run(self.test_suite)
        return self.test_summary
    
    def analyze_results(self):
        """分析结果"""
        if not self.test_summary:
            raise ValueError("请先调用 run_tests()")
        
        print("📊 分析结果...")
        self.analysis_report = self.result_analyzer.analyze(
            self.test_summary,
            coverage_info={
                "total_nodes": len(self.flow_graph.nodes) if self.flow_graph else 0,
                "path_coverage": len(self.test_summary.results) / 
                               max(len(self.path_analyzer.all_paths), 1),
                "branch_coverage": 0.5,  # 简化计算
                "all_nodes": list(self.flow_graph.nodes.keys()) if self.flow_graph else []
            }
        )
        
        # 打印问题摘要
        issues = self.analysis_report.issues
        if issues:
            print(f"   发现 {len(issues)} 个问题:")
            for issue in issues[:5]:
                print(f"   - [{issue.severity}] {issue.title}")
        
        return self.analysis_report
    
    def run_full_pipeline(self, prompt_path: str, 
                         llm_client=None, 
                         flow_handler=None,
                         run_tests_flag=False) -> dict:
        """
        运行完整流程
        
        Args:
            prompt_path: Prompt 文件路径
            llm_client: LLM 客户端（可选）
            flow_handler: 流程处理器（可选）
            run_tests_flag: 是否运行测试
            
        Returns:
            dict: 分析报告
        """
        # 1. 加载
        prompt_text = self.load_prompt(prompt_path)
        
        # 2. 解析
        self.parse(prompt_text)
        
        # 3. 构建流程
        self.build_flow()
        
        # 4. 分析路径
        self.analyze_paths()
        
        # 5. 生成测试
        self.generate_tests()
        
        # 6. 运行测试（可选）
        if run_tests_flag and (llm_client or flow_handler):
            self.run_tests(llm_client, flow_handler)
            self.analyze_results()
        elif run_tests_flag:
            print("⚠️ 未提供 LLM 客户端，跳过测试运行")
        
        # 返回结果
        return self.analysis_report.to_dict() if self.analysis_report else {
            "parsed": {
                "nodes": list(self.parsed.nodes.keys()),
                "rules_count": len(self.parsed.rules),
                "variables": list(self.parsed.variables.keys())
            },
            "paths": {
                "total": len(self.path_analyzer.all_paths),
                "critical": [str(p) for p in self.path_analyzer.get_critical_paths()]
            },
            "test_cases": len(self.test_suite.test_cases) if self.test_suite else 0
        }
    
    def export_report(self, output_path: str, format: str = "json"):
        """导出报告"""
        if not self.analysis_report:
            print("⚠️ 没有可导出的报告")
            return
        
        if format == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_report.to_dict(), f, ensure_ascii=False, indent=2)
        elif format == "html":
            self.runner.export_results(self.test_summary, output_path, "html")
        
        print(f"📄 报告已导出到: {output_path}")
    
    def export_test_cases(self, output_path: str):
        """导出测试用例"""
        if not self.test_suite:
            print("⚠️ 没有可导出的测试用例")
            return
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_suite.to_dict(), f, ensure_ascii=False, indent=2)
        
        print(f"📝 测试用例已导出到: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Prompt 验证工作流工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--prompt', '-p',
        required=True,
        help='Prompt 文件路径'
    )
    
    parser.add_argument(
        '--run-tests', '-r',
        action='store_true',
        help='运行测试'
    )
    
    parser.add_argument(
        '--export', '-e',
        choices=['json', 'html'],
        help='导出报告格式'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='report.json',
        help='输出文件路径'
    )
    
    parser.add_argument(
        '--tests-output',
        default='test_cases.json',
        help='测试用例输出文件路径'
    )
    
    args = parser.parse_args()
    
    # 创建验证器
    validator = PromptValidator()
    
    # 运行
    try:
        result = validator.run_full_pipeline(
            args.prompt,
            run_tests_flag=args.run_tests
        )
        
        # 导出测试用例
        validator.export_test_cases(args.tests_output)
        
        # 导出报告
        if args.export:
            validator.export_report(args.output, args.export)
        
        print("\n✅ 完成!")
        
    except FileNotFoundError:
        print(f"❌ 文件未找到: {args.prompt}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
