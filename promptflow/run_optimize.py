#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""电信橙分期话术+标签完整测试"""
import sys
import os
from datetime import datetime

# 标签库
VIOLATION_PRODUCTS = ["耳机", "充电宝", "空气炸锅", "锅", "电视"]
NORMAL_PRODUCTS = ["手机", "路由器", "宽带", "华为"]

# 测试用例
TEST_CASES = [
    {"name": "标准流程-正常", "dialogue": [
        {"user": "是的", "ai": "请问您拿到了什么商品？"},
        {"user": "拿到了华为手机", "ai": "请问您知道还款吗？"},
        {"user": "知道", "ai": "好的感谢配合"}
    ], "expected_tag": "正常"},
    {"name": "客户等待", "dialogue": [
        {"user": "等一下", "ai": "好的"},
        {"user": "", "ai": "喂？"}
    ], "expected_tag": "未沟通"},
    {"name": "语气词", "dialogue": [
        {"user": "嗯", "ai": "请问方便吗？"},
        {"user": "嗯嗯", "ai": "好的"}
    ], "expected_tag": "未沟通"},
    {"name": "投诉", "dialogue": [
        {"user": "我要投诉", "ai": "请问什么问题？"},
        {"user": "被骗了", "ai": "非常抱歉"}
    ], "expected_tag": "营销缺失"},
    {"name": "询问业务", "dialogue": [
        {"user": "啥是橙分期？", "ai": "橙分期是..."},
        {"user": "咋还？", "ai": "每月需要..."}
    ], "expected_tag": "营销缺失"},
    {"name": "方言粤语", "dialogue": [
        {"user": "係啊收到咯", "ai": "请问是？"},
        {"user": "整了个路由器", "ai": "好的请问知道合约吗？"},
        {"user": "知道得嘛", "ai": "好的"}
    ], "expected_tag": "正常"},
    {"name": "方言四川", "dialogue": [
        {"user": "整了个手机", "ai": "请问是手机吗？"},
        {"user": "晓得咯", "ai": "好的请问知道分期吗？"}
    ], "expected_tag": "正常"},
    {"name": "未收到商品", "dialogue": [
        {"user": "我没收到东西", "ai": "非常抱歉"},
        {"user": "只有钱", "ai": "好的记录"}
    ], "expected_tag": "套机套现"},
    {"name": "违规商品-耳机", "dialogue": [
        {"user": "拿到了耳机", "ai": "好的请问知道还款吗？"},
        {"user": "知道", "ai": "好的"}
    ], "expected_tag": "违规商品"},
    {"name": "违规商品-空气炸锅", "dialogue": [
        {"user": "整了个空气炸锅", "ai": "好的请问知道合约吗？"},
        {"user": "晓得咯", "ai": "好的"}
    ], "expected_tag": "违规商品"},
    {"name": "矛盾表述", "dialogue": [
        {"user": "收到了但好像又没收到", "ai": "请问？"},
        {"user": "整了个手机", "ai": "好的请问知道合约吗？"},
        {"user": "知道", "ai": "好的"}
    ], "expected_tag": "正常"},
    {"name": "边界-付费但违规", "dialogue": [
        {"user": "我花钱买的耳机", "ai": "好的"}
    ], "expected_tag": "违规商品"},
]

def classify_tag(dialogue):
    """简单标签判定"""
    full_text = " ".join([t.get("user", "") for t in dialogue])
    
    # 未收到商品
    if any(kw in full_text for kw in ["没收到", "什么都没", "只有钱", "冇"]):
        if not any(kw in full_text for kw in ["买", "付费", "花钱", "整", "係"]):
            return "套机套现"
    
    # 违规商品
    for p in VIOLATION_PRODUCTS:
        if p in full_text:
            return "违规商品"
    
    # 正常商品
    for p in NORMAL_PRODUCTS:
        if p in full_text:
            if any(kw in full_text for kw in ["知道", "晓得"]):
                return "正常"
            else:
                return "营销缺失"
    
    # 投诉/询问
    if any(kw in full_text for kw in ["投诉", "骗", "啥是", "啥玩意儿"]):
        return "营销缺失"
    
    # 语气词
    if len(dialogue) <= 2:
        users = [t.get("user", "") for t in dialogue]
        if all(u.strip() in ["", "嗯", "啊", "哦", "嗯嗯"] for u in users):
            return "未沟通"
    
    return "正常"

def analyze_flow(dialogue):
    """分析话术流程"""
    score = 100
    problems = []
    
    for i, turn in enumerate(dialogue):
        user = turn.get("user", "")
        
        if any(kw in user for kw in ["等一下", "稍等", "忙"]):
            problems.append({"turn": i, "problem": "客户等待/忙碌", "suggestion": "话术应包含'好的，我等您'"})
            score -= 10
        
        if user.strip() in ["", "嗯", "啊", "哦", "嗯嗯", "啊啊"]:
            problems.append({"turn": i, "problem": "语气词", "suggestion": "应二次确认或结束"})
            score -= 5
        
        if any(kw in user for kw in ["投诉", "骗", "被骗"]):
            problems.append({"turn": i, "problem": "客户投诉", "suggestion": "应道歉并记录"})
            score -= 15
        
        if any(kw in user for kw in ["啥是", "啥玩意儿", "怎么"]):
            problems.append({"turn": i, "problem": "询问业务", "suggestion": "应清晰解释"})
            score -= 10
        
        dialect = ["收到咯", "冇", "整咯", "晓得咯", "啥子"]
        if any(kw in user for kw in dialect):
            problems.append({"turn": i, "problem": "方言", "suggestion": "应识别并确认"})
            score -= 5
    
    return {"score": max(0, score), "problems": problems}

def main():
    print("=" * 60)
    print("  电信橙分期话术 + 标签 完整测试")
    print("=" * 60)
    
    results = []
    
    print("\n" + "=" * 60)
    print("  📋 测试结果")
    print("=" * 60)
    
    for case in TEST_CASES:
        dialogue = case["dialogue"]
        expected = case["expected_tag"]
        actual = classify_tag(dialogue)
        flow = analyze_flow(dialogue)
        
        tag_ok = actual == expected
        flow_ok = flow["score"] >= 80
        
        status = "✅" if tag_ok else "❌"
        flow_icon = "💚" if flow_ok else "💛"
        
        print(f"\n{status}{flow_icon} {case['name']}")
        print(f"   标签: 期望={expected} 实际={actual}")
        print(f"   流程: {flow['score']}分")
        
        if flow["problems"]:
            for p in flow["problems"]:
                print(f"   - {p['problem']}: {p['suggestion']}")
        
        results.append({
            "name": case["name"],
            "tag_ok": tag_ok,
            "actual": actual,
            "expected": expected,
            "flow_score": flow["score"],
            "problems": flow["problems"]
        })
    
    # 统计
    tag_errors = sum(1 for r in results if not r["tag_ok"])
    avg_score = sum(r["flow_score"] for r in results) / len(results)
    total_problems = sum(len(r["problems"]) for r in results)
    
    print("\n" + "=" * 60)
    print("  📊 统计")
    print("=" * 60)
    print(f"   总测试: {len(results)}")
    print(f"   标签正确: {len(results) - tag_errors}")
    print(f"   标签错误: {tag_errors}")
    print(f"   流程评分平均: {avg_score:.1f}%")
    print(f"   话术问题总数: {total_problems}")
    
    # 生成报告
    print("\n" + "=" * 60)
    print("  📄 生成优化报告")
    print("=" * 60)
    
    report = f"""# 电信橙分期话术 + 标签优化报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 一、测试统计

| 指标 | 值 |
|------|-----|
| 总测试数 | {len(results)} |
| 标签正确 | {len(results) - tag_errors} |
| 标签错误 | {tag_errors} |
| 流程评分平均 | {avg_score:.1f}% |
| 话术问题数 | {total_problems} |

---

## 二、测试结果

| 场景 | 期望标签 | 实际标签 | 状态 | 流程评分 |
|------|----------|----------|------|----------|
"""
    
    for r in results:
        status = "✅" if r["tag_ok"] else "❌"
        report += f"| {r['name']} | {r['expected']} | {r['actual']} | {status} | {r['flow_score']} |\n"
    
    report += f"""

---

## 三、话术问题分析

### 问题类型统计

| 问题类型 | 出现次数 | 建议话术 |
|----------|----------|----------|
"""
    
    # 统计问题
    problem_count = {}
    for r in results:
        for p in r["problems"]:
            prob = p["problem"]
            if prob not in problem_count:
                problem_count[prob] = {"count": 0, "suggestion": p["suggestion"]}
            problem_count[prob]["count"] += 1
    
    for prob, info in sorted(problem_count.items(), key=lambda x: x[1]["count"], reverse=True):
        report += f"| {prob} | {info['count']} | {info['suggestion']} |\n"
    
    report += """

---

## 四、话术优化建议

### 1. 开场白优化

```markdown
❌ 旧: "您好，我是电信客服"
✅ 新: "您好，请问是[姓名]吗？我是电信客服，想回访橙分期业务，请问方便吗？"
```

### 2. 等待处理

```markdown
客户: "等一下"
AI: "好的，请您先忙，我等您一下。"
```

### 3. 语气词处理

```markdown
客户: "嗯"
AI: "请问您方便吗？"
  └── 仍语气词 → "好的，打扰了，再见"
```

### 4. 投诉处理

```markdown
客户: "我要投诉"
AI: "非常抱歉给您带来不便，请问是什么问题呢？"
```

### 5. 业务解释

```markdown
客户: "啥是橙分期？"
AI: "橙分期是电信分期还款业务，您每月还款..."
```

---

## 五、标签判定规则（优化后）

1. **套机套现**: 未收到商品 + 无付费
2. **违规商品**: 收到耳机/充电宝/锅等
3. **营销缺失**: 收到商品但不知晓/投诉
4. **正常**: 收到商品 + 知晓合约
5. **未沟通**: 语气词 < 3轮

---

## 六、下一步行动

### 高优先级
- [ ] 更新开场白话术
- [ ] 添加等待/投诉话术
- [ ] 增加方言确认

### 中优先级
- [ ] 应用优化后的标签规则
- [ ] 丰富方言词库
- [ ] 增加测试覆盖

"""
    
    # 保存报告
    report_path = "FLOW_TAG_OPTIMIZATION_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"   报告已保存: {report_path}")
    
    print("\n" + "=" * 60)
    if tag_errors == 0:
        print("  🎉 所有标签测试通过！")
    else:
        print(f"  ⚠️  {tag_errors} 个标签测试失败")
    print("=" * 60)

if __name__ == "__main__":
    main()
