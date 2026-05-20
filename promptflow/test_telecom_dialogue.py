#!/usr/bin/env python
"""
电信橙分期标签判定 - 完整对话测试
支持测试报告生成
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
# 标签分类器
# ============================================================

class TelecomTagClassifier:
    """电信标签分类器 - 基于完整对话上下文"""

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
        self.is_transfer = False
        self.hung_up = False
        self.no_response = False

    def process_dialogue(self, conversation: list):
        self.conversation = conversation
        self.turns = len(conversation)
        all_user_text = " ".join([turn.get("user", "") for turn in conversation])
        self.full_text = all_user_text
        self.user_inputs = [turn.get("user", "") for turn in conversation]

        self._extract_goods_info()
        self._extract_contract_info()
        self._extract_attitude_info()
        self._check_ending_status()

    def _extract_goods_info(self):
        text = self.full_text

        payment_keywords = ["付费", "花钱", "自费", "买", "花了", "花了钱", "花咯", "花啦",
                          "整咯", "整了个", "入手", "购买", "买的", "买咯"]
        if any(kw in text for kw in payment_keywords):
            self.has_payment = True
            self.received_goods = True

        received_keywords = ["拿到了", "收到了", "有", "拿到了", "收到咯", "拿到咯",
                            "有收到", "拿到手了", "已经拿到", "拿到喽", "整了个", "装好了",
                            "安装好了", "买咯", "买了个", "搞了个"]
        if any(kw in text for kw in received_keywords):
            self.received_goods = True
            self.received_goods_confirmed = True

        not_received_keywords = ["没拿到", "没收到", "没有", "什么都没", "只有钱",
                                "木有", "冇", "根本冇", "根本没", "没得", "未收到",
                                "没有收到", "未拿到", "没有拿到", "啥都没"]
        if any(kw in text for kw in not_received_keywords):
            self.received_goods = False

        dialect_received = ["收到咯", "拿到咯", "收到啰", "拿到啰"]
        if any(kw in text for kw in dialect_received):
            self.received_goods = True
            self.received_goods_confirmed = True

        all_products = set(NORMAL_PRODUCTS + VIOLATION_PRODUCTS)
        for product in all_products:
            if product in text:
                self.goods_type = product
                break

    def _extract_contract_info(self):
        text = self.full_text

        knows_keywords = ["知道", "明白", "理解", "清楚", "晓得", "晓得了",
                         "知道咯", "晓得咯", "了解", "清楚了"]
        if any(kw in text for kw in knows_keywords):
            self.knows_contract = True
            self.knows_contract_confirmed = True

        not_knows_keywords = ["不知道", "不晓得", "不晓滴", "不造啊", "不造",
                             "没办过", "没要求", "不清", "不知道啥", "啥是", "啥玩意儿",
                             "咋还", "咋整", "咋回事", "不理解", "不晓得啥"]
        if any(kw in text for kw in not_knows_keywords):
            self.knows_contract = False

        dialect_known = ["晓得咯", "晓得喽", "晓得了", "知道得嘛", "知道得了"]
        dialect_unknown = ["不晓得咡", "不晓得咯", "母鸡啊"]
        if any(kw in text for kw in dialect_known):
            self.knows_contract = True
        if any(kw in text for kw in dialect_unknown):
            self.knows_contract = False

    def _extract_attitude_info(self):
        text = self.full_text

        complaint_keywords = ["投诉", "骗", "骗人", "被骗", "欺诈", "虚假",
                            "坑", "坑人", "垃圾", "太差", "不满", "不满意"]
        if any(kw in text for kw in complaint_keywords):
            self.is_complaint = True

        fraud_keywords = ["被骗了", "被骗咯", "被坑", "被坑咯", "欺诈"]
        if any(kw in text for kw in fraud_keywords):
            self.is_fraud = True

    def _check_ending_status(self):
        if self.user_inputs:
            last_input = self.user_inputs[-1].strip()
            if last_input in ["", "嗯", "啊", "哦", "嗯嗯", "啊啊"]:
                self.hung_up = True

        if len(self.user_inputs) == 1 and self.user_inputs[0] == "":
            self.no_response = True

        if self.turns < 2 and self.received_goods is None:
            self.hung_up = True

    def classify(self) -> str:
        if self._is_no_communication():
            return "未沟通"
        if self._is_cash_out():
            return "套机套现"
        if self._is_violation_product():
            return "违规商品"
        if self._is_marketing_lack():
            return "营销缺失"
        if self._is_normal():
            return "正常"
        return "营销缺失"

    def _is_no_communication(self) -> bool:
        if self.no_response:
            return True
        if self.turns < 2 and self.received_goods is None:
            return True
        if self.turns <= 2:
            filler_only = all(inp.strip() in ["", "嗯", "啊", "哦", "嗯嗯", "啊啊", "嗯嗯嗯"]
                            for inp in self.user_inputs)
            if filler_only:
                return True
        return False

    def _is_cash_out(self) -> bool:
        if self.received_goods is False and not self.has_payment:
            return True
        return False

    def _is_violation_product(self) -> bool:
        if self.received_goods and self.goods_type:
            if self.goods_type in VIOLATION_PRODUCTS:
                return True
        return False

    def _is_marketing_lack(self) -> bool:
        if self.received_goods is True and self.knows_contract is False:
            return True
        if self.is_fraud:
            return True
        if self.is_complaint and self.received_goods:
            return True
        if "啥是" in self.full_text or "啥玩意儿" in self.full_text:
            if self.received_goods:
                return True
        return False

    def _is_normal(self) -> bool:
        if self.received_goods and self.goods_type:
            if self.goods_type in NORMAL_PRODUCTS:
                if self.knows_contract is True:
                    return True
        return False

    def get_output(self) -> dict:
        return {"tags": [self.classify()]}

    def get_context_summary(self) -> dict:
        return {
            "turns": self.turns,
            "received_goods": self.received_goods,
            "goods_type": self.goods_type,
            "has_payment": self.has_payment,
            "knows_contract": self.knows_contract,
            "is_complaint": self.is_complaint,
            "is_fraud": self.is_fraud,
            "hung_up": self.hung_up,
            "no_response": self.no_response,
            "label": self.classify()
        }


# ============================================================
# 测试报告生成器
# ============================================================

class TestReport:
    """测试报告生成器"""

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.results = []
        self.summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "categories": {}
        }

    def add_result(self, case_name: str, category: str, expected: str, actual: str,
                   passed: bool, dialogue: list, context: dict):
        self.results.append({
            "name": case_name,
            "category": category,
            "expected": expected,
            "actual": actual,
            "passed": passed,
            "dialogue": dialogue,
            "context": context
        })

        self.summary["total"] += 1
        if passed:
            self.summary["passed"] += 1
        else:
            self.summary["failed"] += 1

        if category not in self.summary["categories"]:
            self.summary["categories"][category] = {"total": 0, "passed": 0, "failed": 0}
        self.summary["categories"][category]["total"] += 1
        if passed:
            self.summary["categories"][category]["passed"] += 1
        else:
            self.summary["categories"][category]["failed"] += 1

    def generate_html(self, output_path: str = None):
        """生成 HTML 报告"""
        if output_path is None:
            output_path = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        pass_rate = (self.summary["passed"] / self.summary["total"] * 100) if self.summary["total"] > 0 else 0

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>电信橙分期标签测试报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; background: #f5f7fa; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; margin-bottom: 20px; padding: 20px; background: white; border-radius: 8px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-card h3 {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
        .stat-card .value {{ font-size: 32px; font-weight: bold; color: #333; }}
        .stat-card.total {{ border-left: 4px solid #3498db; }}
        .stat-card.passed {{ border-left: 4px solid #27ae60; }}
        .stat-card.failed {{ border-left: 4px solid #e74c3c; }}
        .stat-card.rate {{ border-left: 4px solid #f39c12; }}
        .category-section {{ background: white; border-radius: 8px; margin-bottom: 20px; overflow: hidden; }}
        .category-header {{ background: #3498db; color: white; padding: 15px 20px; font-weight: bold; }}
        .category-header.failed {{ background: #e74c3c; }}
        .test-item {{ padding: 15px 20px; border-bottom: 1px solid #eee; }}
        .test-item:last-child {{ border-bottom: none; }}
        .test-item.pass {{ background: #f0fff4; }}
        .test-item.fail {{ background: #fff5f5; }}
        .test-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .test-name {{ font-weight: bold; color: #333; }}
        .test-status {{ padding: 4px 12px; border-radius: 4px; font-size: 12px; }}
        .test-status.pass {{ background: #27ae60; color: white; }}
        .test-status.fail {{ background: #e74c3c; color: white; }}
        .dialogue {{ background: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 10px; font-size: 13px; }}
        .dialogue-item {{ margin: 5px 0; }}
        .user {{ color: #27ae60; }}
        .ai {{ color: #3498db; }}
        .context {{ margin-top: 10px; font-size: 12px; color: #666; }}
        .context span {{ margin-right: 15px; }}
        .footer {{ text-align: center; color: #999; margin-top: 20px; padding: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 电信橙分期个性标签测试报告</h1>

        <div class="summary">
            <div class="stat-card total">
                <h3>总测试数</h3>
                <div class="value">{self.summary['total']}</div>
            </div>
            <div class="stat-card passed">
                <h3>通过</h3>
                <div class="value">{self.summary['passed']}</div>
            </div>
            <div class="stat-card failed">
                <h3>失败</h3>
                <div class="value">{self.summary['failed']}</div>
            </div>
            <div class="stat-card rate">
                <h3>通过率</h3>
                <div class="value">{pass_rate:.1f}%</div>
            </div>
        </div>
"""

        # 按类别分组
        categories = {}
        for r in self.results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r)

        for cat_name, items in categories.items():
            cat_info = self.summary["categories"][cat_name]
            cat_pass = cat_info["passed"]
            cat_total = cat_info["total"]
            cat_rate = (cat_pass / cat_total * 100) if cat_total > 0 else 0
            has_failed = cat_info["failed"] > 0

            html += f"""
        <div class="category-section">
            <div class="category-header{' failed' if has_failed else ''}">
                {cat_name} ({cat_pass}/{cat_total} - {cat_rate:.0f}%)
            </div>
"""

            for item in items:
                status_class = "pass" if item["passed"] else "fail"
                status_text = "✅ 通过" if item["passed"] else "❌ 失败"

                html += f"""
            <div class="test-item {status_class}">
                <div class="test-header">
                    <span class="test-name">{item['name']}</span>
                    <span class="test-status {status_class}">{status_text}</span>
                </div>
                <div class="context">
                    <span>期望: {item['expected']}</span>
                    <span>实际: {item['actual']}</span>
                </div>
                <div class="dialogue">
"""

                for turn in item["dialogue"]:
                    user = turn.get("user", "") or "(无输入)"
                    ai = turn.get("ai", "")
                    html += f"""
                    <div class="dialogue-item"><span class="user">用户:</span> {user}</div>
                    <div class="dialogue-item"><span class="ai">AI:</span> {ai}</div>
"""

                ctx = item["context"]
                html += f"""
                </div>
                <div class="context">
                    <span>轮次: {ctx.get('turns', 0)}</span>
                    <span>收到商品: {ctx.get('received_goods', 'N/A')}</span>
                    <span>商品类型: {ctx.get('goods_type', 'N/A')}</span>
                    <span>知晓合约: {ctx.get('knows_contract', 'N/A')}</span>
                </div>
            </div>
"""

            html += """
        </div>
"""

        html += f"""
        <div class="footer">
            <p>生成时间: {self.timestamp}</p>
            <p>测试框架: PromptFlow</p>
        </div>
    </div>
</body>
</html>
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return output_path

    def generate_json(self, output_path: str = None):
        """生成 JSON 报告"""
        if output_path is None:
            output_path = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report = {
            "timestamp": self.timestamp,
            "summary": self.summary,
            "results": self.results
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return output_path

    def print_summary(self):
        """打印摘要"""
        print("\n" + "=" * 60)
        print("  📊 测试摘要")
        print("=" * 60)
        print(f"  总测试数: {self.summary['total']}")
        print(f"  通过: {self.summary['passed']}")
        print(f"  失败: {self.summary['failed']}")
        pass_rate = (self.summary['passed'] / self.summary['total'] * 100) if self.summary['total'] > 0 else 0
        print(f"  通过率: {pass_rate:.1f}%")
        print("\n  📋 分类统计:")
        for cat, stats in self.summary['categories'].items():
            cat_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"    {cat}: {stats['passed']}/{stats['total']} ({cat_rate:.0f}%)")


# ============================================================
# 测试用例
# ============================================================

FULL_DIALOGUE_CASES = [
    # 未沟通
    {"name": "零互动-直接挂断", "category": "未沟通", "dialogue": [{"user": "", "ai": "您好"}], "expected": "未沟通"},
    {"name": "短轮次-只说嗯", "category": "未沟通", "dialogue": [{"user": "嗯", "ai": "您好"}, {"user": "嗯嗯", "ai": "请问"}], "expected": "未沟通"},
    {"name": "中途挂机", "category": "未沟通", "dialogue": [{"user": "等一下", "ai": "好的"}, {"user": "", "ai": "喂？"}], "expected": "未沟通"},

    # 正常
    {"name": "正常-手机", "category": "正常", "dialogue": [{"user": "拿到了华为手机", "ai": "好的"}, {"user": "知道每月还款", "ai": "好的"}], "expected": "正常"},
    {"name": "正常-宽带", "category": "正常", "dialogue": [{"user": "装好了宽带", "ai": "好的"}, {"user": "晓得咯", "ai": "好的"}], "expected": "正常"},
    {"name": "正常-方言", "category": "正常", "dialogue": [{"user": "係啊收到咯", "ai": "请问"}, {"user": "整了个路由器", "ai": "好的"}, {"user": "知道得嘛", "ai": "好的"}], "expected": "正常"},
    {"name": "正常-路由器", "category": "正常", "dialogue": [{"user": "买了个路由器", "ai": "好的"}, {"user": "知道", "ai": "好的"}], "expected": "正常"},

    # 套机套现
    {"name": "套机套现-只收钱", "category": "套机套现", "dialogue": [{"user": "我只收到钱没拿东西", "ai": "好的"}], "expected": "套机套现"},
    {"name": "套机套现-什么都没收", "category": "套机套现", "dialogue": [{"user": "啥都没收到", "ai": "请问"}, {"user": "只有折现", "ai": "好的"}], "expected": "套机套现"},
    {"name": "套机套现-方言", "category": "套机套现", "dialogue": [{"user": "根本冇收到咯", "ai": "请问"}, {"user": "只有钱", "ai": "好的"}], "expected": "套机套现"},

    # 违规商品
    {"name": "违规商品-耳机", "category": "违规商品", "dialogue": [{"user": "拿到了耳机", "ai": "好的"}, {"user": "知道", "ai": "好的"}], "expected": "违规商品"},
    {"name": "违规商品-空气炸锅", "category": "违规商品", "dialogue": [{"user": "整了个空气炸锅", "ai": "好的"}, {"user": "晓得咯", "ai": "好的"}], "expected": "违规商品"},
    {"name": "违规商品-锅", "category": "违规商品", "dialogue": [{"user": "我拿了个锅", "ai": "好的"}, {"user": "知道", "ai": "好的"}], "expected": "违规商品"},
    {"name": "违规商品-充电宝", "category": "违规商品", "dialogue": [{"user": "拿到了个充电宝", "ai": "好的"}, {"user": "知道", "ai": "好的"}], "expected": "违规商品"},
    {"name": "违规商品-电视", "category": "违规商品", "dialogue": [{"user": "买了电视", "ai": "好的"}, {"user": "知道", "ai": "好的"}], "expected": "违规商品"},

    # 营销缺失
    {"name": "营销缺失-不知业务", "category": "营销缺失", "dialogue": [{"user": "我不知道啥是橙分期", "ai": "请问"}, {"user": "整了个手机", "ai": "好的"}], "expected": "营销缺失"},
    {"name": "营销缺失-投诉", "category": "营销缺失", "dialogue": [{"user": "我要投诉", "ai": "请问"}, {"user": "被骗了", "ai": "抱歉"}], "expected": "营销缺失"},
    {"name": "营销缺失-反问", "category": "营销缺失", "dialogue": [{"user": "啥是橙分期？", "ai": "橙分期是..."}, {"user": "咋还？", "ai": "每月..."}], "expected": "营销缺失"},
    {"name": "营销缺失-被骗", "category": "营销缺失", "dialogue": [{"user": "我被骗了", "ai": "请问"}, {"user": "说免费结果扣钱", "ai": "抱歉"}], "expected": "营销缺失"},
    {"name": "营销缺失-不知晓合约", "category": "营销缺失", "dialogue": [{"user": "拿到了手机", "ai": "好的"}, {"user": "不知道", "ai": "好的"}], "expected": "营销缺失"},

    # 边界
    {"name": "边界-付费但违规", "category": "边界", "dialogue": [{"user": "我花钱买的耳机", "ai": "好的"}], "expected": "违规商品"},
    {"name": "边界-矛盾表述", "category": "边界", "dialogue": [{"user": "收到了但好像又没收到", "ai": "请问"}, {"user": "整了个手机", "ai": "好的"}, {"user": "知道", "ai": "好的"}], "expected": "正常"},
]


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 60)
    print("  电信橙分期个性标签判定 - 完整对话测试")
    print("=" * 60)

    report = TestReport()

    for case in FULL_DIALOGUE_CASES:
        classifier = TelecomTagClassifier()
        classifier.process_dialogue(case["dialogue"])
        result = classifier.classify()
        context = classifier.get_context_summary()
        passed = result == case["expected"]

        report.add_result(
            case_name=case["name"],
            category=case["category"],
            expected=case["expected"],
            actual=result,
            passed=passed,
            dialogue=case["dialogue"],
            context=context
        )

        # 打印结果
        status = "✅" if passed else "❌"
        print(f"\n  {status} {case['category']} - {case['name']}")
        print(f"     期望: {case['expected']} | 实际: {result}")

    # 打印摘要
    report.print_summary()

    # 生成报告
    print("\n" + "=" * 60)
    print("  📄 生成测试报告")
    print("=" * 60)

    html_path = report.generate_html()
    print(f"  HTML报告: {html_path}")

    json_path = report.generate_json()
    print(f"  JSON报告: {json_path}")

    print("\n" + "=" * 60)
    if report.summary['failed'] == 0:
        print("  🎉 所有测试通过！")
    else:
        print(f"  ⚠️  {report.summary['failed']} 个测试失败")
    print("=" * 60)

    return 0 if report.summary['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
