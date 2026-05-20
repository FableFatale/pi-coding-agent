#!/usr/bin/env python
"""
电信橙分期标签测试 + 优化报告生成
完整版：测试 → 分析 → 优化建议 → 生成报告
"""
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


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
    "茶吧机", "破壁机", "家电", "蓝牙耳机", "微波炉", "插座", "电动车",
    "烤箱", "保温杯", "电子产品", "电子设备", "电器", "吹风机", "电瓶车",
    "礼包", "蒸汽锅", "小礼品", "电动自行车", "唱歌设备", "烤盘", "烧水壶",
    "除螨仪", "词典笔", "绞肉机", "话费等"
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
    "小爱同学", "小天才", "空调", "冰箱", "电视", "洗衣机", "血压计",
    "点读笔", "血压仪", "电饭煲", "老年机", "学习机", "家教机", "智慧大屏",
    "智能传感器", "传感器", "智能窗帘电机", "智能机器人", "机器人",
    "学习桌", "助听器", "热水器", "游戏机", "台灯", "体脂秤", "电子秤",
    "体重秤", "灯", "秤", "煮饭锅", "煮饭煲", "插头", "插座", "插排", "老人机"
]


# ============================================================
# 优化后的标签分类器
# ============================================================

class OptimizedTagClassifier:
    """优化后的标签分类器 - 完整实现上下文累积"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.conversation = []
        self.user_inputs = []
        self.full_text = ""
        self.turns = 0
        self.received_goods = None
        self.received_goods_confirmed = False
        self.goods_type = None
        self.has_payment = False
        self.knows_contract = None
        self.knows_contract_confirmed = False
        self.is_cancelled = False
        self.is_fraud = False
        self.is_complaint = False

    def process_dialogue(self, conversation: list):
        self.conversation = conversation
        self.turns = len(conversation)
        all_user_text = " ".join([turn.get("user", "") for turn in conversation])
        self.full_text = all_user_text
        self.user_inputs = [turn.get("user", "") for turn in conversation]

        self._extract_all_info()

    def _extract_all_info(self):
        """提取所有信息 - 全文分析"""
        text = self.full_text

        # 1. 付费关键词 - 付费即已收到
        payment_keywords = [
            "付费", "花钱", "自费", "买", "花了", "花了钱", "花咯", "花啦",
            "整咯", "整了个", "入手", "购买", "买的", "买咯", "搞咯", "搞了个"
        ]
        if any(kw in text for kw in payment_keywords):
            self.has_payment = True
            self.received_goods = True

        # 2. 已收到商品
        received_keywords = [
            "拿到了", "收到了", "有", "收到了咯", "拿到咯", "收到啰", "拿到啰",
            "有收到", "拿到手了", "已经拿到", "拿到喽", "整了个", "装好了",
            "安装好了", "买咯", "买了个", "搞了个", "係啊"
        ]
        if any(kw in text for kw in received_keywords):
            self.received_goods = True
            self.received_goods_confirmed = True

        # 3. 未收到商品
        not_received_keywords = [
            "没拿到", "没收到", "没有", "什么都没", "只有钱", "木有", "冇",
            "根本冇", "根本没", "没得", "未收到", "没有收到", "未拿到",
            "没有拿到", "啥都没", "冇收到"
        ]
        if any(kw in text for kw in not_received_keywords):
            self.received_goods = False

        # 4. 商品类型
        all_products = set(NORMAL_PRODUCTS + VIOLATION_PRODUCTS)
        for product in all_products:
            if product in text:
                self.goods_type = product
                break

        # 5. 方言商品表达
        dialect_goods = {
            "手机": ["手几", "电话", "话机"],
            "宽带": ["网", "wifi", "宽贷"],
        }
        for goods, dialects in dialect_goods.items():
            if any(d in text for d in dialects):
                self.goods_type = goods

        # 6. 知晓合约
        knows_keywords = [
            "知道", "明白", "理解", "清楚", "晓得", "晓得了", "知道咯",
            "晓得咯", "了解", "清楚了", "知道得嘛", "知道得了"
        ]
        if any(kw in text for kw in knows_keywords):
            self.knows_contract = True
            self.knows_contract_confirmed = True

        # 7. 不知晓合约
        not_knows_keywords = [
            "不知道", "不晓得", "不晓滴", "不造啊", "不造", "没办过",
            "没要求", "不清", "啥是", "啥玩意儿", "咋还", "咋整",
            "咋回事", "不理解", "不记得"
        ]
        if any(kw in text for kw in not_knows_keywords):
            self.knows_contract = False

        # 8. 投诉/被骗
        complaint_keywords = [
            "投诉", "骗", "骗人", "被骗", "被骗了", "被骗咯", "被坑",
            "被坑咯", "欺诈", "虚假", "坑", "坑人", "垃圾", "太差",
            "不满", "不满意"
        ]
        if any(kw in text for kw in complaint_keywords):
            self.is_complaint = True
            if "骗" in text or "坑" in text:
                self.is_fraud = True

    def classify(self) -> str:
        """分类 - 按优先级"""

        # 优先级1: 未沟通
        if self._is_no_communication():
            return "未沟通"

        # 优先级2: 套机套现
        if self._is_cash_out():
            return "套机套现"

        # 优先级3: 违规商品
        if self._is_violation_product():
            return "违规商品"

        # 优先级4: 营销缺失
        if self._is_marketing_lack():
            return "营销缺失"

        # 优先级5: 正常
        if self._is_normal():
            return "正常"

        # 兜底: 营销缺失
        return "营销缺失"

    def _is_no_communication(self) -> bool:
        """未沟通判定"""
        # 零互动
        if self.turns == 0:
            return True

        # 轮次很少且无有效信息
        if self.turns < 3 and self.received_goods is None and self.knows_contract is None:
            filler_only = all(
                inp.strip() in ["", "嗯", "啊", "哦", "嗯嗯", "啊啊", "嗯嗯嗯", "撒", "嘛"]
                for inp in self.user_inputs
            )
            if filler_only:
                return True

        return False

    def _is_cash_out(self) -> bool:
        """套机套现判定"""
        # 已收到商品=False 且 无付费
        if self.received_goods is False and not self.has_payment:
            return True
        return False

    def _is_violation_product(self) -> bool:
        """违规商品判定"""
        if self.received_goods and self.goods_type:
            if self.goods_type in VIOLATION_PRODUCTS:
                return True
        return False

    def _is_marketing_lack(self) -> bool:
        """营销缺失判定"""
        # 收到商品但不知晓合约
        if self.received_goods is True and self.knows_contract is False:
            return True

        # 被骗
        if self.is_fraud:
            return True

        # 投诉+收到商品
        if self.is_complaint and self.received_goods:
            return True

        # 询问业务定义但没明确知晓
        if ("啥是" in self.full_text or "啥玩意儿" in self.full_text) and self.received_goods:
            return True

        return False

    def _is_normal(self) -> bool:
        """正常判定"""
        if self.received_goods and self.goods_type:
            if self.goods_type in NORMAL_PRODUCTS:
                if self.knows_contract is True:
                    return True
        return False

    def get_output(self) -> dict:
        return {"tags": [self.classify()]}


# ============================================================
# 测试用例
# ============================================================

TEST_CASES = [
    # 未沟通
    {"name": "未沟通-零互动", "category": "未沟通", "dialogue": [{"user": "", "ai": "您好"}], "expected": "未沟通"},
    {"name": "未沟通-语气词", "category": "未沟通", "dialogue": [{"user": "嗯", "ai": "您好"}, {"user": "嗯嗯", "ai": "请问"}], "expected": "未沟通"},
    {"name": "未沟通-中途挂机", "category": "未沟通", "dialogue": [{"user": "等一下", "ai": "好的"}, {"user": "", "ai": "喂？"}], "expected": "未沟通"},

    # 正常
    {"name": "正常-手机", "category": "正常", "dialogue": [{"user": "拿到了华为手机", "ai": "好的"}, {"user": "知道每月还款", "ai": "好的"}], "expected": "正常"},
    {"name": "正常-宽带", "category": "正常", "dialogue": [{"user": "装好了宽带", "ai": "好的"}, {"user": "晓得咯", "ai": "好的"}], "expected": "正常"},
    {"name": "正常-方言粤语", "category": "正常", "dialogue": [{"user": "係啊收到咯", "ai": "请问"}, {"user": "整了个路由器", "ai": "好的"}, {"user": "知道得嘛", "ai": "好的"}], "expected": "正常"},
    {"name": "正常-方言东北", "category": "正常", "dialogue": [{"user": "整了个宽带", "ai": "好的"}, {"user": "知道得了", "ai": "好的"}], "expected": "正常"},

    # 套机套现
    {"name": "套机套现-只收钱", "category": "套机套现", "dialogue": [{"user": "我只收到钱没拿东西", "ai": "好的"}], "expected": "套机套现"},
    {"name": "套机套现-什么都没收", "category": "套机套现", "dialogue": [{"user": "啥都没收到", "ai": "请问"}, {"user": "只有折现", "ai": "好的"}], "expected": "套机套现"},
    {"name": "套机套现-方言", "category": "套机套现", "dialogue": [{"user": "根本冇收到咯", "ai": "请问"}, {"user": "只有钱", "ai": "好的"}], "expected": "套机套现"},

    # 违规商品
    {"name": "违规商品-耳机", "category": "违规商品", "dialogue": [{"user": "拿到了耳机", "ai": "好的"}, {"user": "知道", "ai": "好的"}], "expected": "违规商品"},
    {"name": "违规商品-空气炸锅", "category": "违规商品", "dialogue": [{"user": "整了个空气炸锅", "ai": "好的"}, {"user": "晓得咯", "ai": "好的"}], "expected": "违规商品"},
    {"name": "违规商品-锅", "category": "违规商品", "dialogue": [{"user": "我拿了个锅", "ai": "好的"}, {"user": "知道", "ai": "好的"}], "expected": "违规商品"},
    {"name": "违规商品-充电宝", "category": "违规商品", "dialogue": [{"user": "拿到了个充电宝", "ai": "好的"}, {"user": "知道", "ai": "好的"}], "expected": "违规商品"},
    {"name": "违规商品-付费但违规", "category": "违规商品", "dialogue": [{"user": "我花钱买的耳机", "ai": "好的"}], "expected": "违规商品"},

    # 营销缺失
    {"name": "营销缺失-不知业务", "category": "营销缺失", "dialogue": [{"user": "我不知道啥是橙分期", "ai": "请问"}, {"user": "整了个手机", "ai": "好的"}], "expected": "营销缺失"},
    {"name": "营销缺失-投诉", "category": "营销缺失", "dialogue": [{"user": "我要投诉", "ai": "请问"}, {"user": "被骗了", "ai": "抱歉"}], "expected": "营销缺失"},
    {"name": "营销缺失-反问", "category": "营销缺失", "dialogue": [{"user": "啥是橙分期？", "ai": "橙分期是..."}, {"user": "咋还？", "ai": "每月..."}], "expected": "营销缺失"},
    {"name": "营销缺失-被骗", "category": "营销缺失", "dialogue": [{"user": "我被骗了", "ai": "请问"}, {"user": "说免费结果扣钱", "ai": "抱歉"}], "expected": "营销缺失"},
    {"name": "营销缺失-收到但不知晓", "category": "营销缺失", "dialogue": [{"user": "拿到了手机", "ai": "好的"}, {"user": "不知道", "ai": "好的"}], "expected": "营销缺失"},

    # 边界
    {"name": "边界-矛盾表述", "category": "边界", "dialogue": [{"user": "收到了但好像又没收到", "ai": "请问"}, {"user": "整了个手机", "ai": "好的"}, {"user": "知道", "ai": "好的"}], "expected": "正常"},
    {"name": "边界-长对话", "category": "边界", "dialogue": [{"user": "我当时办的时候业务员说了一堆", "ai": "好的"}, {"user": "他说每月只要付很少的钱就能拿个手机", "ai": "好的"}, {"user": "拿到了华为", "ai": "好的"}, {"user": "知道", "ai": "好的"}], "expected": "正常"},
]


# ============================================================
# 测试报告生成
# ============================================================

class TestReport:
    """测试报告"""

    def __init__(self):
        self.results = []
        self.timestamp = datetime.now()

    def add_result(self, case, actual, passed):
        self.results.append({
            "name": case["name"],
            "category": case["category"],
            "expected": case["expected"],
            "actual": actual,
            "passed": passed,
            "dialogue": case["dialogue"]
        })

    def generate_html(self, output_path):
        """生成 HTML 报告"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        rate = (passed / total * 100) if total > 0 else 0

        # 按类别分组
        categories = {}
        for r in self.results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>测试报告 - {self.timestamp.strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; background: #f5f7fa; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; margin-bottom: 20px; padding: 20px; background: white; border-radius: 8px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px; }}
        .stat {{ background: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat h3 {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
        .stat .value {{ font-size: 32px; font-weight: bold; }}
        .total {{ border-left: 4px solid #3498db; }}
        .passed {{ border-left: 4px solid #27ae60; }}
        .failed {{ border-left: 4px solid #e74c3c; }}
        .rate {{ border-left: 4px solid #f39c12; }}
        .category {{ background: white; border-radius: 8px; margin-bottom: 20px; overflow: hidden; }}
        .category-header {{ padding: 15px 20px; color: white; font-weight: bold; }}
        .category-header.pass {{ background: #27ae60; }}
        .category-header.fail {{ background: #e74c3c; }}
        .test-item {{ padding: 15px 20px; border-bottom: 1px solid #eee; }}
        .test-item:last-child {{ border-bottom: none; }}
        .test-item.pass {{ background: #f0fff4; }}
        .test-item.fail {{ background: #fff5f5; }}
        .test-name {{ font-weight: bold; color: #333; margin-bottom: 5px; }}
        .test-result {{ font-size: 13px; color: #666; }}
        .test-result span {{ margin-right: 15px; }}
        .pass {{ color: #27ae60; }}
        .fail {{ color: #e74c3c; }}
        .dialogue {{ margin-top: 10px; font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 电信橙分期标签测试报告</h1>
        <div class="stats">
            <div class="stat total">
                <h3>总测试数</h3>
                <div class="value">{total}</div>
            </div>
            <div class="stat passed">
                <h3>通过</h3>
                <div class="value">{passed}</div>
            </div>
            <div class="stat failed">
                <h3>失败</h3>
                <div class="value">{failed}</div>
            </div>
            <div class="stat rate">
                <h3>通过率</h3>
                <div class="value">{rate:.1f}%</div>
            </div>
        </div>
"""

        for cat_name, items in categories.items():
            cat_pass = sum(1 for i in items if i["passed"])
            cat_total = len(items)
            has_fail = any(not i["passed"] for i in items)

            html += f"""
        <div class="category">
            <div class="category-header {'pass' if not has_fail else 'fail'}">
                {cat_name} ({cat_pass}/{cat_total})
            </div>
"""

            for item in items:
                status_class = "pass" if item["passed"] else "fail"
                status_text = "✅ 通过" if item["passed"] else "❌ 失败"

                html += f"""
            <div class="test-item {status_class}">
                <div class="test-name">{item['name']}</div>
                <div class="test-result">
                    <span class="{status_class}">{status_text}</span>
                    <span>期望: {item['expected']}</span>
                    <span>实际: {item['actual']}</span>
                </div>
                <div class="dialogue">
                    对话轮次: {len(item['dialogue'])}
                </div>
            </div>
"""

            html += """
        </div>
"""

        html += f"""
        <div style="text-align: center; color: #999; padding: 20px;">
            生成时间: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return output_path

    def generate_markdown(self, output_path):
        """生成 Markdown 报告"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        rate = (passed / total * 100) if total > 0 else 0

        md = f"""# 电信橙分期标签测试报告

生成时间: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

## 测试统计

| 指标 | 值 |
|------|-----|
| 总测试数 | {total} |
| 通过 | {passed} |
| 失败 | {failed} |
| 通过率 | {rate:.1f}% |

## 测试结果

"""

        # 按类别分组
        categories = {}
        for r in self.results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)

        for cat_name, items in categories.items():
            cat_pass = sum(1 for i in items if i["passed"])
            cat_total = len(items)

            md += f"\n### {cat_name} ({cat_pass}/{cat_total})\n\n"
            md += "| 场景 | 期望 | 实际 | 状态 |\n"
            md += "|------|------|------|------|\n"

            for item in items:
                status = "✅" if item["passed"] else "❌"
                md += f"| {item['name']} | {item['expected']} | {item['actual']} | {status} |\n"

        # 添加优化建议
        md += """

---

## 优化建议

### 1. 方言支持

根据测试结果，建议扩展以下方言词库：

**粤语**：
- 收到咯 → 收到了
- 冇 → 没有
- 不晓得咡 → 不知道

**四川**：
- 整咯/整了个 → 买了个
- 晓得咯 → 知道了
- 啥子/啥玩意儿 → 什么

**东北**：
- 整了个 → 买了个
- 知道得了 → 知道了

### 2. 边界情况处理

- 矛盾表述："收到了但好像没收到" → 以肯定表述为准
- 语气词：<3轮且无商品信息 → 未沟通
- 超长输入：提取关键词分析

### 3. 上下文累积

- 关键词永久标记
- 首次明确表述优先
- 全文扫描，不只看最后一轮

"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md)

        return output_path


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 60)
    print("  电信橙分期标签测试 + 优化报告生成")
    print("=" * 60)

    # 运行测试
    report = TestReport()
    classifier = OptimizedTagClassifier()

    print("\n📋 运行测试...\n")

    for case in TEST_CASES:
        classifier.reset()
        classifier.process_dialogue(case["dialogue"])
        actual = classifier.classify()
        passed = actual == case["expected"]

        report.add_result(case, actual, passed)

        status = "✅" if passed else "❌"
        print(f"  {status} [{case['category']}] {case['name']}")
        if not passed:
            print(f"      期望: {case['expected']} | 实际: {actual}")

    # 生成报告
    print("\n" + "=" * 60)
    print("  📄 生成测试报告")
    print("=" * 60)

    total = len(report.results)
    passed = sum(1 for r in report.results if r["passed"])
    failed = total - passed
    rate = (passed / total * 100) if total > 0 else 0

    print(f"\n  📊 测试统计:")
    print(f"     总测试数: {total}")
    print(f"     通过: {passed}")
    print(f"     失败: {failed}")
    print(f"     通过率: {rate:.1f}%")

    # 生成 HTML 报告
    html_path = report.generate_html("test_report.html")
    print(f"\n  📄 HTML报告: {html_path}")

    # 生成 Markdown 报告
    md_path = report.generate_markdown("test_report.md")
    print(f"  📄 Markdown报告: {md_path}")

    # 生成 JSON 数据
    json_path = "test_results.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total": total,
            "passed": passed,
            "failed": failed,
            "rate": rate,
            "results": report.results
        }, f, ensure_ascii=False, indent=2)
    print(f"  📄 JSON数据: {json_path}")

    print("\n" + "=" * 60)
    if failed == 0:
        print("  🎉 所有测试通过！")
    else:
        print(f"  ⚠️  {failed} 个测试失败，请查看报告")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
