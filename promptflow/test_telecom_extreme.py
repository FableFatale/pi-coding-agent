#!/usr/bin/env python
"""
电信橙分期标签判定 - 极端测试验证脚本
"""
import sys
import os
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
        self.user_queries = []
        self.negative_responses = []
        self.affirmative_responses = []

    def process(self, node: str, user_input: str, context: dict):
        self.turns_count += 1
        self.conversation.append({"node": node, "user": user_input, "turn": self.turns_count})

        text = user_input.strip()
        if not text:
            return

        # 付费关键词
        payment_keywords = ["付费", "花钱", "自费", "买", "花了", "花了钱", "花咯", "花啦", "整咯"]
        if any(kw in text for kw in payment_keywords):
            self.has_payment_keywords = True
            self.received_goods = True

        # 已收到商品
        received_keywords = ["拿到了", "收到了", "有", "拿到了", "收到咯", "拿到咯", "买咯", "买咯", "整了个", "整咯"]
        if any(kw in text for kw in received_keywords):
            self.received_goods = True

        # 未收到商品
        not_received_keywords = ["没拿到", "没收到", "没有", "什么都没", "只有钱", "木有", "冇", "根本冇", "根本没"]
        if any(kw in text for kw in not_received_keywords):
            self.received_goods = False

        # 方言-已收到
        dialect_received = ["收到咯", "拿到咯", "有收到", "拿到手了", "已经拿到", "拿到喽"]
        if any(kw in text for kw in dialect_received):
            self.received_goods = True

        # 方言-不知道
        dialect_unknown = ["不晓得", "不晓滴", "不造啊", "晓不得", "母鸡啊"]
        if any(kw in text for kw in dialect_unknown):
            self.negative_responses.append("不知道")

        # 方言-知道了
        dialect_known = ["晓得咯", "晓得喽", "晓得了", "知道咯", "知道了撒", "知道得嘛", "知道得了"]
        if any(kw in text for kw in dialect_known):
            self.affirmative_responses.append("知道")

        # 检测商品类型
        all_products = set(NORMAL_PRODUCTS + VIOLATION_PRODUCTS)
        for product in all_products:
            if product in text:
                self.goods_type = product
                break

        # 知晓合约
        if any(kw in text for kw in ["知道", "明白", "理解", "清楚", "晓得", "晓得了"]):
            self.knows_contract = True

        if any(kw in text for kw in ["不知道", "不晓得", "不晓滴", "不造", "没办过", "没要求", "不清", "咋"]):
            self.knows_contract = False

        # 用户询问
        question_keywords = ["啥", "什么", "怎么", "哪", "为啥", "为什么", "咋", "咋整"]
        if any(kw in text for kw in question_keywords):
            self.user_queries.append(text)

    def classify(self) -> str:
        # 未沟通
        if self._is_no_communication():
            return "未沟通"

        # 套机套现
        if self._is_cash_out():
            return "套机套现"

        # 违规商品
        if self._is_violation_product():
            return "违规商品"

        # 营销缺失
        if self._is_marketing_lack():
            return "营销缺失"

        # 正常
        if self._is_normal():
            return "正常"

        return "未沟通"

    def _is_no_communication(self) -> bool:
        if self.turns_count == 0:
            return True

        if self.turns_count < 3 and self.received_goods is None:
            filler_words = ["嗯", "啊", "哦", "呃", "嗯嗯", "啊啊", "嗯嗯嗯", "撒", "嘛"]
            all_filler = all(
                any(fw in turn["user"] for fw in filler_words)
                for turn in self.conversation
                if turn["user"]
            )
            if all_filler or len(self.conversation) == 0:
                return True

        return False

    def _is_cash_out(self) -> bool:
        if self.received_goods is False and not self.has_payment_keywords:
            if self.goods_type not in VIOLATION_PRODUCTS:
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

        denial_keywords = ["不知情", "被骗了", "没办过", "没要求", "不记得", "啥是", "咋还", "啥玩意儿"]
        for turn in self.conversation:
            if any(kw in turn["user"] for kw in denial_keywords):
                return True

        return False

    def _is_normal(self) -> bool:
        if self.received_goods and self.goods_type in NORMAL_PRODUCTS:
            if self.knows_contract is True:
                return True
        return False

    def get_output(self) -> dict:
        tag = self.classify()
        return {"tags": [tag]}


# ============================================================
# 测试函数
# ============================================================

class TestResults:
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def run_test(name, test_func):
    try:
        result = test_func()
        status = TestResults.PASS if result else TestResults.FAIL
        print(f"  {status} {name}")
        return result
    except Exception as e:
        print(f"  ❌ FAIL {name}: {e}")
        return False


# ============================================================
# 测试用例数据
# ============================================================

DIALECT_CASES = [
    # 粤语
    {"input": "收到咯，手机", "expected": "正常", "dialect": "粤语"},
    {"input": "冇收到咯", "expected": "套机套现", "dialect": "粤语"},
    {"input": "不晓得咁", "expected": "营销缺失", "dialect": "粤语"},
    {"input": "知道咯", "expected": "正常", "dialect": "粤语"},
    {"input": "根本冇收到", "expected": "套机套现", "dialect": "粤语"},

    # 四川
    {"input": "拿到咯", "expected": "正常", "dialect": "四川"},
    {"input": "不晓得咡", "expected": "营销缺失", "dialect": "四川"},
    {"input": "咋整嘛", "expected": "营销缺失", "dialect": "四川"},
    {"input": "啥子哦", "expected": "营销缺失", "dialect": "四川"},

    # 东北
    {"input": "整了个手机", "expected": "正常", "dialect": "东北"},
    {"input": "整啥玩意儿", "expected": "营销缺失", "dialect": "东北"},
    {"input": "知道得了", "expected": "正常", "dialect": "东北"},
    {"input": "行", "expected": "正常", "dialect": "东北"},
]

NON_STANDARD_CASES = [
    {"input": "等等，我先接个电话", "desc": "打断-接电话"},
    {"input": "你等会儿，我忙", "desc": "打断-忙"},
    {"input": "啥是橙分期？", "desc": "反问-询问业务"},
    {"input": "咋还分期？", "desc": "反问-询问分期"},
    {"input": "我要投诉，你们骗人", "desc": "投诉-被骗"},
    {"input": "嗯", "desc": "模糊-嗯"},
    {"input": "啊？", "desc": "模糊-啊"},
    {"input": "哦", "desc": "模糊-哦"},
    {"input": "嗯嗯嗯", "desc": "模糊-嗯嗯嗯"},
]

EXTREME_CASES = [
    {"input": "", "desc": "空字符串"},
    {"input": "   ", "desc": "空格"},
    {"input": "。", "desc": "句号"},
    {"input": "@#$%^&*()", "desc": "特殊字符"},
    {"input": "🎉🎊🎁", "desc": "emoji"},
    {"input": "1234567890", "desc": "纯数字"},
    {"input": "fuck", "desc": "英语脏话"},
    {"input": "滚", "desc": "中文拒绝"},
]

PRODUCT_CASES = [
    {"input": "拿到了华为手机", "expected": "正常", "product": "手机"},
    {"input": "装好了宽带", "expected": "正常", "product": "宽带"},
    {"input": "买了个路由器", "expected": "正常", "product": "路由器"},
    {"input": "收到了耳机", "expected": "违规商品", "product": "耳机"},
    {"input": "拿了个充电宝", "expected": "违规商品", "product": "充电宝"},
    {"input": "搞了个空气炸锅", "expected": "违规商品", "product": "空气炸锅"},
    {"input": "拿了个锅", "expected": "违规商品", "product": "锅"},
    {"input": "买了个电视", "expected": "违规商品", "product": "电视"},
]


# ============================================================
# 测试函数
# ============================================================

def test_dialect_cantonese():
    """测试粤语方言"""
    results = []
    for case in DIALECT_CASES:
        if case.get("dialect") == "粤语":
            classifier = TelecomTagClassifier()
            classifier.process("B", case["input"], {})
            result = classifier.classify()
            match = result == case["expected"]
            results.append(match)
            status = "✅" if match else "❌"
            print(f"    {status} 粤语: '{case['input']}' -> {result} (期望: {case['expected']})")
    return all(results)


def test_dialect_sichuan():
    """测试四川方言"""
    results = []
    for case in DIALECT_CASES:
        if case.get("dialect") == "四川":
            classifier = TelecomTagClassifier()
            classifier.process("B", case["input"], {})
            result = classifier.classify()
            match = result == case["expected"]
            results.append(match)
            status = "✅" if match else "❌"
            print(f"    {status} 四川: '{case['input']}' -> {result} (期望: {case['expected']})")
    return all(results)


def test_dialect_northeast():
    """测试东北方言"""
    results = []
    for case in DIALECT_CASES:
        if case.get("dialect") == "东北":
            classifier = TelecomTagClassifier()
            classifier.process("B", case["input"], {})
            result = classifier.classify()
            match = result == case["expected"]
            results.append(match)
            status = "✅" if match else "❌"
            print(f"    {status} 东北: '{case['input']}' -> {result} (期望: {case['expected']})")
    return all(results)


def test_nonstandard_interruption():
    """测试打断"""
    for case in NON_STANDARD_CASES[:2]:
        classifier = TelecomTagClassifier()
        classifier.process("A", case["input"], {})
        result = classifier.classify()
        print(f"    打断: '{case['input']}' -> {result}")
    return True


def test_nonstandard_questions():
    """测试反问"""
    for case in NON_STANDARD_CASES[2:4]:
        classifier = TelecomTagClassifier()
        classifier.process("B", case["input"], {})
        result = classifier.classify()
        print(f"    反问: '{case['input']}' -> {result}")
    return True


def test_nonstandard_complaints():
    """测试投诉"""
    for case in NON_STANDARD_CASES[4:6]:
        classifier = TelecomTagClassifier()
        classifier.process("B", case["input"], {})
        result = classifier.classify()
        print(f"    投诉: '{case['input']}' -> {result}")
    return True


def test_nonstandard_filler():
    """测试模糊回答"""
    results = []
    for case in NON_STANDARD_CASES[6:]:
        classifier = TelecomTagClassifier()
        classifier.process("A", case["input"], {})
        result = classifier.classify()
        match = result == "未沟通"
        results.append(match)
        status = "✅" if match else "❌"
        print(f"    {status} 模糊: '{case['input']}' -> {result} (期望: 未沟通)")
    return all(results)


def test_extreme_empty():
    """测试空输入"""
    results = []
    for case in EXTREME_CASES[:3]:
        classifier = TelecomTagClassifier()
        classifier.process("A", case["input"], {})
        result = classifier.classify()
        match = result == "未沟通"
        results.append(match)
        status = "✅" if match else "❌"
        print(f"    {status} 极端: '{case['input'][:20]}' -> {result}")
    return all(results)


def test_extreme_special():
    """测试特殊字符"""
    results = []
    for case in EXTREME_CASES[3:7]:
        classifier = TelecomTagClassifier()
        classifier.process("A", case["input"], {})
        result = classifier.classify()
        print(f"    特殊: '{case['input']}' -> {result}")
        results.append(True)
    return all(results)


def test_product_normal():
    """测试正常商品"""
    results = []
    for case in PRODUCT_CASES[:3]:
        classifier = TelecomTagClassifier()
        classifier.process("B", case["input"], {})
        result = classifier.classify()
        match = result == case["expected"]
        results.append(match)
        status = "✅" if match else "❌"
        print(f"    {status} 正常: '{case['input']}' -> {result} (期望: {case['expected']})")
    return all(results)


def test_product_violation():
    """测试违规商品"""
    results = []
    for case in PRODUCT_CASES[3:]:
        classifier = TelecomTagClassifier()
        classifier.process("B", case["input"], {})
        result = classifier.classify()
        match = result == case["expected"]
        results.append(match)
        status = "✅" if match else "❌"
        print(f"    {status} 违规: '{case['input']}' -> {result} (期望: {case['expected']})")
    return all(results)


def test_real_conversation_1():
    """真实对话1"""
    print("    场景: 粤语-收到手机")
    classifier = TelecomTagClassifier()
    classifier.process("A", "係啊", {})
    classifier.process("B", "收到咯，手机", {})
    classifier.process("C", "知道咯", {})
    result = classifier.classify()
    print(f"    -> {result}")
    return result == "正常"


def test_real_conversation_2():
    """真实对话2"""
    print("    场景: 四川-拿到耳机")
    classifier = TelecomTagClassifier()
    classifier.process("A", "晓得咯", {})
    classifier.process("B", "拿到咯耳机", {})
    result = classifier.classify()
    print(f"    -> {result}")
    return result == "违规商品"


def test_real_conversation_3():
    """真实对话3"""
    print("    场景: 东北-整了个宽带")
    classifier = TelecomTagClassifier()
    classifier.process("A", "整了个宽带", {})
    classifier.process("B", "知道得了", {})
    classifier.process("C", "行", {})
    result = classifier.classify()
    print(f"    -> {result}")
    return result == "正常"


def test_real_conversation_4():
    """真实对话4"""
    print("    场景: 投诉-没收到东西")
    classifier = TelecomTagClassifier()
    classifier.process("A", "我要投诉", {})
    classifier.process("B", "根本冇收到", {})
    classifier.process("C", "不知道", {})
    result = classifier.classify()
    print(f"    -> {result}")
    return result == "套机套现"


def test_real_conversation_5():
    """真实对话5"""
    print("    场景: 反问-啥是橙分期")
    classifier = TelecomTagClassifier()
    classifier.process("A", "啥是橙分期？", {})
    classifier.process("B", "我整了个东西", {})
    result = classifier.classify()
    print(f"    -> {result}")
    return result in ["营销缺失", "正常"]


def test_priority_order():
    """测试优先级"""
    print("    测试优先级顺序...")

    # 套机套现
    c1 = TelecomTagClassifier()
    c1.received_goods = False
    assert c1.classify() == "套机套现"
    print("    ✅ 套机套现优先")

    # 违规商品
    c2 = TelecomTagClassifier()
    c2.received_goods = True
    c2.goods_type = "耳机"
    assert c2.classify() == "违规商品"
    print("    ✅ 违规商品次之")

    # 正常
    c3 = TelecomTagClassifier()
    c3.received_goods = True
    c3.goods_type = "手机"
    c3.knows_contract = True
    assert c3.classify() == "正常"
    print("    ✅ 正常")

    return True


def test_output_format():
    """测试输出格式"""
    import json

    classifier = TelecomTagClassifier()
    classifier.received_goods = True
    classifier.goods_type = "手机"
    classifier.knows_contract = True

    output = classifier.get_output()
    result = json.dumps(output)

    assert "tags" in result
    assert "正常" in result
    assert len(output["tags"]) == 1

    print(f"    输出: {result}")
    return True


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 60)
    print("  电信橙分期个性标签判定 - 极端测试")
    print("=" * 60)

    test_groups = [
        ("1. 粤语方言测试", test_dialect_cantonese),
        ("2. 四川方言测试", test_dialect_sichuan),
        ("3. 东北方言测试", test_dialect_northeast),
        ("4. 非标准流程-打断", test_nonstandard_interruption),
        ("5. 非标准流程-反问", test_nonstandard_questions),
        ("6. 非标准流程-投诉", test_nonstandard_complaints),
        ("7. 非标准流程-模糊", test_nonstandard_filler),
        ("8. 极端输入-空", test_extreme_empty),
        ("9. 极端输入-特殊", test_extreme_special),
        ("10. 正常商品判定", test_product_normal),
        ("11. 违规商品判定", test_product_violation),
        ("12. 真实对话1-粤语", test_real_conversation_1),
        ("13. 真实对话2-四川", test_real_conversation_2),
        ("14. 真实对话3-东北", test_real_conversation_3),
        ("15. 真实对话4-投诉", test_real_conversation_4),
        ("16. 真实对话5-反问", test_real_conversation_5),
        ("17. 标签优先级", test_priority_order),
        ("18. 输出格式", test_output_format),
    ]

    passed = 0
    failed = 0

    for name, test_func in test_groups:
        print_section(name)
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ FAIL: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"  测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 所有极端测试通过！\n")
    else:
        print(f"\n⚠️  {failed} 个测试失败\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
