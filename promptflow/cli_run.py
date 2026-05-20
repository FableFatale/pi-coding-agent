#!/usr/bin/env python
"""
PromptFlow CLI - 完整版
"""
import argparse
import json
import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from promptflow import (
    PromptParser, FlowBuilder, PathAnalyzer,
    TestGenerator, ScenarioRunner, ResultAnalyzer
)


def main():
    parser = argparse.ArgumentParser(
        description="PromptFlow - Prompt workflow validator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('prompt', nargs='?', help='Prompt file path')
    parser.add_argument('--run-tests', '-r', action='store_true', help='Run tests')
    parser.add_argument('--export', '-e', choices=['json', 'html'], help='Export format')
    parser.add_argument('--output', '-o', default='report.html', help='Output file')
    parser.add_argument('--tests', '-t', default='tests.json', help='Tests output file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
    
    args = parser.parse_args()
    
    # 如果没有提供文件，使用示例
    if not args.prompt:
        args.prompt = str(Path(__file__).parent / "sample_prompt.md")
        print(f"No prompt file specified, using sample: {args.prompt}")
    
    prompt_path = Path(args.prompt)
    if not prompt_path.exists():
        print(f"Error: File not found: {args.prompt}")
        print(f"\nUsage:")
        print(f"  python cli_run.py prompt.md")
        print(f"  python cli_run.py prompt.md --run-tests --export html -o report.html")
        sys.exit(1)
    
    print("="*60)
    print("PromptFlow - Prompt Workflow Validator")
    print("="*60)
    print(f"File: {prompt_path}")
    print()
    
    # 1. 读取并解析
    print("[1/5] Parsing prompt...")
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt_text = f.read()
    
    p = PromptParser()
    parsed = p.parse(prompt_text)
    
    print(f"   Nodes: {len(parsed.nodes)}")
    print(f"   Rules: {len(parsed.rules)}")
    print(f"   Variables: {list(parsed.variables.keys())}")
    if parsed.nodes:
        print(f"   Node list: {', '.join(parsed.nodes.keys())}")
    
    # 2. 构建流程
    print("\n[2/5] Building flow graph...")
    builder = FlowBuilder()
    flow = builder.build(parsed)
    print(f"   Nodes: {len(flow.nodes)}")
    print(f"   Edges: {len(flow.edges)}")
    
    # 3. 分析路径
    print("\n[3/5] Analyzing paths...")
    analyzer = PathAnalyzer()
    coverage = analyzer.analyze(flow, parsed)
    print(f"   Total paths: {len(analyzer.all_paths)}")
    print(f"   Branch points: {len(analyzer.branch_points)}")
    
    if analyzer.branch_points:
        print(f"   Branch nodes: {', '.join([bp.node_id for bp in analyzer.branch_points])}")
    
    # 4. 生成测试
    print("\n[4/5] Generating tests...")
    generator = TestGenerator()
    generator.flow_graph = flow
    generator.path_analyzer = analyzer
    suite = generator.generate(flow, analyzer)
    print(f"   Test cases: {len(suite.test_cases)}")
    
    # 保存测试用例
    with open(args.tests, 'w', encoding='utf-8') as f:
        json.dump(suite.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"   Saved: {args.tests}")
    
    # 5. 运行测试
    test_summary = None
    if args.run_tests:
        print("\n[5/5] Running tests...")
        
        def mock_handler(node, user_input, context):
            """模拟的流程处理器"""
            next_nodes = {
                'A': 'D', 'B': 'T', 'D': 'K',
                'K': 'L', 'L': 'N', 'M': 'N',
                'O': 'N', 'P': 'N', 'Q': 'N',
                'N': 'H'
            }
            responses = {
                'A': "您好，请问是本人吗？",
                'B': "请问您认识机主吗？",
                'D': "耽误您一分钟做个回访可以吗？",
                'K': "您清楚合约期吗？",
                'L': "请问您拿到手机了吗？",
                'M': "有宽带设备吗？",
                'N': "您知道橙分期吗？",
                'H': "好的，再见！",
                'I': "橙分期是分期服务，再见！",
                'J': "记录反馈，再见！",
                'T': "好的，打扰了，再见！",
                'U': "麻烦转告，再见！",
            }
            resp = responses.get(node, "好的")
            nxt = next_nodes.get(node, 'H')
            return resp, nxt
        
        runner = ScenarioRunner()
        runner.set_flow_handler(mock_handler)
        runner.verbose = args.verbose
        test_summary = runner.run(suite)
    
    # 6. 导出报告
    if args.export or args.run_tests:
        output_path = args.output
        print(f"\n[Export] Generating report...")
        
        if args.export == 'html' or output_path.endswith('.html'):
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>PromptFlow Report - {prompt_path.name}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a2e; border-bottom: 3px solid #4361ee; padding-bottom: 15px; }}
        h2 {{ color: #4361ee; margin-top: 30px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 10px; text-align: center; }}
        .stat-card.green {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .stat-card.red {{ background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }}
        .stat-number {{ font-size: 2.5em; font-weight: bold; margin: 10px 0; }}
        .stat-label {{ font-size: 0.9em; opacity: 0.9; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #4361ee; color: white; font-weight: 600; }}
        tr:hover {{ background: #f8f9fa; }}
        .pass {{ color: #22c55e; font-weight: bold; }}
        .fail {{ color: #ef4444; font-weight: bold; }}
        .pending {{ color: #f59e0b; font-weight: bold; }}
        .nodes {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0; }}
        .node-tag {{ background: #e0e7ff; color: #3730a3; padding: 8px 16px; border-radius: 20px; font-size: 0.9em; }}
        .path {{ background: #f1f5f9; padding: 15px; border-radius: 8px; margin: 10px 0; font-family: monospace; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 PromptFlow 测试报告</h1>
        <p><strong>文件:</strong> {prompt_path.name}</p>
        
        <h2>📊 统计概览</h2>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">节点数</div>
                <div class="stat-number">{len(flow.nodes)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">路径数</div>
                <div class="stat-number">{len(analyzer.all_paths)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">测试用例</div>
                <div class="stat-number">{len(suite.test_cases)}</div>
            </div>
"""
            
            if test_summary:
                html_content += f"""
            <div class="stat-card green">
                <div class="stat-label">通过</div>
                <div class="stat-number">{test_summary.passed}</div>
            </div>
            <div class="stat-card red">
                <div class="stat-label">失败</div>
                <div class="stat-number">{test_summary.failed}</div>
            </div>
"""
            
            html_content += """
        </div>
        
        <h2>🔀 节点列表</h2>
        <div class="nodes">
"""
            
            for node_id in parsed.nodes.keys():
                html_content += f'            <span class="node-tag">{node_id}</span>\n'
            
            html_content += """        </div>
        
        <h2>🛤️ 关键路径</h2>
"""
            
            for i, path in enumerate(analyzer.get_critical_paths()[:5]):
                html_content += f'        <div class="path">{" → ".join(path.nodes)}</div>\n'
            
            if test_summary:
                html_content += """
        <h2>🧪 测试结果</h2>
        <table>
            <tr><th>ID</th><th>测试名称</th><th>类型</th><th>路径</th><th>结果</th></tr>
"""
                
                for r in test_summary.results:
                    status_class = "pass" if r.passed else "fail"
                    status_text = "✅ 通过" if r.passed else "❌ 失败"
                    path_str = " → ".join(r.test_case.path) if r.test_case.path else "-"
                    html_content += f"""            <tr>
                <td>{r.test_case.id}</td>
                <td>{r.test_case.name}</td>
                <td>{r.test_case.test_type.value}</td>
                <td><small>{path_str}</small></td>
                <td class="{status_class}">{status_text}</td>
            </tr>
"""
                
                html_content += """
        </table>
"""
            
            html_content += f"""
        <div class="footer">
            <p>Generated by PromptFlow | {Path(__file__).name}</p>
        </div>
    </div>
</body>
</html>
"""
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        elif args.export == 'json':
            report = {
                "file": str(prompt_path),
                "nodes": list(parsed.nodes.keys()),
                "edges": [{"from": e.source, "to": e.target} for e in flow.edges],
                "paths": {
                    "total": len(analyzer.all_paths),
                    "critical": [p.nodes for p in analyzer.get_critical_paths()]
                },
                "test_cases": suite.to_dict(),
                "test_results": test_summary.to_dict() if test_summary else None
            }
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"   ✅ Report saved: {output_path}")
    
    print("\n" + "="*60)
    print("✅ Done! All outputs:")
    print(f"   - Tests: {args.tests}")
    if args.export or args.run_tests:
        print(f"   - Report: {args.output}")
    print("="*60)


if __name__ == "__main__":
    main()
