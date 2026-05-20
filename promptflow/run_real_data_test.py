#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
真实对话数据测试脚本
加载真实对话记录，验证标签判定准确性
"""
import sys
import os
import csv
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ============================================================
# 标签白名单
# ============================================================

TAG_WHITELIST = ["套机套现", "违规商品", "营销缺失", "正常", "未沟通"]


# ============================================================
# 商品库 (来自个性标签.md)
# ============================================================

NORMAL_PRODUCTS = [
    "手机", "天翼", "小E", "优惠", "打折", "折扣", "国补", "设备", "关猫",
    "魅族", "联想", "摩托罗拉", "索尼", "华硕", "华为", "oppo", "vivo",
    "红米", "小米", "荣耀", "苹果", "mate60", "iphone", "中兴", "三星",
    "全光", "一加", "真我", "合约机", "电话", "话机", "智能机", "购机优惠",
    "财务覆盖", "全屋组网", "全屋覆盖", "全部覆盖", "全屋", "Fttr", "fttr",
    "表", "手表", "手环", "小天才", "电话手表", "儿童手表", "电子表",
    "云电脑", "VR", "电脑", "平板电脑", "笔记本", "平板", "iPad", "ipad",
    "pad", "爱拍", "爱派", "派", "Pad", "PAD", "光猫", "机顶盒", "盒",
    "猫", "网", "网关", "二宽", "千兆", "光纤", "宽带", "WiFi", "wifi",
    "无线", "网线", "路由", "路由器", "无线路由", "无线网", "小爱同学",
    "小爱", "小猪", "小豆", "小杜", "小艾", "小度", "小肚", "小翼管家",
    "小翼", "天猫精灵", "天猫", "精灵", "智能遥控", "智能音响", "智能猫眼",
    "智能门锁", "智能门铃", "密码锁", "指纹密码锁", "电子锁", "门锁",
    "智能报警器", "智能开关", "门铃", "音响", "音箱", "猫眼", "指纹锁",
    "锁", "报警器", "智能产品", "智能锁", "消防烟感器", "智慧屏", "智慧大屏",
    "空调", "冰箱", "洗衣机", "点读笔", "伴读机", "AC", "AP", "体感游戏",
    "遥控", "开关", "卫星终端", "卫星", "智能传感器", "传感器", "智能窗帘电机",
    "智能机器人", "机器人", "智能学习桌椅套", "桌椅套", "学习桌", "智能胸卡",
    "胸卡", "学生证", "助听器", "助听机", "热水器", "游戏机", "学习机",
    "家教机", "家教器", "收银音箱", "老人陪伴机", "陪伴机", "智能陪伴机",
    "收银一体机", "收银机", "收银设备", "收银的", "收款机", "扫码终端",
    "扫码的终端", "扫码枪", "扫码设备", "扫码的", "血氧仪", "血氧机",
    "台灯", "体脂秤", "电子秤", "体重秤", "声控灯", "智能灯", "感应灯",
    "太阳能灯", "灯", "秤", "电饭煲", "电饭锅", "饭煲", "饭锅", "煮饭的",
    "煮饭锅", "煮饭煲", "插头", "插座", "插排", "插板", "排插", "智能插排",
    "智能插头", "智能排插", "POS机", "话筒", "固话机", "固定电话",
    "智能康养遥控器", "遥控器", "老人机", "老年机", "摄像头"
]

VIOLATION_PRODUCTS = [
    "购机券", "三轮车", "购金券", "购机款", "充值卡", "购物券", "油卡",
    "加油券", "优惠券", "购物卡", "加油卡", "超市卡", "物业费", "代金券",
    "耳机", "蓝牙", "蓝牙耳机", "按摩器", "按摩仪", "光盘", "词典笔",
    "扫描笔", "智能笔", "学习笔", "读写笔", "投影仪", "投影", "电子笔",
    "家具礼包", "家用电器", "家电套装", "家电", "家具", "厨房用品",
    "厨房用具", "智家大礼包", "智家礼包", "油烟机", "智电炸锅", "消毒柜",
    "燃气灶", "打印机", "扫地机", "打印器", "扫地器", "净化器", "净化机",
    "净水机", "净水器", "电动车", "电动汽车", "电瓶车", "电动自行车",
    "摩托", "电车", "自行车", "汽车", "电动的汽车", "电动的车", "山地车",
    "洗碗机", "阿尔法", "阿尔法蛋", "翻译机", "电子产品", "电子设备",
    "电器", "话费券", "电暖桌", "吸尘器", "吸尘机", "热风机", "热风器",
    "压力煲", "压力高", "高压锅", "高压包", "壶", "焖锅", "空气炸锅",
    "料理锅", "涮烤锅", "炸锅", "电火锅", "烤火的", "烤火炉", "电压锅",
    "饮水机", "饮水器", "一体锅", "烤炉", "烤锅", "蒸锅", "鸳鸯锅",
    "烤涮一体锅", "烤涮锅", "豆浆机", "电水壶", "水壶", "电暖炉", "暖炉",
    "榨汁机", "榨汁器", "挂烫机", "挂烫器", "电风扇", "暖风扇", "循环扇",
    "风扇", "电扇", "电蒸锅", "电热锅", "电力压锅", "压锅", "电锅",
    "养生壶", "电饼铛", "电饼档", "茶具", "炒锅", "电磁炉", "磁炉",
    "炉子", "茶吧机", "破壁机", "茶吧器", "破壁器", "微波炉", "压力锅",
    "烤箱", "多功能锅", "保温杯", "吹风机", "吹风器", "电吹风", "吹风",
    "吹头发的", "电炸锅", "蒸汽锅", "烤盘", "烧水壶", "除螨仪", "除螨机",
    "除螨器", "绞肉机", "绞肉器", "空气炸锅机", "剃须刀", "刮胡刀",
    "筋膜枪", "加湿器", "料理器", "料理机", "充电宝", "充电线", "鼠标",
    "模型", "飞机模型", "高铁模型", "火车模型", "唱歌设备", "唱歌的设备",
    "收音机", "录音机", "小礼品", "礼品", "礼包", "大礼包", "赠品",
    "奖品", "礼物", "被子", "棉被", "空调被", "羽绒被", "绒被", "蚕丝被",
    "电热毯解压器", "电热壶", "转换器", "行李箱", "热水壶", "电动牙刷",
    "足浴桶", "泡脚的", "泡脚桶", "取暖器", "取暖机", "取暖的", "话费"
]


# ============================================================
# 方言映射
# ============================================================

DIALECT_MAP = {
    # 粤语
    "收到咯": "收到了", "拿到咯": "拿到了", "冇": "没有", "係啊": "是的",
    "不晓得咡": "不知道", "知道得嘛": "知道了", "得嘛": "知道了",
    # 四川
    "整咯": "买了", "整了个": "买了个", "晓得咯": "知道了", "啥子": "什么",
    "咋整": "怎么回事", "要得": "好的",
    # 东北
    "知道得了": "知道了", "中": "好的", "整一个": "买了一个"
}


# ============================================================
# 标签分类器 (基于个性标签.md规则)
# ============================================================

class RealTagClassifier:
    """
    真实对话标签分类器
    规则来源: 个性标签.md
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.full_text = ""
        self.turns = 0
        self.received_goods = None  # None=未确认, True=已收到, False=未收到
        self.has_payment = False    # 付费关键词
        self.goods_type = None
        self.knows_contract = None  # None=未确认, True=知晓, False=不知晓
        self.is_complaint = False
        self.is_fraud = False
        self.is_cash_out = False    # 折现
        self.dialogue_history = []

    def process_dialogue(self, conversation: list):
        """
        处理对话列表
        conversation: [{"user": "xxx", "ai": "xxx"}, ...]
        """
        self.dialogue_history = conversation
        self.turns = len(conversation)

        # 合并所有用户输入
        all_user_text = " ".join([turn.get("user", "") for turn in conversation])
        self.full_text = all_user_text

        # 转换方言
        for dialect, standard in DIALECT_MAP.items():
            self.full_text = self.full_text.replace(dialect, standard)

        self._extract_features()

    def _extract_features(self):
        text = self.full_text

        # 1. 付费关键词检测 (0号铁则)
        payment_keywords = ["花钱", "付费", "自费", "买", "花了", "花咯", "花啦",
                           "付了", "付款", "购买", "买的", "整咯", "整了个"]
        if any(kw in text for kw in payment_keywords):
            self.has_payment = True
            self.received_goods = True  # 付费 = 已收到商品

        # 2. 收到商品关键词
        received_keywords = ["拿到了", "收到了", "有", "有收到", "拿到手",
                           "已经拿到", "拿到喽", "装好了", "安装好了",
                           "买咯", "买了个", "搞了个", "优惠", "用上"]
        if any(kw in text for kw in received_keywords):
            self.received_goods = True

        # 3. 未收到商品关键词
        not_received_keywords = ["没拿到", "没收到", "没有", "什么都没",
                                "只有钱", "木有", "冇", "根本冇", "根本没",
                                "没得", "未收到", "没有收到", "未拿到",
                                "没有拿到", "啥都没", "手机被回收", "做样板"]
        if any(kw in text for kw in not_received_keywords):
            self.received_goods = False
            if "钱" in text or "折现" in text:
                self.is_cash_out = True

        # 4. 商品类型检测
        for product in NORMAL_PRODUCTS + VIOLATION_PRODUCTS:
            if product in text:
                self.goods_type = product
                break

        # 5. 知晓合约检测
        knows_keywords = ["知道", "明白", "理解", "清楚", "晓得", "晓得了",
                         "了解了", "清楚了"]
        not_knows_keywords = ["不知道", "不晓得", "不晓滴", "不造", "没办过",
                             "没要求", "不清", "啥是", "啥玩意儿", "咋还",
                             "咋整", "咋回事", "不理解", "没听过"]
        if any(kw in text for kw in knows_keywords):
            self.knows_contract = True
        if any(kw in text for kw in not_knows_keywords):
            self.knows_contract = False

        # 6. 投诉/欺诈检测
        complaint_keywords = ["投诉", "骗", "骗人", "被骗", "欺诈", "虚假",
                            "坑", "坑人", "垃圾", "太差", "不满"]
        fraud_keywords = ["被骗了", "被骗咯", "被坑", "被坑咯", "欺诈"]
        if any(kw in text for kw in complaint_keywords):
            self.is_complaint = True
        if any(kw in text for kw in fraud_keywords):
            self.is_fraud = True

    def classify(self) -> str:
        """
        基于规则进行标签分类
        优先级: 套机套现 > 违规商品 > 营销缺失 > 正常 > 未沟通
        """

        # 0号铁则: 付费 = 禁止套机套现
        if self.has_payment:
            pass  # 不触发套机套现

        # 1. 套机套现 (优先级1)
        # 条件: 未收到商品 + 无付费 + 未知晓业务
        if self.received_goods is False and not self.has_payment:
            return "套机套现"

        # 2. 违规商品 (优先级2)
        if self.received_goods and self.goods_type:
            if self.goods_type in VIOLATION_PRODUCTS:
                return "违规商品"

        # 3. 营销缺失 (优先级3)
        # 条件: 收到商品 + 不知晓业务
        if self.received_goods and self.knows_contract is False:
            return "营销缺失"
        if self.is_fraud:
            return "营销缺失"
        if self.is_complaint and self.received_goods:
            return "营销缺失"
        # 询问业务定义但没有明确否认
        if "啥是" in self.full_text or "啥玩意儿" in self.full_text:
            if self.received_goods:
                return "营销缺失"

        # 4. 正常 (优先级4)
        # 条件: 收到商品 + 商品在正常库 + 知晓合约
        if self.received_goods and self.goods_type:
            if self.goods_type in NORMAL_PRODUCTS:
                if self.knows_contract is True:
                    return "正常"
                # 收到商品但无明确否定 -> 视为正常
                if self.knows_contract is None:
                    return "正常"

        # 收到商品但未确认知晓 -> 默认正常
        if self.received_goods:
            return "正常"

        # 5. 未沟通 (优先级5)
        # 条件: 轮次少 + 无有效信息
        if self.turns < 2 and self.received_goods is None:
            return "未沟通"

        # 兜底
        return "营销缺失"

    def get_context(self) -> dict:
        return {
            "turns": self.turns,
            "received_goods": self.received_goods,
            "goods_type": self.goods_type,
            "has_payment": self.has_payment,
            "knows_contract": self.knows_contract,
            "is_complaint": self.is_complaint,
            "is_fraud": self.is_fraud,
            "is_cash_out": self.is_cash_out,
            "label": self.classify()
        }


# ============================================================
# 测试用例 (来自问题.txt)
# ============================================================

ERROR_CASES = [
    {
        "id": "2245940",
        "description": "标签出错，应该是正常",
        "expected": "正常",
        "dialogue": [
            {"user": "我拿到了手机", "ai": "请问您知道橙分期吗？"},
            {"user": "知道", "ai": "好的"}
        ]
    },
    {
        "id": "2246337",
        "description": "标签出错，应该是正常",
        "expected": "正常",
        "dialogue": [
            {"user": "拿到了", "ai": "请问您知道合约吗？"},
            {"user": "知道", "ai": "好的"}
        ]
    },
    {
        "id": "2246052",
        "description": "核实流程出错，用户表示没有拿到手机，应该继续问有没有拿到宽带",
        "expected": "营销缺失",
        "dialogue": [
            {"user": "我没有拿到手机", "ai": "好的"},
            {"user": "", "ai": ""}
        ]
    },
    {
        "id": "2246359",
        "description": "标签出错，应该是正常，用户没有明确说自己不知道橙分期",
        "expected": "正常",
        "dialogue": [
            {"user": "拿到了手机", "ai": "请问您知道橙分期吗？"},
            {"user": "嗯", "ai": "好的"}
        ]
    },
    {
        "id": "2246143",
        "description": "标签出错，应该是正常",
        "expected": "正常",
        "dialogue": [
            {"user": "我办理了橙分期，拿到了手机", "ai": "请问您知道合约吗？"},
            {"user": "知道", "ai": "好的"}
        ]
    },
    {
        "id": "2246037",
        "description": "用户表示手机被门店回收了，要做样板机，实际情况应该是套机套现",
        "expected": "套机套现",
        "dialogue": [
            {"user": "手机被门店回收了，要做样板机", "ai": "请问您知道橙分期吗？"},
            {"user": "知道", "ai": "好的"}
        ]
    }
]


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 70)
    print("  电信橙分期话术与标签测试 - 真实数据验证")
    print("=" * 70)

    classifier = RealTagClassifier()
    results = []

    print("\n" + "=" * 70)
    print("  📋 错误案例测试 (来自问题.txt)")
    print("=" * 70)

    for case in ERROR_CASES:
        classifier.reset()
        classifier.process_dialogue(case["dialogue"])
        actual = classifier.classify()
        context = classifier.get_context()
        passed = actual == case["expected"]

        status = "✅" if passed else "❌"
        print(f"\n{status} 案例 {case['id']}")
        print(f"   描述: {case['description']}")
        print(f"   期望: {case['expected']} | 实际: {actual}")
        print(f"   上下文: 收到={context['received_goods']}, "
              f"商品={context['goods_type']}, "
              f"知晓={context['knows_contract']}")

        results.append({
            "id": case["id"],
            "expected": case["expected"],
            "actual": actual,
            "passed": passed,
            "context": context
        })

    # 统计
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    print("\n" + "=" * 70)
    print("  📊 测试统计")
    print("=" * 70)
    print(f"   总测试: {total}")
    print(f"   通过: {passed}")
    print(f"   失败: {failed}")
    print(f"   通过率: {passed/total*100:.1f}%")

    # 生成报告
    print("\n" + "=" * 70)
    print("  📄 生成报告")
    print("=" * 70)

    report = f"""# 电信橙分期真实数据测试报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 测试统计

| 指标 | 值 |
|------|-----|
| 总测试 | {total} |
| 通过 | {passed} |
| 失败 | {failed} |
| 通过率 | {passed/total*100:.1f}% |

## 错误案例测试结果

| ID | 期望 | 实际 | 状态 | 收到商品 | 商品类型 | 知晓合约 |
|----|------|------|------|----------|----------|----------|
"""

    for r in results:
        status = "✅" if r["passed"] else "❌"
        ctx = r["context"]
        report += f"| {r['id']} | {r['expected']} | {r['actual']} | {status} | "
        report += f"{ctx['received_goods']} | {ctx['goods_type']} | {ctx['knows_contract']} |\n"

    report += """
## 失败案例分析

"""

    for r in results:
        if not r["passed"]:
            ctx = r["context"]
            report += f"""### 案例 {r['id']}

- **期望**: {r['expected']}
- **实际**: {r['actual']}
- **上下文**:
  - 收到商品: {ctx['received_goods']}
  - 商品类型: {ctx['goods_type']}
  - 付费: {ctx['has_payment']}
  - 知晓合约: {ctx['knows_contract']}
  - 投诉: {ctx['is_complaint']}
  - 欺诈: {ctx['is_fraud']}
  - 折现: {ctx['is_cash_out']}

"""

    report += """
---
*报告自动生成*
"""

    # 保存报告
    report_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(report_dir, exist_ok=True)

    report_path = os.path.join(
        report_dir,
        f"REAL_DATA_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"   报告已保存: {report_path}")

    print("\n" + "=" * 70)
    if failed == 0:
        print("  🎉 所有测试通过！")
    else:
        print(f"  ⚠️  {failed} 个测试失败，需要调整规则")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
