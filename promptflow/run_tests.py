#!/usr/bin/env python
"""
测试运行脚本
用于验证 PromptFlow 测试用例
"""
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

def run_tests():
    """运行测试"""
    try:
        import pytest
        
        # 运行所有测试
        print("=" * 60)
        print("运行 PromptFlow 测试用例")
        print("=" * 60)
        
        # 使用 pytest 运行测试
        exit_code = pytest.main([
            'tests/',
            '-v',           # 详细输出
            '--tb=short',   # 简短的 traceback
            '--color=yes',  # 彩色输出
        ])
        
        print("\n" + "=" * 60)
        if exit_code == 0:
            print("✅ 所有测试通过!")
        else:
            print(f"❌ 测试失败 (退出码: {exit_code})")
        print("=" * 60)
        
        return exit_code
        
    except ImportError as e:
        print(f"错误: 无法导入 pytest - {e}")
        print("请运行: pip install pytest pytest-cov")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
