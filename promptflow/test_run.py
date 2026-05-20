"""直接运行测试"""
import sys
sys.path.insert(0, 'src')

from promptflow import PromptParser, FlowBuilder, PathAnalyzer, TestGenerator

# 用户 prompt 文件路径
PROMPT_FILE = r"C:\Users\17745\Desktop\360营销\【Agent话术提示词导出】112471_信贷-甜橙信审-公众引流（流式）-翼支付-流程优化-202603_2026_04_10_14_28_11.md"

print("="*60)
print("PromptFlow 测试运行")
print("="*60)

# 1. 读取 Prompt
print(f"\n1. 读取 Prompt 文件...")
try:
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        prompt_text = f.read()
    print(f"   ✓ 读取成功，共 {len(prompt_text)} 字符")
except Exception as e:
    print(f"   ✗ 读取失败: {e}")
    prompt_text = """
# 角色
你是电信翼支付回访客服。

## 节点 A
确认本人

## 节点 B
非本人处理

## 节点 D
获取回访许可

## 节点 K
核实合约期

## 节点 L
核实手机类

## 节点 M
核实宽带类

## 节点 N
核实分期

## 节点 H
礼貌挂机

## 节点 I
分期解释挂机

## 节点 J
登记挂机
"""
    print(f"   使用默认示例 Prompt")

# 2. 解析
print(f"\n2. 解析 Prompt...")
parser = PromptParser()
parsed = parser.parse(prompt_text)
print(f"   ✓ 解析完成")
print(f"   - 节点数: {len(parsed.nodes)}")
print(f"   - 规则数: {len(parsed.rules)}")
print(f"   - 变量数: {len(parsed.variables)}")
if parsed.nodes:
    print(f"   - 节点列表: {list(parsed.nodes.keys())}")

# 3. 构建流程
print(f"\n3. 构建流程图...")
builder = FlowBuilder()
flow = builder.build(parsed)
print(f"   ✓ 流程图构建完成")
print(f"   - 节点数: {len(flow.nodes)}")
print(f"   - 边数: {len(flow.edges)}")

# 4. 分析路径
print(f"\n4. 分析路径...")
analyzer = PathAnalyzer()
coverage = analyzer.analyze(flow, parsed)
print(f"   ✓ 路径分析完成")
print(f"   - 总路径数: {len(analyzer.all_paths)}")
print(f"   - 分支点数: {len(analyzer.branch_points)}")

critical = analyzer.get_critical_paths()
print(f"   - 关键路径: {len(critical)} 条")
for p in critical[:3]:
    print(f"     • {p}")

# 5. 生成测试
print(f"\n5. 生成测试用例...")
generator = TestGenerator()
generator.flow_graph = flow
generator.path_analyzer = analyzer
suite = generator.generate(flow, analyzer)
print(f"   ✓ 生成完成")
print(f"   - 测试用例数: {len(suite.test_cases)}")

# 导出
import json
output_file = "tests_output.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(suite.to_dict(), f, ensure_ascii=False, indent=2)
print(f"\n6. 测试用例已导出到: {output_file}")

print("\n" + "="*60)
print("测试完成!")
print("="*60)
