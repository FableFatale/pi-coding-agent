#!/usr/bin/env python
"""快速验证"""
import sys
sys.path.insert(0, 'src')

print("1. Testing imports...")
try:
    from promptflow import PromptParser, FlowBuilder, PathAnalyzer, TestGenerator
    print("   OK: Core modules imported")
except Exception as e:
    print(f"   FAIL: {e}")
    sys.exit(1)

print("2. Testing PromptParser...")
try:
    parser = PromptParser()
    prompt = open('examples/customer_service.md', 'r', encoding='utf-8').read()
    result = parser.parse(prompt)
    print(f"   OK: Parsed {len(result.nodes)} nodes")
except Exception as e:
    print(f"   FAIL: {e}")
    sys.exit(1)

print("3. Testing FlowBuilder...")
try:
    builder = FlowBuilder()
    flow = builder.build(result)
    print(f"   OK: Built flow with {len(flow.nodes)} nodes")
except Exception as e:
    print(f"   FAIL: {e}")
    sys.exit(1)

print("4. Testing PathAnalyzer...")
try:
    analyzer = PathAnalyzer()
    coverage = analyzer.analyze(flow, result)
    print(f"   OK: Found {len(analyzer.all_paths)} paths")
except Exception as e:
    print(f"   FAIL: {e}")
    sys.exit(1)

print("5. Testing TestGenerator...")
try:
    generator = TestGenerator()
    suite = generator.generate(flow, analyzer)
    print(f"   OK: Generated {len(suite.test_cases)} test cases")
except Exception as e:
    print(f"   FAIL: {e}")
    sys.exit(1)

print("\n✅ All basic tests passed!")
