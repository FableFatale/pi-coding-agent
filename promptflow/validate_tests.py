#!/usr/bin/env python
"""
语法验证脚本
验证所有测试文件的语法正确性
"""
import sys
import os
import py_compile
import traceback


def validate_file(filepath):
    """验证单个文件的语法"""
    try:
        py_compile.compile(filepath, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)


def validate_tests():
    """验证所有测试文件"""
    project_root = os.path.dirname(__file__)
    tests_dir = os.path.join(project_root, 'tests')
    
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
        'conftest.py',
        '__init__.py',
    ]
    
    print("=" * 60)
    print("验证测试文件语法")
    print("=" * 60)
    
    all_valid = True
    valid_count = 0
    invalid_count = 0
    
    for filename in test_files:
        filepath = os.path.join(tests_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"⏭️  跳过: {filename} (不存在)")
            continue
        
        print(f"\n验证: {filename}")
        valid, error = validate_file(filepath)
        
        if valid:
            print(f"  ✅ 语法正确")
            valid_count += 1
        else:
            print(f"  ❌ 语法错误:")
            print(f"     {error}")
            all_valid = False
            invalid_count += 1
    
    print("\n" + "=" * 60)
    print(f"验证完成: {valid_count} 通过, {invalid_count} 失败")
    print("=" * 60)
    
    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(validate_tests())
