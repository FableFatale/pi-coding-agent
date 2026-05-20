#!/usr/bin/env python
"""
电信橙分期 - 话术 + 标签 完整测试与优化
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


# ============================================================
# 话术分析器
# ============================================================

class FlowAnalyzer:
    """话术流程分析器"""

    def __init__(self):
        self.issues = []
        self.suggestions = []

    def analyze_flow(self, dialogue: list) -> dict:
        """分析话术流程"""
        result = {
            "flow_score": 100,
            "issues": [],
            "suggestions": [],
            "flow_problems": [],
            "tag_recommendations": []
        }

        for i, turn in enumerate(dialogue):
            user_input = turn.get("user", "")
            ai_output = turn.get("ai", "")

            # 问题1: 客户等待/中断
            if any(kw in user_input for kw in ["等一下", "稍等", "忙"]):
                result["flow_problems"].append({
                    "turn": i,
                    "problem": "客户表示等待/忙碌",
                    "suggestion": "话术应包含'好的，我等您'并等待回应"
                })
                result["flow_score"] -= 10

            # 问题2: 语气词
            if user_input.strip() in ["", "嗯", "啊", "哦", "嗯嗯", "啊啊"]:
                result["flow_problems"].append({
                    "turn": i,
                    "problem": "客户只回复语气词",
                    "suggestion": "话术应包含二次确认或结束语"
                })
                result["flow_score"] -= 5

            # 问题3: 投诉
            if any(kw in user_input for kw in ["投诉", "骗", "被骗", "不满"]):
                result["flow_problems"].append({
                    "turn": i,
                    "problem": "客户表示投诉/不满",
                    "suggestion": "话术应切换到投诉处理话术，包含道歉和记录确认"
                })
                result["flow_score"] -= 15

            # 问题4: 询问业务
            if any(kw in user_input for kw in ["啥是", "啥玩意儿", "怎么", "为什么"]):
                result["flow_problems"].append({
                    "turn": i,
                    "problem": "客户询问业务定义",
                    "suggestion": "话术应包含清晰业务解释话术"
                })
                result["flow_score"] -= 10

            # 问题5: 方言
            dialect_keywords = ["收到咯", "冇", "整咯", "晓得咯", "啥子"]
            if any(kw in user_input for kw in dialect_keywords):
                result["flow_problems"].append({
                    "turn": i,
                    "problem": "客户使用方言",
                    "suggestion": "话术应包含方言确认环节"
                })
                result["flow_score"] -= 5

            # 问题6: 未收到商品
            if any(kw in user_input for kw in ["没收到", "什么都没", "只有钱"]):
                result["flow_problems"].append({
                    "turn": i,
                    "problem": "客户表示未收到商品",
                    "suggestion": "话术应包含道歉和记录确认话术"
                })
                result["flow_score"] -= 10

        result["flow_score"] = max(0, result["flow_score"])
        return result


# ============================================================
# 综合测试用例
# ============================================================

COMPREHENSIVE_TEST_CASES = [
    # 场景1: 标准流程 - 正常
    {
        "name": "标准流程-正常",
        "dialogue": [
            {"user": "是的", "ai": "请问您当时办理橙分期，拿到了什么商品呢？"},
            {"user": "拿到了华为手机", "ai": "请问您知道每月需要还款吗？"},
            {"user": "知道", "ai": "好的，感谢您的配合，祝您生活愉快！"}
        ],
        "expected_flow_score": 100,
        "expected_tag": "正常"
    },

    # 场景2: 客户等待
    {
        "name": "流程问题-客户等待",
        "dialogue": [
            {"user": "等一下", "ai": "好的，请问您先忙"},
            {"user": "", "ai": "喂？"}
        ],
        "expected_flow_score": 90,
        "expected_tag": "未沟通"
    },

    # 场景3: 语气词
    {
        "name": "流程问题-语气词",
        "dialogue": [
            {"user": "嗯", "ai": "请问您方便吗？"},
            {"user": "嗯嗯", "ai": "好的，打扰了"}
        ],
        "expected_flow_score": 95,
        "expected_tag": "未沟通"
    },

    # 场景4: 投诉
    {
        "name": "流程问题-客户投诉",
        "dialogue": [
            {"user": "我要投诉", "ai": "请问是什么问题？"},
            {"user": "被骗了", "ai": "非常抱歉给您带来不便"}
        ],
        "expected_flow_score": 85,
        "expected_tag": "营销缺失"
    },

    # 场景5: 询问业务
    {
        "name": "流程问题-询问业务",
        "dialogue": [
            {"user": "啥是橙分期？", "ai": "橙分期是..."},
            {"user": "咋还？", "ai": "每月需要..."}
        ],
        "expected_flow_score": 90,
        "expected_tag": "营销缺失"
    },

    # 场景6: 方言-粤语
    {
        "name": "流程问题-方言粤语",
        "dialogue": [
            {"user": "係啊收到咯", "ai": "请问您说的是...吗？"},
            {"user": "整了个路由器", "ai": "好的请问您知道合约吗？"},
            {"user": "知道得嘛", "ai": "好的感谢配合"}
        ],
        "expected_flow_score": 95,
        "expected_tag": "正常"
    },

    # 场景7: 方言-四川
    {
        "name": "流程问题-方言四川",
        "dialogue": [
            {"user": "整了个手机", "ai": "请问您说的是手机吗？"},
            {"user": "晓得咯", "ai": "好的请问您知道分期规则吗？"}
        ],
        "expected_flow_score": 95,
        "expected_tag": "正常"
    },

    # 场景8: 未收到商品
    {
        "name": "流程问题-未收到商品",
        "dialogue": [
            {"user": "我没收到东西", "ai": "非常抱歉，请问您是说什么都没收到吗？"},
            {"user": "只有钱", "ai": "好的我这边记录您反馈的情况"}
        ],
        "expected_flow_score": 90,
        "expected_tag": "套机套现"
    },

    # 场景9: 违规商品
    {
        "name": "流程问题-违规商品",
        "dialogue": [
            {"user": "拿到了耳机", "ai": "好的请问您知道还款规则吗？"},
            {"user": "知道", "ai": "好的感谢配合"}
        ],
        "expected_flow_score": 100,
        "expected_tag": "违规商品"
    },

    # 场景10: 矛盾表述
    {
        "name": "流程问题-矛盾表述",
        "dialogue": [
            {"user": "收到了但好像没收到", "ai": "请问您能具体说明一下吗？"},
            {"user": "整了个东西", "ai": "好的请问是什么商品呢？"},
            {"user": "手机", "ai": "好的请问您知道合约吗？"}
        ],
        "expected_flow_score": 90,
        "expected_tag": "正常"
    },
]


# ============================================================
# 优化建议生成
# ============================================================

def generate_optimization_report(results: list) -> str:
    """生成综合优化报告"""

    report = f"""# 电信橙分期话术 + 标签 优化报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 一、测试统计

| 指标 | 值 |
|------|-----|
| 总测试数 | {len(results)} |
| 流程评分平均 | {sum(r['flow_score'] for r in results) / len(results):.1f}% |
| 话术问题数 | {sum(len(r['flow_problems']) for r in results)} |
| 标签错误数 | {sum(1 for r in results if not r['tag_correct'])} |

---

## 二、话术问题分析

### 问题类型统计

| 问题类型 | 出现次数 | 影响 |
|----------|----------|------|
"""

    # 统计问题类型
    problem_stats = {}
    for r in results:
        for p in r.get("flow_problems", []):
            prob = p["problem"]
            if prob not in problem_stats:
                problem_stats[prob] = 0
            problem_stats[prob] += 1

    for prob, count in sorted(problem_stats.items(), key=lambda x: x[1], reverse=True):
        report += f"| {prob} | {count} | 扣{5*count}分 |\n"

    report += """
### 话术优化建议

#### 1. 开场白优化

```markdown
❌ 旧: "您好，我是电信客服，想问您关于橙分期的问题"
✅ 新: "您好，请问是[姓名]先生/女士吗？我是中国电信客服，
        想跟您回访一下橙分期业务，请问现在方便吗？"

要点:
- 确认身份（提升信任）
- 明确目的（降低抗拒）
- 询问是否方便（尊重客户）
```

#### 2. 等待/中断处理

```markdown
客户: "等一下" / "稍等" / "我忙"

AI: "好的，请您先忙，我等您一下。" [等待30秒]

   ├── 客户返回 → 继续流程
   └── 客户仍忙 → AI: "打扰您了，再见！"
                  → 记录: 未沟通
```

#### 3. 语气词处理

```markdown
客户: "嗯" / "啊" / "哦"

AI: "请问您方便吗？" [二次确认]

   ├── 客户明确回复 → 继续
   └── 客户仍语气词 → AI: "好的，打扰您了，再见！"
                      → 记录: 未沟通
```

#### 4. 投诉处理话术

```markdown
客户: "我要投诉" / "被骗了"

AI: "非常抱歉给您带来不便，请问您遇到了什么问题呢？"

→ 记录投诉内容
→ AI: "您说的情况我已经记录，会转交相关部门处理，感谢您的反馈！"
```

#### 5. 业务解释话术

```markdown
客户: "啥是橙分期？" / "咋还？"

AI: "橙分期是我们电信的一个分期还款业务，
   您每月需要还款XX元，12期/24期后设备就是您的了。
   请问您当时办理时工作人员有说明吗？"
```

#### 6. 方言识别确认

```markdown
客户: "係啊收到咯" / "整了个宽带"

AI: [方言识别] "好的，您是说拿到了[商品]，请问您知道每月需要还款吗？"
         或
AI: "不好意思，请问您说的是...（宽带/手机）吗？"
```

---

## 三、标签判定优化

### 当前问题

"""

    # 统计标签问题
    tag_errors = [r for r in results if not r.get("tag_correct")]
    if tag_errors:
        report += f"发现 {len(tag_errors)} 个标签判定问题：\n\n"
        for r in tag_errors:
            report += f"- {r['name']}: 期望'{r['expected_tag']}' 实际'{r['actual_tag']}'\n"
    else:
        report += "✅ 标签判定全部正确\n"

    report += """
### 标签判定规则（已优化）

1. **上下文累积**: 全文分析，关键词永久标记
2. **方言语义映射**: 收到咯→收到了，冇→没有
3. **边界情况**: 矛盾表述以肯定为准

### 完整标签规则

```
1. 套机套现 → 未收到商品 + 无付费
2. 违规商品 → 收到违规商品库商品
3. 营销缺失 → 收到商品但不知晓/被骗/投诉
4. 正常 → 收到商品 + 知晓合约
5. 未沟通 → 轮次少/无有效信息
```

---

## 四、综合优化建议

### 高优先级（立即优化）

1. **话术开场白**: 增加身份确认、目的说明、询问是否方便
2. **异常处理话术**: 增加等待、语气词、投诉处理话术
3. **方言支持**: 增加方言识别和确认环节
4. **业务解释话术**: 增加清晰的业务定义解释

### 中优先级（尽快优化）

1. **标签规则**: 应用优化后的上下文累积规则
2. **方言词库**: 持续丰富方言映射表
3. **测试覆盖**: 增加更多边界场景测试

### 低优先级（持续优化）

1. **A/B测试**: 测试不同话术效果
2. **数据收集**: 收集真实对话持续优化
3. **机器学习**: 基于数据训练更智能的话术

---

## 五、下一步行动

### 立即执行
- [ ] 更新开场白话术
- [ ] 添加异常处理话术
- [ ] 增加方言确认环节
- [ ] 更新标签判定规则

### 持续改进
- [ ] 每周分析话术问题
- [ ] 每月更新方言词库
- [ ] 每季度优化话术流程

---

## 六、测试用例

### 话术测试用例

| 场景 | 流程问题 | 建议 |
|------|----------|------|
"""

    for r in results:
        problems = "、".join([p["problem"] for p in r.get("flow_problems", [])])
        if problems:
            report += f"| {r['name']} | {problems} | 话术优化 |\n"
        else:
            report += f"| {r['name']} | 无 | 保持 |\n"

    report += """

---

*报告自动生成*
"""

    return report


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 60)
    print("  电信橙分期话术 + 标签 完整测试")
    print("=" * 60)

    # 标签库
    TAG_WHITELIST = ["套机套现", "违规商品", "营销缺失", "正常", "未沟通"]
    VIOLATION_PRODUCTS = ["耳机", "充电宝", "空气炸锅", "锅", "电视"]
    NORMAL_PRODUCTS = ["手机", "路由器", "宽带", "华为"]

    # 分析器
    flow_analyzer = FlowAnalyzer()

    # 结果
    results = []

    print("\n📋 运行综合测试...\n")

    for case in COMPREHENSIVE_TEST_CASES:
        dialogue = case["dialogue"]

        # 分析话术流程
        flow_result = flow_analyzer.analyze_flow(dialogue)

        # 简单标签判定
        full_text = " ".join([t.get("user", "") for t in dialogue])

        if any(kw in full_text for kw in ["没收到", "什么都没有", "只有钱"]):
            if not any(kw in full_text for kw in ["买", "付费", "花钱", "整"]):
                tag = "套机套现"
            else:
                tag = "正常"
        elif any(kw in full_text for kw in ["耳机", "充电宝", "空气炸锅", "锅"]):
            tag = "违规商品"
        elif any(kw in full_text for kw in ["手机", "路由器", "宽带", "华为"]):
            if any(kw in full_text for kw in ["知道", "晓得"]):
                tag = "正常"
            else:
                tag = "营销缺失"
        elif any(kw in full_text for kw in ["投诉", "骗", "啥是"]):
            tag = "营销缺失"
        elif len(dialogue) <= 2 and any(u.strip() in ["", "嗯", "啊"] for u in [t.get("user", "") for t in dialogue]):
            tag = "未沟通"
        else:
            tag = "正常"

        tag_correct = tag == case["expected_tag"]

        result = {
            "name": case["name"],
            "dialogue": dialogue,
            "flow_score": flow_result["flow_score"],
            "flow_problems": flow_result["flow_problems"],
            "expected_tag": case["expected_tag"],
            "actual_tag": tag,
            "tag_correct": tag_correct
        }
        results.append(result)

        # 打印结果
        status = "✅" if tag_correct else "❌"
        flow_status = "💚" if flow_result["flow_score"] >= 90 else "💛" if flow_result["flow_score"] >= 70 else "❤️"

        print(f"  {status}{flow_status} {case['name']}")
        print(f"      流程: {flow_result['flow_score']}% | 标签: {tag}")

        if flow_result["flow_problems"]:
            for p in flow_result["flow_problems"]:
                print(f"      问题: {p['problem']}")
                print(f"      建议: {p['suggestion']}")

    # 生成报告
    print("\n" + "=" * 60)
    print("  📄 生成优化报告")
    print("=" * 60)

    report = generate_optimization_report(results)

    # 保存报告
    report_path = "FLOW_TAG_OPTIMIZATION_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n  报告已保存: {report_path}")

    # 统计
    avg_score = sum(r['flow_score'] for r in results) / len(results)
    tag_errors = sum(1 for r in results if not r['tag_correct'])
    flow_issues = sum(len(r['flow_problems']) for r in results)

    print(f"\n  📊 统计:")
    print(f"     流程评分平均: {avg_score:.1f}%")
    print(f"     话术问题数: {flow_issues}")
    print(f"     标签错误数: {tag_errors}")

    print("\n" + "=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
