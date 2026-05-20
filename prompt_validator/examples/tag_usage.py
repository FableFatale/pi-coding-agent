"""
标签系统使用示例
"""
from core.tags import (
    TagEngine,
    TagParser,
    LabelDefinition,
    create_tag_engine_from_prompt
)


# ============ 示例1: 从 Prompt 自动解析 ============

def example_parse_from_prompt():
    """从 Prompt 文件自动解析标签"""
    
    prompt_text = """
## 意向标签定义

| 等级 | 名称 | 判定条件 |
|------|------|----------|
| A | 高意向 | 接受邀约>=2 |
| B | 中意向 | 接受邀约=1 |
| C | 待定 | 其他 |
| D | 明确拒绝 | 拒绝>=1 |

## 个性标签

| 标签 | 触发语义 |
|------|----------|
| 询问利息 | "利息多少"、"利率多少" |
| 询问额度 | "额度多少"、"能借多少" |
| 接受邀约 | "行"、"可以"、"好的" |
| 拒绝邀约 | "不需要"、"不用了" |
    """
    
    # 解析
    engine, intent_labels, personal_labels = create_tag_engine_from_prompt(prompt_text)
    
    print("=== 解析结果 ===")
    print(f"意向标签: {len(intent_labels)} 个")
    print(f"个性标签: {len(personal_labels)} 个")
    
    # 使用
    engine.process_turn("利息多少啊？", node="node1", turn=1)
    engine.process_turn("行，可以试试", node="node2", turn=2)
    
    result = engine.get_result()
    print(f"\n判定结果: {result.intent_label} - {result.intent_label_name}")
    print(f"采集标签: {result.personal_tags}")


# ============ 示例2: 手动注册标签 ============

def example_manual_registration():
    """手动注册标签"""
    
    engine = TagEngine()
    
    # 注册意向标签
    engine.register_label(LabelDefinition(
        id="A",
        name="高意向",
        category="intent",
        conditions=["accept_count>=2"],
        priority=50
    ))
    
    engine.register_label(LabelDefinition(
        id="B", 
        name="中意向",
        category="intent",
        conditions=["accept_count>=1"],
        priority=40
    ))
    
    engine.register_label(LabelDefinition(
        id="C",
        name="待定意向",
        category="intent",
        priority=30
    ))
    
    # 注册个性标签
    engine.register_label(LabelDefinition(
        id="ask_interest",
        name="询问利息",
        category="personal",
        trigger_keywords=["利息", "利率", "日利率"],
        count_rules="once"
    ))
    
    engine.register_label(LabelDefinition(
        id="ask_quota",
        name="询问额度",
        category="personal",
        trigger_keywords=["额度", "能借多少", "最高多少"],
        count_rules="once"
    ))
    
    engine.register_label(LabelDefinition(
        id="accept",
        name="接受邀约",
        category="personal",
        trigger_keywords=["行", "可以", "好的", "试试"],
        count_rules="accumulate"  # 累加计数
    ))
    
    engine.register_label(LabelDefinition(
        id="reject",
        name="拒绝邀约",
        category="personal",
        trigger_keywords=["不需要", "不用了", "没兴趣"],
        count_rules="accumulate"
    ))
    
    return engine


# ============ 示例3: 自定义匹配器 ============

def example_custom_matcher():
    """自定义匹配器"""
    from core.tags import KeywordMatcher, RegexMatcher, CompositeMatcher
    
    engine = TagEngine()
    
    # 关键词匹配
    engine.register_label(LabelDefinition(
        id="complaint",
        name="投诉威胁",
        category="personal",
        trigger_keywords=["投诉", "举报", "报警", "曝光"],
        priority=100
    ))
    
    # 正则匹配
    engine.register_label(LabelDefinition(
        id="phone_number",
        name="电话号码",
        category="personal",
        trigger_pattern=r"1[3-9]\d{9}",  # 手机号正则
        priority=50
    ))
    
    # 组合匹配
    composite = CompositeMatcher([
        KeywordMatcher(["利息", "利率"]),
        KeywordMatcher(["高", "贵"])
    ], mode="all")
    
    # 注册自定义匹配器
    engine._matchers["high_interest"] = composite
    engine.register_label(LabelDefinition(
        id="high_interest",
        name="利息太高",
        category="personal",
        priority=60
    ))
    
    return engine


# ============ 示例4: 完整流程 ============

def example_full_flow():
    """完整标签流程"""
    
    # 创建引擎
    engine = example_manual_registration()
    
    # 模拟对话
    dialogs = [
        ("你们利息多少？", "node_intro"),
        ("额度最高多少？", "node_quota"),
        ("好的，我可以试试", "node_accept"),
        ("那怎么申请？", "node_apply"),
        ("行，帮我申请", "node_final"),
    ]
    
    for i, (user_input, node) in enumerate(dialogs, 1):
        engine.process_turn(user_input, node=node, turn=i)
        print(f"轮次{i}: {user_input}")
    
    # 判定结果
    result = engine.get_result()
    
    print("\n" + "="*50)
    print("最终判定结果")
    print("="*50)
    print(f"意向标签: {result.intent_label} - {result.intent_label_name}")
    print(f"采集标签: {result.personal_tags}")
    print(f"计数信息: {result.counts}")


# ============ 运行示例 ============

if __name__ == "__main__":
    print("="*60)
    print("示例1: 从 Prompt 解析")
    print("="*60)
    # example_parse_from_prompt()
    
    print("\n" + "="*60)
    print("示例2: 手动注册")
    print("="*60)
    engine = example_manual_registration()
    
    print("\n" + "="*60)
    print("示例3: 自定义匹配器")
    print("="*60)
    engine = example_custom_matcher()
    
    print("\n" + "="*60)
    print("示例4: 完整流程")
    print("="*60)
    example_full_flow()
