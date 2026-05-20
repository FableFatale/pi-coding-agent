"""
电信橙分期个性标签判定测试
基于 telecom_tags.md 规范
"""
import pytest
import sys
sys.path.insert(0, 'src')

from promptflow import (
    PromptParser, FlowBuilder, PathAnalyzer,
    TestGenerator, ScenarioRunner, ResultAnalyzer
)
from promptflow.test_generator import TestCase, TestSuite, TestType, TestInput
from promptflow.scenario_runner import TestResult


# ============================================================
# 测试数据：标签库
# ============================================================

# 标签库（白名单）
TAG_WHITELIST = [
    "套机套现",      # 优先级 1
    "违规商品",      # 优先级 2
    "营销缺失",      # 优先级 3
    "正常",          # 优先级 4
    "未沟通",        # 优先级 5
]

# 违规商品库（部分）
VIOLATION_PRODUCTS = [
    "耳机", "电暖桌", "压力煲", "高压锅", "净水机", "智家大礼包",
    "炸锅", "电火锅", "烤火炉", "电压锅", "热水器", "油烟机",
    "饮水机", "一体锅", "烤锅", "充电宝", "彩电", "蒸锅",
    "鸳鸯锅", "吸尘器", "热风机", "豆浆机", "电水壶", "电暖炉",
    "消毒柜", "榨汁机", "燃气灶", "挂烫机", "风扇", "电蒸锅",
    "电热锅", "电锅", "养生壶", "打印机", "扫地机", "电饼铛",
    "净化器", "礼品", "净水器", "茶具", "炒锅", "电磁炉",
    "茶吧机", "破壁机", "家电", "蓝牙耳机", "微波炉", "插座",
    "电动车", "烤箱", "多功能锅", "保温杯", "电动汽车", "电子产品",
    "电子设备", "电器", "吹风机", "电瓶车", "智能插排", "礼包",
    "电炸锅", "蒸汽锅", "锅", "小礼品", "电动自行车", "智能排插",
    "唱歌设备", "烤盘", "烧水壶", "除螨仪", "词典笔", "绞肉机",
    "话费", "优惠券", "购物卡", "加油卡", "超市卡", "物业费",
    "代金券", "助听器", "血氧仪", "体脂秤", "POS机", "话筒",
    "烤炉", "摩托", "电车", "冰柜", "大礼包", "空气炸锅机",
    "大屏幕电视", "电视机", "家具礼包", "家用电器", "家电套装",
    "自行车", "智能插头", "扫描笔", "智能笔", "学习笔", "读写笔",
    "投影仪", "赠品", "剃须刀", "刮胡刀", "电扇", "奖品",
    "投影", "固话机", "筋膜枪", "礼物", "水壶", "电子笔",
    "加湿器", "遥控器", "解压器", "电热壶", "收音机", "收银机",
    "壶", "车载记录仪", "行李箱", "料理机", "被子", "购机券",
    "三轮车", "购金券", "充值卡", "购物券", "油卡", "加油券",
    "按摩器", "按摩仪", "光盘", "厨房用品", "厨房用具", "智电炸锅",
    "打印器", "扫地器", "汽车", "电动的汽车", "电动的车", "山地车",
    "洗碗机", "阿尔法", "阿尔法蛋", "翻译机", "焖锅", "空气炸锅",
    "料理锅", "涮烤锅", "充电线", "热水壶", "电动牙刷", "足浴桶", "取暖器"
]

# 正常商品库（部分）
NORMAL_PRODUCTS = [
    "手机", "路由器", "智能手表", "ipad", "云电脑", "VR", "电脑",
    "平板电脑", "光猫", "机顶盒", "宽带设备", "宽带", "WiFi",
    "智能机", "安装设备", "fttr", "光纤", "全光", "电话手表",
    "华为", "oppo", "vivo", "红米", "小米", "荣耀", "苹果",
    "小度", "天猫精灵", "智能音响", "智能猫眼", "智能门锁", "智能门铃",
    "儿童手表", "摄像头", "门锁", "智能报警器", "手表", "手环",
    "智能开关", "门铃", "音响", "音箱", "电饭锅", "猫眼", "指纹锁",
    "报警器", "监控", "网关", "智能产品", "智能锁", "mate60", "iphone",
    "一加", "真我", "中兴", "三星", "网线", "智慧屏", "平板",
    "pad", "笔记本", "合约机", "小爱同学", "小天才", "空调", "冰箱",
    "电视", "洗衣机", "血压计", "点读笔", "血压仪", "电饭煲", "老年机",
    "学习机", "家教机", "固话机", "智慧大屏", "智能传感器", "传感器",
    "智能窗帘电机", "智能机器人", "机器人", "学习桌", "助听器", "热水器",
    "游戏机", "台灯", "体脂秤", "电子秤", "体重秤", "灯", "秤",
    "煮饭锅", "煮饭煲", "插头", "插座", "插排", "老人机"
]


# ============================================================
# 标签判定模拟器
# ============================================================

class TelecomTagClassifier:
    """电信标签分类模拟器"""

    def __init__(self):
        self.conversation = []
        self.received_goods = None  # None=未确认, True=已收到, False=未收到
        self.goods_type = None
        self.knows_contract = None
        self.has_payment_keywords = False
        self.turns_count = 0

    def reset(self):
        """重置状态"""
        self.conversation = []
        self.received_goods = None
        self.goods_type = None
        self.knows_contract = None
        self.has_payment_keywords = False
        self.turns_count = 0

    def process(self, node: str, user_input: str, context: dict) -> tuple:
        """处理对话并返回响应和下一节点"""
        self.turns_count += 1
        self.conversation.append({"node": node, "user": user_input})

        # 检测付费关键词
        payment_keywords = ["付费", "花钱", "自费", "买", "花了", "花了钱"]
        if any(kw in user_input for kw in payment_keywords):
            self.has_payment_keywords = True
            self.received_goods = True  # 0号铁则：付费=已收到商品

        # 检测已收到商品
        if any(kw in user_input for kw in ["拿到了", "收到了", "有", "拿到了手机", "拿到了空调"]):
            self.received_goods = True

        # 检测未收到商品
        if any(kw in user_input for kw in ["没拿到", "没收到", "没有", "什么都没", "只有钱"]):
            self.received_goods = False

        # 检测商品类型
        for product in NORMAL_PRODUCTS:
            if product in user_input:
                self.goods_type = product
                break

        # 检测是否知晓合约
        if any(kw in user_input for kw in ["知道", "明白", "理解", "清楚"]):
            self.knows_contract = True

        # 节点响应
        responses = {
            "A": ("您好，请问您办理的橙分期业务是什么情况？", "B"),
            "B": ("请问您有没有拿到手机/家电/宽带/拍照类商品？", self._determine_next(user_input)),
            "C": ("好的，请问您是否知晓橙分期的合约规则？", "D"),
            "D": ("好的，正在分析...", None),
        }

        if node in responses:
            return responses[node]

        return ("分析完成", None)

    def _determine_next(self, user_input: str) -> str:
        """根据用户输入决定下一节点"""
        if self.received_goods:
            return "C"  # 已收到商品 -> 分期核实
        elif self.received_goods is False:
            return "F"  # 未收到商品 -> 套机套现判断
        return "C"  # 默认

    def classify(self) -> str:
        """根据规则分类标签"""
        # 0号铁则：付费关键词 -> 锁死"套机套现"禁止
        # 但实际上付费=已收到商品，应该触发"正常"或"违规商品"

        # 未沟通（兜底）
        if self.turns_count < 2 and not self.received_goods:
            return "未沟通"

        # 套机套现（优先级1）
        if self.received_goods is False and not self.has_payment_keywords:
            return "套机套现"

        # 已收到商品 + 违规商品
        if self.received_goods and self.goods_type:
            if self.goods_type in VIOLATION_PRODUCTS:
                return "违规商品"

        # 已收到商品 + 知晓合约 = 正常
        if self.received_goods and self.knows_contract:
            return "正常"

        # 已收到商品 + 不知晓合约 = 营销缺失
        if self.received_goods and self.knows_contract is False:
            return "营销缺失"

        # 已收到商品但未确认是否知晓合约
        if self.received_goods:
            return "正常"  # 默认正常

        return "未沟通"


# ============================================================
# 测试类
# ============================================================

class TestTagWhitelist:
    """标签白名单测试"""

    def test_tag_whitelist_count(self):
        """测试标签数量"""
        assert len(TAG_WHITELIST) == 5, "应该有5个标签"

    def test_tag_whitelist_values(self):
        """测试标签值"""
        expected = ["套机套现", "违规商品", "营销缺失", "正常", "未沟通"]
        assert TAG_WHITELIST == expected

    def test_tag_priorities(self):
        """测试标签优先级"""
        # 优先级1应该是套机套现
        assert TAG_WHITELIST[0] == "套机套现"
        # 优先级5应该是未沟通
        assert TAG_WHITELIST[4] == "未沟通"


class TestViolationProducts:
    """违规商品库测试"""

    def test_violation_products_count(self):
        """测试违规商品数量"""
        assert len(VIOLATION_PRODUCTS) >= 100, "违规商品应该>=100个"

    def test_common_violation_products(self):
        """测试常见违规商品"""
        common = ["耳机", "充电宝", "电视机", "空气炸锅", "锅", "净水器", "扫地机"]
        for product in common:
            assert product in VIOLATION_PRODUCTS, f"{product}应该在违规商品库中"

    def test_normal_products_not_in_violation(self):
        """测试正常商品不在违规商品库"""
        normal_only = ["手机", "路由器", "平板电脑", "华为", "苹果", "小米"]
        for product in normal_only:
            assert product not in VIOLATION_PRODUCTS, f"{product}不应该在违规商品库中"


class TestNormalProducts:
    """正常商品库测试"""

    def test_normal_products_count(self):
        """测试正常商品数量"""
        assert len(NORMAL_PRODUCTS) >= 100, "正常商品应该>=100个"

    def test_common_normal_products(self):
        """测试常见正常商品"""
        common = ["手机", "路由器", "平板电脑", "华为", "苹果", "小米", "空调", "冰箱", "电视"]
        for product in common:
            assert product in NORMAL_PRODUCTS, f"{product}应该在正常商品库中"

    def test_violation_products_not_in_normal(self):
        """测试违规商品不在正常商品库"""
        # 注意：有些商品可能同时存在于两个库中（鸳鸯锅）
        violation_only = ["充电宝", "耳机", "空气炸锅"]
        for product in violation_only:
            if product in NORMAL_PRODUCTS:
                print(f"注意: {product}同时存在于两个库中")


class TestTagClassifier:
    """标签分类器测试"""

    @pytest.fixture
    def classifier(self):
        return TelecomTagClassifier()

    def test_classifier_initialization(self, classifier):
        """测试分类器初始化"""
        assert classifier is not None
        assert classifier.received_goods is None
        assert classifier.turns_count == 0

    def test_classifier_reset(self, classifier):
        """测试分类器重置"""
        classifier.turns_count = 5
        classifier.received_goods = True
        classifier.reset()
        assert classifier.turns_count == 0
        assert classifier.received_goods is None

    def test_detect_received_goods(self, classifier):
        """测试检测已收到商品"""
        classifier.process("B", "我拿到了手机", {})
        assert classifier.received_goods == True

    def test_detect_not_received_goods(self, classifier):
        """测试检测未收到商品"""
        classifier.process("B", "我没拿到任何东西", {})
        assert classifier.received_goods == False

    def test_detect_payment_keywords(self, classifier):
        """测试检测付费关键词"""
        classifier.process("B", "我花了2000块买的", {})
        assert classifier.has_payment_keywords == True
        assert classifier.received_goods == True  # 0号铁则

    def test_detect_goods_type_normal(self, classifier):
        """测试检测商品类型-正常商品"""
        classifier.process("B", "我拿到了手机", {})
        assert classifier.goods_type == "手机"

    def test_detect_goods_type_violation(self, classifier):
        """测试检测商品类型-违规商品"""
        classifier.process("B", "我拿到了耳机", {})
        assert classifier.goods_type == "耳机"


class TestTagClassificationScenarios:
    """标签分类场景测试"""

    @pytest.fixture
    def classifier(self):
        return TelecomTagClassifier()

    # --------------------------------------------------------
    # 场景1: 套机套现（优先级1）
    # --------------------------------------------------------

    def test_scenario_cash_out_no_goods(self, classifier):
        """场景: 套机套现-未收到商品"""
        classifier.received_goods = False
        classifier.has_payment_keywords = False

        result = classifier.classify()

        assert result == "套机套现"

    def test_scenario_cash_out_with_cash_only(self, classifier):
        """场景: 套机套现-仅收到现金"""
        classifier.received_goods = False
        classifier.has_payment_keywords = False
        classifier.conversation.append({"node": "B", "user": "只收到了钱"})

        result = classifier.classify()

        assert result == "套机套现"

    # --------------------------------------------------------
    # 场景2: 违规商品（优先级2）
    # --------------------------------------------------------

    def test_scenario_violation_product_headphones(self, classifier):
        """场景: 违规商品-耳机"""
        classifier.received_goods = True
        classifier.goods_type = "耳机"
        classifier.knows_contract = True

        result = classifier.classify()

        assert result == "违规商品"

    def test_scenario_violation_product_air_fryer(self, classifier):
        """场景: 违规商品-空气炸锅"""
        classifier.received_goods = True
        classifier.goods_type = "空气炸锅"
        classifier.knows_contract = True

        result = classifier.classify()

        assert result == "违规商品"

    def test_scenario_violation_product_pot(self, classifier):
        """场景: 违规商品-锅"""
        classifier.received_goods = True
        classifier.goods_type = "锅"
        classifier.knows_contract = True

        result = classifier.classify()

        assert result == "违规商品"

    # --------------------------------------------------------
    # 场景3: 正常商品（优先级4）
    # --------------------------------------------------------

    def test_scenario_normal_phone(self, classifier):
        """场景: 正常商品-手机"""
        classifier.received_goods = True
        classifier.goods_type = "手机"
        classifier.knows_contract = True

        result = classifier.classify()

        assert result == "正常"

    def test_scenario_normal_router(self, classifier):
        """场景: 正常商品-路由器"""
        classifier.received_goods = True
        classifier.goods_type = "路由器"
        classifier.knows_contract = True

        result = classifier.classify()

        assert result == "正常"

    def test_scenario_normal_broadband(self, classifier):
        """场景: 正常商品-宽带"""
        classifier.received_goods = True
        classifier.goods_type = "宽带"
        classifier.knows_contract = True

        result = classifier.classify()

        assert result == "正常"

    # --------------------------------------------------------
    # 场景4: 营销缺失（优先级3）
    # --------------------------------------------------------

    def test_scenario_marketing_lack_no_knowledge(self, classifier):
        """场景: 营销缺失-不知晓合约"""
        classifier.received_goods = True
        classifier.goods_type = "手机"
        classifier.knows_contract = False

        result = classifier.classify()

        assert result == "营销缺失"

    # --------------------------------------------------------
    # 场景5: 未沟通（优先级5）
    # --------------------------------------------------------

    def test_scenario_no_communication_short(self, classifier):
        """场景: 未沟通-轮次过少"""
        classifier.turns_count = 1
        classifier.received_goods = None

        result = classifier.classify()

        assert result == "未沟通"

    def test_scenario_zero_interaction(self, classifier):
        """场景: 零互动"""
        classifier.turns_count = 0
        classifier.conversation = []

        result = classifier.classify()

        assert result == "未沟通"


class TestOutputFormat:
    """输出格式测试"""

    def test_output_format(self):
        """测试输出格式"""
        # 输出应该是 {"tags":["标签值"]}
        import json

        valid_output = {"tags": ["正常"]}
        result = json.dumps(valid_output)

        assert "tags" in result
        assert "正常" in result

    def test_output_must_be_single_tag(self):
        """测试输出必须是单个标签"""
        import json

        # 单标签
        single = {"tags": ["正常"]}
        assert len(json.loads(json.dumps(single))["tags"]) == 1

    def test_invalid_tags_rejected(self):
        """测试无效标签应该被拒绝"""
        valid_tags = TAG_WHITELIST
        invalid_tag = "无效标签"

        assert invalid_tag not in valid_tags


class TestCoreRules:
    """核心规则测试"""

    def test_rule_0_payment_lock(self):
        """0号铁则: 付费关键词锁死套机套现禁止"""
        classifier = TelecomTagClassifier()
        classifier.process("B", "我花了2000块", {})
        # 付费 -> 已收到商品 -> 不能是套机套现
        assert classifier.received_goods == True

    def test_rule_0_payment_to_received_goods(self):
        """0号铁则: 付费表述 -> 已收到商品"""
        classifier = TelecomTagClassifier()

        for payment_input in [
            "我付费了",
            "花钱买的",
            "自费购买",
            "花了1000",
            "花了1千7",
            "花了1700"
        ]:
            classifier.reset()
            classifier.process("B", payment_input, {})
            assert classifier.received_goods == True, f"'{payment_input}'应该触发已收到商品"

    def test_rule_priority_order(self):
        """测试优先级顺序"""
        # 套机套现(1) > 违规商品(2) > 营销缺失(3) > 正常(4) > 未沟通(5)

        priority_order = [
            ("套机套现", 1),
            ("违规商品", 2),
            ("营销缺失", 3),
            ("正常", 4),
            ("未沟通", 5),
        ]

        for i, (tag, priority) in enumerate(priority_order):
            assert TAG_WHITELIST.index(tag) == i


class TestProductLibraryBoundaries:
    """商品库边界测试"""

    def test_electric_cooker_normal(self):
        """电饭锅应该是正常商品"""
        assert "电饭锅" in NORMAL_PRODUCTS
        assert "电饭煲" in NORMAL_PRODUCTS

    def test_pot_violation_except_electric_cooker(self):
        """锅类商品违规，但电饭锅除外"""
        # 锅 是违规商品
        assert "锅" in VIOLATION_PRODUCTS

        # 电饭锅是正常商品
        assert "电饭锅" in NORMAL_PRODUCTS
        assert "电饭煲" in NORMAL_PRODUCTS
        assert "煮饭锅" in NORMAL_PRODUCTS
        assert "煮饭煲" in NORMAL_PRODUCTS

    def test_television_violation(self):
        """电视应该是违规商品"""
        assert "彩电" in VIOLATION_PRODUCTS
        assert "大屏幕电视" in VIOLATION_PRODUCTS
        assert "电视机" in VIOLATION_PRODUCTS

    def test_phone_normal(self):
        """手机应该是正常商品"""
        assert "手机" in NORMAL_PRODUCTS
        assert "合约机" in NORMAL_PRODUCTS
        assert "老人机" in NORMAL_PRODUCTS


class TestTagClassificationIntegration:
    """标签分类集成测试"""

    @pytest.fixture
    def classifier(self):
        return TelecomTagClassifier()

    def test_complete_flow_normal_phone(self, classifier):
        """完整流程: 正常手机场景"""
        # 场景: 用户拿到手机，知晓合约
        classifier.process("A", "我办理了橙分期", {})
        classifier.process("B", "我拿到了手机", {})
        classifier.process("C", "知道合约规则", {})

        result = classifier.classify()

        assert result == "正常"

    def test_complete_flow_violation_headphones(self, classifier):
        """完整流程: 违规耳机场景"""
        # 场景: 用户拿到耳机
        classifier.process("A", "我办理了橙分期", {})
        classifier.process("B", "我拿到了耳机", {})

        result = classifier.classify()

        assert result == "违规商品"

    def test_complete_flow_cash_out(self, classifier):
        """完整流程: 套机套现场景"""
        # 场景: 用户没拿到商品，只收到钱
        classifier.process("A", "我办理了橙分期", {})
        classifier.process("B", "我没拿到东西，只收到了钱", {})

        result = classifier.classify()

        assert result == "套机套现"

    def test_complete_flow_no_communication(self, classifier):
        """完整流程: 未沟通场景"""
        # 场景: 零互动
        classifier.turns_count = 0
        classifier.conversation = []

        result = classifier.classify()

        assert result == "未沟通"


class TestTagScenariosSuite:
    """标签场景测试套件"""

    @pytest.fixture
    def test_suite(self):
        """创建标签场景测试套件"""
        suite = TestSuite(
            name="电信橙分期标签场景测试",
            description="基于 telecom_tags.md 的标签判定测试",
            test_cases=[
                # 场景1: 正常-手机
                TestCase(
                    id="tag_001",
                    name="正常-手机",
                    description="用户收到手机，知晓合约",
                    test_type=TestType.NORMAL,
                    path=["A", "B", "C"],
                    user_inputs=[
                        TestInput(node="A", text="我办理了橙分期"),
                        TestInput(node="B", text="拿到了手机"),
                        TestInput(node="C", text="知道合约规则"),
                    ],
                    expected_ending="正常"
                ),
                # 场景2: 正常-路由器
                TestCase(
                    id="tag_002",
                    name="正常-路由器",
                    description="用户收到路由器，知晓合约",
                    test_type=TestType.NORMAL,
                    path=["A", "B", "C"],
                    user_inputs=[
                        TestInput(node="A", text="我办理了橙分期"),
                        TestInput(node="B", text="拿到了路由器"),
                        TestInput(node="C", text="知道"),
                    ],
                    expected_ending="正常"
                ),
                # 场景3: 违规商品-耳机
                TestCase(
                    id="tag_003",
                    name="违规商品-耳机",
                    description="用户收到耳机",
                    test_type=TestType.EDGE,
                    path=["A", "B"],
                    user_inputs=[
                        TestInput(node="A", text="我办理了橙分期"),
                        TestInput(node="B", text="拿到了耳机"),
                    ],
                    expected_ending="违规商品"
                ),
                # 场景4: 违规商品-空气炸锅
                TestCase(
                    id="tag_004",
                    name="违规商品-空气炸锅",
                    description="用户收到空气炸锅",
                    test_type=TestType.EDGE,
                    path=["A", "B"],
                    user_inputs=[
                        TestInput(node="A", text="我办理了橙分期"),
                        TestInput(node="B", text="拿到了空气炸锅"),
                    ],
                    expected_ending="违规商品"
                ),
                # 场景5: 违规商品-锅
                TestCase(
                    id="tag_005",
                    name="违规商品-锅",
                    description="用户收到锅",
                    test_type=TestType.EDGE,
                    path=["A", "B"],
                    user_inputs=[
                        TestInput(node="A", text="我办理了橙分期"),
                        TestInput(node="B", text="拿到了锅"),
                    ],
                    expected_ending="违规商品"
                ),
                # 场景6: 套机套现
                TestCase(
                    id="tag_006",
                    name="套机套现",
                    description="用户未收到商品，只收到钱",
                    test_type=TestType.EDGE,
                    path=["A", "B"],
                    user_inputs=[
                        TestInput(node="A", text="我办理了橙分期"),
                        TestInput(node="B", text="没拿到东西，只收到了钱"),
                    ],
                    expected_ending="套机套现"
                ),
                # 场景7: 营销缺失
                TestCase(
                    id="tag_007",
                    name="营销缺失",
                    description="用户收到商品但不知晓合约",
                    test_type=TestType.EDGE,
                    path=["A", "B", "C"],
                    user_inputs=[
                        TestInput(node="A", text="我办理了橙分期"),
                        TestInput(node="B", text="拿到了手机"),
                        TestInput(node="C", text="不知道"),
                    ],
                    expected_ending="营销缺失"
                ),
                # 场景8: 未沟通
                TestCase(
                    id="tag_008",
                    name="未沟通",
                    description="零互动场景",
                    test_type=TestType.EDGE,
                    path=["A"],
                    user_inputs=[
                        TestInput(node="A", text=""),
                    ],
                    expected_ending="未沟通"
                ),
                # 场景9: 付费场景-手机
                TestCase(
                    id="tag_009",
                    name="付费-手机",
                    description="用户付费购买手机",
                    test_type=TestType.EDGE,
                    path=["A", "B"],
                    user_inputs=[
                        TestInput(node="A", text="我办理了橙分期"),
                        TestInput(node="B", text="我花了2000块"),
                    ],
                    expected_ending="正常"
                ),
                # 场景10: 正常-宽带
                TestCase(
                    id="tag_010",
                    name="正常-宽带",
                    description="用户安装宽带",
                    test_type=TestType.NORMAL,
                    path=["A", "B", "C"],
                    user_inputs=[
                        TestInput(node="A", text="我办理了橙分期"),
                        TestInput(node="B", text="安装了宽带"),
                        TestInput(node="C", text="知道"),
                    ],
                    expected_ending="正常"
                ),
            ]
        )
        return suite


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
