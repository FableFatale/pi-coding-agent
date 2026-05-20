#!/usr/bin/env python
"""
快速验证脚本 - 验证所有模块和测试可以正确导入
"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_import(module_name, class_names):
    """测试导入模块和类"""
    try:
        module = __import__(module_name, fromlist=class_names)
        for class_name in class_names:
            if hasattr(module, class_name):
                print(f"  ✅ {class_name}")
            else:
                print(f"  ❌ {class_name} 未找到")
                return False
        return True
    except Exception as e:
        print(f"  ❌ 导入失败: {e}")
        return False


def main():
    print("=" * 60)
    print("验证模块导入")
    print("=" * 60)
    
    # 验证核心模块
    print("\n📦 核心模块:")
    modules = [
        ('parser', ['PromptParser', 'ParsedPrompt', 'NodeDefinition']),
        ('flow_builder', ['FlowBuilder', 'FlowGraph', 'FlowEdge']),
        ('path_analyzer', ['PathAnalyzer', 'Path', 'PathCoverage']),
        ('test_generator', ['TestGenerator', 'TestCase', 'TestSuite']),
        ('scenario_runner', ['ScenarioRunner', 'TestRunResult', 'TestRunSummary']),
        ('result_analyzer', ['ResultAnalyzer', 'AnalysisReport', 'Issue']),
        ('tags', ['TagEngine', 'TagParser', 'TagResult', 'LabelDefinition']),
        ('cli', ['PromptFlow']),
    ]
    
    all_success = True
    for module_name, class_names in modules:
        print(f"\n  模块: {module_name}")
        if not test_import(f'promptflow.{module_name}', class_names):
            all_success = False
    
    # 验证测试文件
    print("\n📋 测试文件:")
    test_files = [
        'test_parser.py',
        'test_flow_builder.py',
        'test_path_analyzer.py',
        'test_test_generator.py',
        'test_scenario_runner.py',
        'test_result_analyzer.py',
        'test_tags.py',
        'test_integration.py',
        'test_cli.py',
    ]
    
    for test_file in test_files:
        test_path = os.path.join('tests', test_file)
        if os.path.exists(test_path):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(test_file.replace('.py', ''), test_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print(f"  ✅ {test_file}")
            except Exception as e:
                print(f"  ❌ {test_file}: {e}")
                all_success = False
        else:
            print(f"  ⏭️  {test_file} (不存在)")
    
    print("\n" + "=" * 60)
    if all_success:
        print("✅ 所有验证通过!")
    else:
        print("❌ 部分验证失败")
    print("=" * 60)
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
