#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
电信橙分期 - 完整测试与优化系统
整合话术测试、标签测试、优化分析
"""
import sys
import os
from datetime import datetime

# 确保路径正确
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# 配置
# ============================================================

VERSION = "3.0"
TITLE = "电信橙分期话术与标签优化系统"


# ============================================================
# 标签库
# ============================================================

TAG_WHITELIST = ["套机套现", "违规商品", "营销缺失", "正常", "未沟通"]

VIOLATION_PRODUCTS = [
    "耳机", "充电宝", "电视机", "空气炸锅", "锅", "净水器", "扫地机",
    "电暖桌", "压力煲", "高压锅", "净水机", "智家大礼包", "炸锅",
    "电火锅", "烤火炉", "电压锅", "热水器", "油烟机", "饮水机",
    "一体锅", "烤锅", "彩电", "蒸锅", "鸳鸯锅", "吸尘器", "热风机",
    "豆浆机", "电水壶", "电暖炉", "消毒柜", "榨汁机", "燃气灶",
    "挂烫机", "风扇", "电蒸锅", "电热锅", "电锅", "养生壶", "打印机",
    "电饼铛", "净化器", "礼品", "净水器", "茶具", "炒锅", "电磁炉",
    "茶吧机", "破壁机", "家电", "蓝牙耳机", "微波炉", "插座", "电动车"
]

NORMAL_PRODUCTS = [
    "手机", "路由器", "智能手表", "ipad", "云电脑", "VR", "电脑",
    "平板电脑", "光猫", "机顶盒", "宽带设备", "宽带", "WiFi", "fttr",
    "智能机", "安装设备", "光纤", "全光", "电话手表", "华为", "oppo",
    "vivo", "红米", "小米", "荣耀", "苹果", "小度", "天猫精灵",
    "智能音响", "智能猫眼", "智能门锁", "智能门铃", "儿童手表", "摄像头",
    "门锁", "智能报警器", "手表", "手环", "智能开关", "门铃", "音响",
    "音箱", "电饭锅", "猫眼", "指纹锁", "报警器", "监控", "网关",
    "智能产品", "智能锁", "mate60", "iphone", "一加", "真我", "中兴",
    "三星", "网线", "智慧屏", "平板", "pad", "笔记本", "合约机",
    "小爱同学", "小天才", "空调", "冰箱", "电视", "洗衣机", "血压计"
]

# 方言语义映射
DIALECT_MAP = {
    # 粤语
    "收到咯": "收到了", "拿到咯": "拿到了", "冇": "没有", "係啊": "是的",
    "不晓得咡": "不知道", "知道得嘛": "知道了",
    # 四川
    "整咯": "买了", "整了个": "买了个", "晓得咯": "知道了",
    "啥子": "什么", "咋整": "怎么回事",
    # 东北
    "知道得了": "知道了"
}


# ============================================================
# 标签分类器
# ============================================================

class TagClassifier:
    """标签分类器"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.dialogue = []
        self.received_goods = None
        self.goods_type = None
        self.has_payment = False
        self.knows_contract = None
        self.is_complaint = False
        self.is_fraud = False
        self.turns = 0

    def process(self, dialogue):
        """处理对话"""
        self.dialogue = dialogue
        self.turns = len(dialogue)

        # 合并所有用户输入
        full_text = " ".join([t.get("user", "") for t in dialogue])

        # 转换方言
        for dialect, standard in DIALECT_MAP.items():
            full_text = full_text.replace(dialect, standard)

        # 检测付费
        payment_kws = ["付费", "花钱", "自费", "买", "花了", "买了个"]
        if any(kw in full_text for kw in payment_kws):
            self.has_payment = True
            self.received_goods = True

        # 检测收到商品
        received_kws = ["拿到了", "收到了", "有", "买了个", "装好了"]
        if any(kw in full_text for kw in received_kws):
            self.received_goods = True

        # 检测未收到商品
        not_received_kws = ["没收到", "什么都没", "只有钱", "木有"]
        if any(kw in full_text for kw in not_received_kws):
            self.received_goods = False

        # 检测商品类型
        for product in NORMAL_PRODUCTS + VIOLATION_PRODUCTS:
            if product in full_text:
                self.goods_type = product
                break

        # 检测知晓合约
        knows_kws = ["知道", "明白", "清楚", "晓得"]
        not_knows_kws = ["不知道", "不晓得", "啥是", "咋整"]
        if any(kw in full_text for kw in knows_kws):
            self.knows_contract = True
        if any(kw in full_text for kw in not_knows_kws):
            self.knows_contract = False

        # 检测投诉
        complaint_kws = ["投诉", "骗", "被骗", "欺诈"]
        if any(kw in full_text for kw in complaint_kws):
            self.is_complaint = True
            self.is_fraud = "骗" in full_text

    def classify(self):
        """分类"""
        # 未沟通
        if self.turns <= 2 and self.received_goods is None:
            if all(t.get("user", "").strip() in ["", "嗯", "啊", "哦"] for t in self.dialogue):
                return "未沟通"

        # 套机套现
        if self.received_goods is False and not self.has_payment:
            return "套机套现"

        # 违规商品
        if self.received_goods and self.goods_type in VIOLATION_PRODUCTS:
            return "违规商品"

        # 营销缺失
        if self.received_goods and self.knows_contract is False:
            return "营销缺失"
        if self.is_fraud:
            return "营销缺失"
        if self.is_complaint and self.received_goods:
            return "营销缺失"

        # 正常
        if self.received_goods and self.goods_type in NORMAL_PRODUCTS and self.knows_contract:
            return "正常"

        # 兜底
        return "营销缺失"


# ============================================================
# 话术分析器
# ============================================================

class FlowAnalyzer:
    """话术流程分析器"""

    def __init__(self):
        self.rules = [
            ("等待/忙碌", ["等一下", "稍等", "忙"], 10),
            ("语气词", ["嗯", "啊", "哦", "嗯嗯"], 5),
            ("投诉/不满", ["投诉", "骗", "被骗"], 15),
            ("询问业务", ["啥是", "啥玩意儿", "怎么", "为什么"], 10),
            ("方言", ["收到咯", "冇", "整咯", "晓得咯"], 5),
            ("未收到", ["没收到", "什么都没"], 10),
        ]

    def analyze(self, dialogue):
        """分析话术"""
        score = 100
        issues = []

        for turn in dialogue:
            user = turn.get("user", "")
            for rule_name, keywords, penalty in self.rules:
                if any(kw in user for kw in keywords):
                    if rule_name not in [i["name"] for i in issues]:
                        issues.append({
                            "name": rule_name,
                            "turn": dialogue.index(turn),
                            "penalty": penalty
                        })
                        score -= penalty

        return {"score": max(0, score), "issues": issues}


# ============================================================
# 测试用例
# ============================================================

TEST_CASES = [
    # 正常场景
    {"name": "正常-标准流程", "dialogue": [
        {"user": "是的", "ai": "请问您拿到了什么商品？"},
        {"user": "拿到了华为手机", "ai": "请问您知道还款吗？"},
        {"user": "知道", "ai": "好的感谢配合"}
    ], "expected": "正常"},

    {"name": "正常-宽带", "dialogue": [
        {"user": "装好了宽带", "ai": "请问您知道合约吗？"},
        {"user": "晓得咯", "ai": "好的"}
    ], "expected": "正常"},

    {"name": "正常-方言粤语", "dialogue": [
        {"user": "係啊收到咯", "ai": "请问是？"},
        {"user": "整了个路由器", "ai": "好的请问知道合约吗？"},
        {"user": "知道得嘛", "ai": "好的"}
    ], "expected": "正常"},

    # 套机套现
    {"name": "套机套现-只收钱", "dialogue": [
        {"user": "我只收到钱没拿东西", "ai": "好的"}
    ], "expected": "套机套现"},

    {"name": "套机套现-什么都没", "dialogue": [
        {"user": "啥都没收到", "ai": "请问？"},
        {"user": "只有折现", "ai": "好的"}
    ], "expected": "套机套现"},

    {"name": "套机套现-方言", "dialogue": [
        {"user": "根本冇收到咯", "ai": "请问？"},
        {"user": "只有钱", "ai": "好的"}
    ], "expected": "套机套现"},

    # 违规商品
    {"name": "违规商品-耳机", "dialogue": [
        {"user": "拿到了耳机", "ai": "好的请问知道还款吗？"},
        {"user": "知道", "ai": "好的"}
    ], "expected": "违规商品"},

    {"name": "违规商品-空气炸锅", "dialogue": [
        {"user": "整了个空气炸锅", "ai": "好的请问知道合约吗？"},
        {"user": "晓得咯", "ai": "好的"}
    ], "expected": "违规商品"},

    {"name": "违规商品-锅", "dialogue": [
        {"user": "我拿了个锅", "ai": "好的请问知道合约吗？"},
        {"user": "知道", "ai": "好的"}
    ], "expected": "违规商品"},

    {"name": "违规商品-付费", "dialogue": [
        {"user": "我花钱买的耳机", "ai": "好的"}
    ], "expected": "违规商品"},

    # 营销缺失
    {"name": "营销缺失-不知业务", "dialogue": [
        {"user": "我不知道啥是橙分期", "ai": "请问？"},
        {"user": "整了个手机", "ai": "好的"}
    ], "expected": "营销缺失"},

    {"name": "营销缺失-投诉", "dialogue": [
        {"user": "我要投诉", "ai": "请问？"},
        {"user": "被骗了", "ai": "抱歉"}
    ], "expected": "营销缺失"},

    {"name": "营销缺失-反问", "dialogue": [
        {"user": "啥是橙分期？", "ai": "橙分期是..."},
        {"user": "咋还？", "ai": "每月..."}
    ], "expected": "营销缺失"},

    # 未沟通
    {"name": "未沟通-零互动", "dialogue": [
        {"user": "", "ai": "您好"}
    ], "expected": "未沟通"},

    {"name": "未沟通-语气词", "dialogue": [
        {"user": "嗯", "ai": "您好"},
        {"user": "嗯嗯", "ai": "请问"}
    ], "expected": "未沟通"},

    {"name": "未沟通-挂机", "dialogue": [
        {"user": "等一下", "ai": "好的"},
        {"user": "", "ai": "喂？"}
    ], "expected": "未沟通"},
]


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 60)
    print(f"  {TITLE}")
    print(f"  版本: {VERSION}")
    print("=" * 60)

    classifier = TagClassifier()
    flow_analyzer = FlowAnalyzer()

    results = []

    print("\n" + "=" * 60)
    print("  📋 测试结果")
    print("=" * 60)

    for case in TEST_CASES:
        dialogue = case["dialogue"]
        expected = case["expected"]

        # 标签分类
        classifier.reset()
        classifier.process(dialogue)
        actual_tag = classifier.classify()

        # 话术分析
        flow_result = flow_analyzer.analyze(dialogue)

        tag_ok = actual_tag == expected
        flow_ok = flow_result["score"] >= 80

        status = "✅" if tag_ok else "❌"
        flow_icon = "💚" if flow_ok else "💛"

        print(f"\n{status}{flow_icon} {case['name']}")
        print(f"   标签: 期望={expected} 实际={actual_tag}")
        print(f"   流程: {flow_result['score']}分")

        if flow_result["issues"]:
            for issue in flow_result["issues"]:
                print(f"   ⚠️ {issue['name']} (扣{issue['penalty']}分)")

        results.append({
            "name": case["name"],
            "expected": expected,
            "actual": actual_tag,
            "tag_ok": tag_ok,
            "flow_score": flow_result["score"],
            "flow_issues": flow_result["issues"]
        })

    # 统计
    total = len(results)
    tag_errors = sum(1 for r in results if not r["tag_ok"])
    avg_flow = sum(r["flow_score"] for r in results) / total
    total_issues = sum(len(r["flow_issues"]) for r in results)

    print("\n" + "=" * 60)
    print("  📊 统计")
    print("=" * 60)
    print(f"   总测试: {total}")
    print(f"   标签正确: {total - tag_errors}")
    print(f"   标签错误: {tag_errors}")
    print(f"   流程评分平均: {avg_flow:.1f}%")
    print(f"   话术问题数: {total_issues}")

    # 生成报告
    print("\n" + "=" * 60)
    print("  📄 生成报告")
    print("=" * 60)

    report = f"""# 电信橙分期话术与标签测试报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 测试统计

| 指标 | 值 |
|------|-----|
| 总测试 | {total} |
| 标签正确 | {total - tag_errors} |
| 标签错误 | {tag_errors} |
| 流程评分平均 | {avg_flow:.1f}% |
| 话术问题数 | {total_issues} |

## 测试结果

| 场景 | 期望 | 实际 | 状态 | 流程评分 |
|------|------|------|------|----------|
"""

    for r in results:
        status = "✅" if r["tag_ok"] else "❌"
        report += f"| {r['name']} | {r['expected']} | {r['actual']} | {status} | {r['flow_score']} |\n"

    report += """
## 优化建议

### 高优先级

1. 增加方言识别和确认话术
2. 添加等待/投诉处理话术
3. 完善业务解释话术

### 中优先级

1. 优化语气词识别和二次确认
2. 增加未收到商品的处理话术
3. 丰富违规商品库

---
*报告自动生成*
"""

    # 保存报告
    report_path = os.path.join(
        os.path.dirname(__file__),
        "reports",
        f"TEST_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"   报告已保存: {report_path}")

    print("\n" + "=" * 60)
    if tag_errors == 0:
        print("  🎉 所有标签测试通过！")
    else:
        print(f"  ⚠️  {tag_errors} 个标签测试失败")
    print("=" * 60)

    return 0 if tag_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
