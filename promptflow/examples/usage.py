"""
PromptFlow 使用示例
"""
from promptflow import (
    PromptParser,
    FlowBuilder,
    PathAnalyzer,
    TestGenerator,
    ScenarioRunner,
    TagEngine,
    LabelDefinition,
)


# ============ 示例1: 基本使用 ============

def example_basic():
    """基本使用流程"""
    
    # 示例 Prompt
    prompt_text = """
# 角色
你是电信客服，负责回访。

## 总目标
核实客户是否收到赠品。

## 节点 A
确认本人

## 节点 B
获取许可

## 节点 C
核实商品

## 节点 H
礼貌挂机

## 节点 I
解释挂机
"""
    
    # 1. 解析
    parser = PromptParser()
    parsed = parser.parse(prompt_text)
    print(f"解析到 {len(parsed.nodes)} 个节点")
    
    # 2. 构建流程
    builder = FlowBuilder()
    flow = builder.build(parsed)
    print(f"流程图: {len(flow.nodes)} 节点, {len(flow.edges)} 边")
    
    # 3. 分析路径
    analyzer = PathAnalyzer()
    coverage = analyzer.analyze(flow, parsed)
    print(f"发现 {len(analyzer.all_paths)} 条路径")
    print(f"关键路径: {len(analyzer.get_critical_paths())} 条")
    
    # 4. 生成测试
    generator = TestGenerator()
    generator.flow_graph = flow
    generator.path_analyzer = analyzer
    suite = generator.generate(flow, analyzer)
    print(f"生成 {len(suite.test_cases)} 个测试用例")
    
    return flow, analyzer, suite


# ============ 示例2: 标签系统 ============

def example_tags():
    """标签系统使用"""
    
    # 创建引擎
    engine = TagEngine()
    
    # 注册意向标签
    engine.register_label(LabelDefinition(
        id="A",
        name="高意向",
        category="intent",
        conditions=["accept>=2"],
        priority=50
    ))
    
    engine.register_label(LabelDefinition(
        id="B",
        name="中意向",
        category="intent",
        conditions=["accept>=1"],
        priority=40
    ))
    
    engine.register_label(LabelDefinition(
        id="C",
        name="待定",
        category="intent",
        priority=30
    ))
    
    # 注册个性标签
    engine.register_label(LabelDefinition(
        id="ask_interest",
        name="询问利息",
        category="personal",
        trigger_keywords=["利息", "利率", "日利率"]
    ))
    
    engine.register_label(LabelDefinition(
        id="accept",
        name="接受邀约",
        category="personal",
        trigger_keywords=["行", "可以", "好的", "试试"],
        count_rules="accumulate"
    ))
    
    engine.register_label(LabelDefinition(
        id="reject",
        name="拒绝邀约",
        category="personal",
        trigger_keywords=["不需要", "不用了", "没兴趣"],
        count_rules="accumulate"
    ))
    
    # 模拟对话
    dialogs = [
        ("你们利息多少？", "node1"),
        ("额度最高多少？", "node2"),
        ("行，我可以试试", "node3"),
        ("那怎么申请？", "node4"),
    ]
    
    for i, (user_input, node) in enumerate(dialogs, 1):
        engine.process_turn(user_input, node=node, turn=i)
    
    # 获取结果
    result = engine.get_result()
    
    print("="*50)
    print("标签判定结果")
    print("="*50)
    print(f"意向标签: {result.intent_label} - {result.intent_label_name}")
    print(f"采集标签: {result.personal_tags}")
    print(f"接受计数: {result.counts.get('accept', 0)}")
    print(f"拒绝计数: {result.counts.get('reject', 0)}")


# ============ 示例3: 运行测试 ============

def example_run_tests():
    """运行测试示例"""
    
    # 简单的流程处理器
    def flow_handler(node, user_input, context):
        if node == "A":
            if "是" in user_input:
                return "好的", "B"
            return "请问您是本人吗？", "A"
        elif node == "B":
            if "不" in user_input:
                return "好的，再见", "H"
            return "请问有什么可以帮您？", "C"
        elif node == "C":
            return "感谢您的配合，再见", "H"
        return "再见", "H"
    
    # 运行
    flow, analyzer, suite = example_basic()
    
    runner = ScenarioRunner()
    runner.set_flow_handler(flow_handler)
    summary = runner.run(suite)
    
    print("\n测试结果:")
    print(f"  通过: {summary.passed}/{summary.total_tests}")
    print(f"  成功率: {summary.pass_rate:.1%}")


# ============ 示例4: 从文件解析标签 ============

def example_parse_tags_from_prompt():
    """从 Prompt 解析标签"""
    
    prompt_with_tags = """
## 意向标签定义

| 等级 | 名称 | 判定条件 |
|------|------|----------|
| A | 高意向 | 接受>=2 |
| B | 中意向 | 接受=1 |
| C | 待定 | 其他 |

## 个性标签

| 标签 | 触发语义 |
|------|----------|
| 询问利息 | 利息、利率 |
| 询问额度 | 额度、能借多少 |
| 接受邀约 | 行、可以、好的 |
| 拒绝邀约 | 不需要、不用了 |
"""
    
    from promptflow.tags import create_tag_engine_from_prompt
    
    engine, intent_labels, personal_labels = create_tag_engine_from_prompt(prompt_with_tags)
    
    print("解析到的意向标签:")
    for label in intent_labels:
        print(f"  {label['id']}: {label['name']}")
    
    print("\n解析到的个性标签:")
    for label in personal_labels:
        print(f"  {label['name']}: {label.get('trigger_keywords', [])}")


# ============ 主函数 ============

if __name__ == "__main__":
    print("="*60)
    print("示例1: 基本使用")
    print("="*60)
    example_basic()
    
    print("\n" + "="*60)
    print("示例2: 标签系统")
    print("="*60)
    example_tags()
    
    print("\n" + "="*60)
    print("示例3: 运行测试")
    print("="*60)
    example_run_tests()
    
    print("\n" + "="*60)
    print("示例4: 解析标签")
    print("="*60)
    example_parse_tags_from_prompt()
