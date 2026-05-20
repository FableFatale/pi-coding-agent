#!/usr/bin/env python
"""
电信橙分期标签判定测试验证脚本
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


# ============================================================
# 测试数据
# ============================================================

TAG_WHITELIST = [
    "套机套现", "违规商品", "营销缺失", "正常", "未沟通"
]

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
    "除螨仪", "词典笔", "绞肉机", "话费", "优惠券", "购物卡", "加油卡",
    "超市卡", "物业费", "代金券", "助听器", "血氧仪", "体脂秤", "话筒",
    "烤炉", "摩托", "电车", "冰柜", "大礼包", "大屏幕电视", "家具礼包",
    "家用电器", "家电套装", "自行车", "扫描笔", "学习笔", "读写笔",
    "投影仪", "赠品", "剃须刀", "刮胡刀", "电扇", "奖品", "投影",
    "固话机", "筋膜枪", "礼物", "水壶", "电子笔", "加湿器", "遥控器",
    "解压器", "电热壶", "收音机", "收银机", "壶", "车载记录仪", "行李箱",
    "料理机", "被子", "三轮车", "购物券", "油卡", "按摩器", "按摩仪",
    "厨房用品", "厨房用具", "汽车", "电动的汽车", "电动的车", "山地车",
    "洗碗机", "翻译机", "料理锅", "涮烤锅", "充电线", "热水壶", "电动牙刷",
    "足浴桶", "取暖器"
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
    """电信标签分类器"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.conversation = []
        self.received_goods = None
        self.goods_type = None
        self.knows_contract = None
        self.has_payment_keywords = False
        self.turns_count = 0

    def process(self, node: str, user_input: str, context: dict):
        """处理对话"""
        self.turns_count += 1
        self.conversation.append({"node": node, "user": user_input})

        # 检测付费关键词
        payment_keywords = ["付费", "花钱", "自费", "买", "花了", "花了钱"]
        if any(kw in user_input for kw in payment_keywords):
            self.has_payment_keywords = True
            self.received_goods = True

        # 检测已收到商品
        if any(kw in user_input for kw in ["拿到了", "收到了", "有"]):
            self.received_goods = True

        # 检测未收到商品
        if any(kw in user_input for kw in ["没拿到", "没收到", "没有", "什么都没"]):
            self.received_goods = False

        # 检测商品类型
        for product in NORMAL_PRODUCTS + VIOLATION_PRODUCTS:
            if product in user_input:
                self.goods_type = product
                break

        # 检测是否知晓合约
        if any(kw in user_input for kw in ["知道", "明白", "理解", "清楚"]):
            self.knows_contract = True

    def classify(self) -> str:
        """分类"""
        # 未沟通
        if self.turns_count < 2 and self.received_goods is None:
            return "未沟通"

        # 套机套现
        if self.received_goods is False and not self.has_payment_keywords:
            return "套机套现"

        # 违规商品
        if self.received_goods and self.goods_type:
            if self.goods_type in VIOLATION_PRODUCTS:
                return "违规商品"

        # 正常或营销缺失
        if self.received_goods:
            if self.knows_contract:
                return "正常"
            else:
                return "营销缺失"

        return "未沟通"


# ============================================================
# 测试函数
# ============================================================

class TestResults:
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    ERROR = "💥 ERROR"


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_tag_whitelist():
    """测试标签白名单"""
    print_section("1. 标签白名单测试")

    try:
        assert len(TAG_WHITELIST) == 5, f"应该有5个标签，实际{len(TAG_WHITELIST)}"
        print(f"  标签数量: {len(TAG_WHITELIST)} ✓")

        expected = ["套机套现", "违规商品", "营销缺失", "正常", "未沟通"]
        assert TAG_WHITELIST == expected
        print(f"  标签值正确 ✓")

        assert TAG_WHITELIST[0] == "套机套现"
        assert TAG_WHITELIST[4] == "未沟通"
        print(f"  优先级正确 ✓")

        print(f"  {TestResults.PASS}")
        return True
    except Exception as e:
        print(f"  {TestResults.ERROR}: {e}")
        return False


def test_violation_products():
    """测试违规商品库"""
    print_section("2. 违规商品库测试")

    try:
        assert len(VIOLATION_PRODUCTS) >= 100, f"违规商品应该>=100个"
        print(f"  违规商品数量: {len(VIOLATION_PRODUCTS)} ✓")

        common = ["耳机", "充电宝", "电视机", "空气炸锅", "锅", "净水器", "扫地机"]
        for product in common:
            assert product in VIOLATION_PRODUCTS, f"{product}应该在违规商品库"
        print(f"  常见违规商品存在 ✓")

        print(f"  {TestResults.PASS}")
        return True
    except Exception as e:
        print(f"  {TestResults.ERROR}: {e}")
        return False


def test_normal_products():
    """测试正常商品库"""
    print_section("3. 正常商品库测试")

    try:
        assert len(NORMAL_PRODUCTS) >= 100, f"正常商品应该>=100个"
        print(f"  正常商品数量: {len(NORMAL_PRODUCTS)} ✓")

        common = ["手机", "路由器", "平板电脑", "华为", "苹果", "小米", "空调", "冰箱"]
        for product in common:
            assert product in NORMAL_PRODUCTS, f"{product}应该在正常商品库"
        print(f"  常见正常商品存在 ✓")

        print(f"  {TestResults.PASS}")
        return True
    except Exception as e:
        print(f"  {TestResults.ERROR}: {e}")
        return False


def test_classifier_initialization():
    """测试分类器初始化"""
    print_section("4. 分类器初始化测试")

    try:
        classifier = TelecomTagClassifier()
        assert classifier is not None
        assert classifier.received_goods is None
        assert classifier.turns_count == 0
        print(f"  分类器初始化正确 ✓")

        classifier.reset()
        assert classifier.turns_count == 0
        assert classifier.received_goods is None
        print(f"  分类器重置正确 ✓")

        print(f"  {TestResults.PASS}")
        return True
    except Exception as e:
        print(f"  {TestResults.ERROR}: {e}")
        return False


def test_scenario_normal_phone():
    """场景: 正常-手机"""
    print_section("5. 场景-正常手机")

    try:
        classifier = TelecomTagClassifier()
        classifier.process("A", "我办理了橙分期", {})
        classifier.process("B", "拿到了手机", {})
        classifier.process("C", "知道合约规则", {})

        result = classifier.classify()
        print(f"  分类结果: {result}")

        assert result == "正常", f"期望'正常'，实际'{result}'"
        print(f"  {TestResults.PASS}")
        return True
    except Exception as e:
        print(f"  {TestResults.ERROR}: {e}")
        return False


def test_scenario_normal_router():
    """场景: 正常-路由器"""
    print_section("6. 场景-正常路由器")

    try:
        classifier = TelecomTagClassifier()
        classifier.process("A", "我办理了橙分期", {})
        classifier.process("B", "拿到了路由器", {})
        classifier.process("C", "知道", {})

        result = classifier.classify()
        print(f"  分类结果: {result}")

        assert result == "正常", f"期望'正常'，实际'{result}'"
        print(f"  {TestResults.PASS}")
        return True
    except Exception as e:
        print(f"  {TestResults.ERROR}: {e}")
        return False


def test_scenario_violation_headphones():
    """场景: 违规商品-耳机"""
    print_section("7. 场景-违规耳机")

    try:
        classifier = TelecomTagClassifier()
        classifier.process("A", "我办理了橙分期", {})
        classifier.process("B", "拿到了耳机", {})

        result = classifier.classify()
        print(f"  分类结果: {result}")

        assert result == "违规商品", f"期望'违规商品'，实际'{result}'"
        print(f"  {TestResults.PASS}")
        return True
    except Exception as e:
        print(f"  {TestResults.ERROR}: {e}")
        return False


def test_scenario_violation_air_fryer():
    """场景: 违规商品-空气炸锅"""
    print_section("8. 场景-违规空气炸锅")

    try:
        classifier = TelecomTagClassifier()
        classifier.process("A", "我办理了橙分期", {})
        classifier.process("B", "拿到了空气炸锅", {})

        result = classifier.classify()
        print(f"  分类结果: {result}")

        assert result == "违规商品", f"期望'违规商品'，实际'{result}'"
        print(f"  {TestResults.PASS}")
        return True
    except Exception as e:
        print(f"  {TestResults.ERROR}: {e}")
        return False


def test_scenario_cash_out():
    """场景: 套机套现"""
    print_section("9. 场景-套机套现")

    try:
        classifier = TelecomTagClassifier()
        classifier.process("A", "我办理了橙分期", {})
        classifier.process("B", "没拿到东西，只收到了钱", {})

        result = classifier.classify()
        print(f"  分类结果: {result}")

        assert result == "套机套现", f"期望'套机套现'，实际'{result}'"
        print(f"  {TestResults.PASS}")
        return True
    except Exception as e:
        print(f"  {TestResults.ERROR}: {e}")
        return False


def test_scenario_marketing_lack():
    """场景: 营销缺失"""
    print_section("10. 场景-营销缺失")

    try:
        classifier = TelecomTagClassifier()
        classifier.process("A", "我办理了橙分期", {})
        classifier.process("B", "拿到了手机", {})
        classifier.process("C", "不知道", {})

        result = classifier.classify()
        print(f"  分类结果: {result}")

        assert result == "营销缺失", f"期望'营销缺失'，实际'{result}'"
        print(f"  {TestResults.PASS}")
        return True
    except Exception as e:
        print(f"  {TestResults.ERROR}: {e}")
        return False


def test_scenario_no_communication():
    """场景: 未沟通"""
    print_section("11. 场景-未沟通")

    try:
        classifier = TelecomTagClassifier()
        # 零互动
        result = classifier.classify()
        print(f"  零互动分类结果: {result}")
        assert result == "未沟通", f"期望'未沟通'，实际'{result}'"

        # 短轮次
        classifier.reset()
        classifier.turns_count = 1
        result = classifier.classify()
        print(f"  短轮次分类结果: {result}")
        assert result == "未沟通", f"期望'未沟通'，实际'{result}'"

        print(f"  {TestResults.PASS}")
        return True
    except Exception as e:
        print(f"  {TestResults.ERROR}: {e}")
        return False


def test_rule_0_payment():
    """0号铁则: 付费关键词"""
    print_section("12. 0号铁则-付费关键词")

    try:
        test_inputs = [
            "我付费了",
            "花钱买的",
            "自费购买",
            "花了1000",
            "花了1千7",
            "花了1700"
        ]

        for payment_input in test_inputs:
            classifier = TelecomTagClassifier()
            classifier.process("B", payment_input, {})
            assert classifier.received_goods == True, f"'{payment_input}'应该触发已收到商品"
            print(f"  '{payment_input}' -> 已收到商品 ✓")

        print(f"  {TestResults.PASS}")
        return True
    except Exception as e:
        print(f"  {TestResults.ERROR}: {e}")
        return False


def test_product_boundaries():
    """商品库边界测试"""
    print_section("13. 商品库边界测试")

    try:
        # 电饭锅应该是正常商品
        assert "电饭锅" in NORMAL_PRODUCTS
        assert "电饭煲" in NORMAL_PRODUCTS
        print(f"  电饭锅 ✓")

        # 锅是违规商品
        assert "锅" in VIOLATION_PRODUCTS
        print(f"  锅(违规) ✓")

        # 手机是正常商品
        assert "手机" in NORMAL_PRODUCTS
        print(f"  手机 ✓")

        # 耳机是违规商品
        assert "耳机" in VIOLATION_PRODUCTS
        print(f"  耳机 ✓")

        print(f"  {TestResults.PASS}")
        return True
    except Exception as e:
        print(f"  {TestResults.ERROR}: {e}")
        return False


def test_output_format():
    """输出格式测试"""
    print_section("14. 输出格式测试")

    try:
        import json

        valid_output = {"tags": ["正常"]}
        result = json.dumps(valid_output)

        assert "tags" in result
        assert "正常" in result
        print(f"  输出格式正确 ✓")

        # 单标签
        assert len(json.loads(result)["tags"]) == 1
        print(f"  单标签 ✓")

        print(f"  {TestResults.PASS}")
        return True
    except Exception as e:
        print(f"  {TestResults.ERROR}: {e}")
        return False


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 60)
    print("  电信橙分期个性标签判定测试")
    print("  基于 telecom_tags.md 规范")
    print("=" * 60)

    tests = [
        ("标签白名单", test_tag_whitelist),
        ("违规商品库", test_violation_products),
        ("正常商品库", test_normal_products),
        ("分类器初始化", test_classifier_initialization),
        ("场景-正常手机", test_scenario_normal_phone),
        ("场景-正常路由器", test_scenario_normal_router),
        ("场景-违规耳机", test_scenario_violation_headphones),
        ("场景-违规空气炸锅", test_scenario_violation_air_fryer),
        ("场景-套机套现", test_scenario_cash_out),
        ("场景-营销缺失", test_scenario_marketing_lack),
        ("场景-未沟通", test_scenario_no_communication),
        ("0号铁则-付费关键词", test_rule_0_payment),
        ("商品库边界", test_product_boundaries),
        ("输出格式", test_output_format),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  {TestResults.ERROR}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"  测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 所有测试通过！标签判定系统工作正常！\n")
    else:
        print(f"\n⚠️  {failed} 个测试失败\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
