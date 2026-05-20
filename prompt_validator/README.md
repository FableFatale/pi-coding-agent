# Prompt 验证工作流框架

通用工具，用于解析、测试和验证结构化 Prompt（如客服话术、工作流 Agent）。

## 目录结构

```
prompt_validator/
├── core/
│   ├── __init__.py          # 导出核心类
│   ├── parser.py            # Prompt 解析器
│   ├── flow_builder.py      # 流程构建器
│   ├── path_analyzer.py     # 路径分析器
│   ├── test_generator.py    # 测试用例生成器
│   ├── scenario_runner.py   # 场景运行器
│   └── result_analyzer.py   # 结果分析器
├── main.py                  # 主入口
└── requirements.txt
```

## 使用方法

### 1. 基础用法 - 解析 Prompt

```python
from prompt_validator import PromptValidator

validator = PromptValidator()

# 解析
prompt_text = open("your_prompt.md").read()
validator.parse(prompt_text)

# 构建流程
validator.build_flow()

# 分析路径
validator.analyze_paths()

# 生成测试用例
validator.generate_tests()

# 导出测试用例
validator.export_test_cases("test_cases.json")
```

### 2. 命令行用法

```bash
# 解析并生成测试用例
python main.py -p path/to/prompt.md

# 解析并运行测试
python main.py -p path/to/prompt.md --run-tests

# 导出 HTML 报告
python main.py -p path/to/prompt.md --export html -o report.html
```

### 3. 自定义 LLM 客户端

```python
from prompt_validator import PromptValidator, ScenarioRunner

class MyLLMClient:
    def call(self, prompt: str, context: dict) -> str:
        # 调用你的 LLM
        response = your_llm_api(prompt)
        return response

validator = PromptValidator()
validator.run_full_pipeline(
    "path/to/prompt.md",
    llm_client=MyLLMClient(),
    run_tests_flag=True
)
```

### 4. 自定义流程处理器

如果不想用 LLM，可以用规则引擎处理：

```python
def my_flow_handler(node: str, user_input: str, context: dict):
    # 根据 node 和 user_input 返回 (response, next_node)
    if node == "A":
        if "是" in user_input:
            return "好的", "D"
        else:
            return "请问您认识张三吗？", "B"
    # ... 其他节点
    return "再见", "END"

validator.run_full_pipeline(
    "path/to/prompt.md",
    flow_handler=my_flow_handler,
    run_tests_flag=True
)
```

## 核心类说明

| 类 | 功能 |
|---|---|
| `PromptParser` | 解析 Prompt 文本，提取节点、规则、变量 |
| `FlowBuilder` | 构建流程图（NetworkX DiGraph） |
| `PathAnalyzer` | 分析所有可能路径，计算覆盖率 |
| `TestGenerator` | 根据路径生成测试用例 |
| `ScenarioRunner` | 运行测试，记录结果 |
| `ResultAnalyzer` | 分析结果，生成报告 |
| `TagEngine` | 通用标签引擎，支持意向/个性标签 |
| `TagParser` | 从 Prompt 中解析标签定义 |

## 标签系统

### 自动解析

```python
from core.tags import create_tag_engine_from_prompt

# 从 Prompt 自动解析标签
engine, intent_labels, personal_labels = create_tag_engine_from_prompt(prompt_text)

# 处理对话
engine.process_turn("利息多少？", node="node1", turn=1)

# 获取结果
result = engine.get_result()
```

### 手动注册

```python
from core.tags import TagEngine, LabelDefinition

engine = TagEngine()

# 注册意向标签
engine.register_label(LabelDefinition(
    id="A",
    name="高意向",
    category="intent",
    conditions=["accept_count>=2"],
    priority=50
))

# 注册个性标签
engine.register_label(LabelDefinition(
    id="ask_interest",
    name="询问利息",
    category="personal",
    trigger_keywords=["利息", "利率", "日利率"],
    count_rules="accumulate"
))
```

### 输出格式

```json
{
  "intent_label": "A",
  "intent_label_name": "高意向",
  "personal_tags": ["personal-询问利息", "personal-接受邀约"],
  "counts": {"accept": 2, "reject": 0}
}
```

## 输出格式

### 测试用例 (JSON)

```json
{
  "name": "Test Suite",
  "total_tests": 50,
  "test_cases": [
    {
      "id": "tc_0001",
      "name": "Happy Path",
      "test_type": "normal",
      "path": ["A", "D", "K", "L", "N", "H"],
      "user_inputs": [
        {"node": "A", "input": "是本人", "type": "normal"}
      ],
      "expected_ending": "H"
    }
  ]
}
```

### 分析报告 (JSON)

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "summary": {
    "total": 50,
    "passed": 45,
    "failed": 3,
    "errors": 2,
    "pass_rate": "90.0%"
  },
  "coverage": {
    "path_coverage": 0.75,
    "node_coverage": 0.95,
    "branch_coverage": 0.60
  },
  "issues": [
    {
      "id": "ISSUE-001",
      "severity": "high",
      "category": "logic",
      "title": "节点 K 逻辑问题",
      "suggestion": "检查分支条件"
    }
  ]
}
```

## 自定义扩展

### 添加输入生成策略

```python
from prompt_validator import TestGenerator

class CustomTestGenerator(TestGenerator):
    def _generate_phone_inputs(self, node_id):
        # 自定义手机类节点输入
        return [
            TestInput(node_id, "拿到了华为手机"),
            TestInput(node_id, "有优惠买小米"),
        ]
```

### 添加验证规则

```python
def validate_response(state, response):
    # 检查是否包含禁用词
    forbidden = ["了解", "好的", "明白"]
    for word in forbidden:
        if word in response:
            return False, f"包含禁用词: {word}"
    return True, ""
```

## 适用场景

- ✅ 客服话术流程验证
- ✅ Agent 工作流测试
- ✅ 多轮对话系统调试
- ✅ Prompt 覆盖率分析
- ✅ 回归测试

## License

MIT
