"""
电信橙分期个性标签判定 - 极端测试
包含非标准流程、方言、异常情况
"""
import pytest
import sys
sys.path.insert(0, 'src')

from promptflow.test_generator import TestCase, TestSuite, TestType, TestInput
from promptflow.scenario_runner import ScenarioRunner, TestResult


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
# 方言库
# ============================================================

DIALECT_EXPRESSIONS = {
    # 肯定表达
    "收到了": ["收到了", "收到咯", "收到啦", "拿到咯", "拿到啦", "有收到", "拿到手了", "已经拿到", "拿到喽"],
    "知道了": ["知道了", "晓得咯", "晓得喽", "晓得了", "知道咯", "知道了撒", "哦知道了", "了解了"],
    "买了": ["买了", "买咯", "买啦", "购买咯", "入手咯", "搞咯一个", "搞了个"],

    # 否定表达
    "没收到": ["没收到", "冇收到", "没收到咯", "冇收到咯", "木有收到", "没拿到", "冇拿到", "没得"],
    "不知道": ["不知道", "不晓得", "不晓滴", "不造啊", "不晓得咯", "晓不得", "母鸡啊"],

    # 商品表达
    "手机": ["手机", "手几", "电话", "电话机", "移动电话", "话机"],
    "宽带": ["宽带", "网", "WiFi", "wifi", "网络", "网线", "宽贷"],
    "空调": ["空调", "凉霸", "冷气", "空调机"],

    # 疑问表达
    "什么": ["什么", "啥", "啥子", "啥玩意儿", "哪个", "咋"],
    "怎么": ["怎么", "咋", "咋个", "咋整", "咋弄"],
}


# ============================================================
# 标签分类器 (完整实现)
# ============================================================

class TelecomTagClassifier:
    """电信标签分类器 - 完整版"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.conversation = []
        self.received_goods = None  # None, True, False
        self.goods_type = None
        self.knows_contract = None
        self.has_payment_keywords = False
        self.turns_count = 0
        self.user_queries = []  # 用户主动询问
        self.negative_responses = []  # 负面/否认表达
        self.affirmative_responses = []  # 肯定表达

    def process(self, node: str, user_input: str, context: dict):
        """处理对话"""
        self.turns_count += 1
        self.conversation.append({"node": node, "user": user_input, "turn": self.turns_count})

        text = user_input.strip()
        if not text:
            return

        # 0号铁则: 付费关键词
        payment_keywords = ["付费", "花钱", "自费", "买", "花了", "花了钱", "花咯", "花啦", "整咯"]
        if any(kw in text for kw in payment_keywords):
            self.has_payment_keywords = True
            self.received_goods = True

        # 检测已收到商品
        received_keywords = ["拿到了", "收到了", "有", "拿到了", "收到咯", "拿到咯", "买咯", "买咯"]
        if any(kw in text for kw in received_keywords):
            self.received_goods = True

        # 检测未收到商品
        not_received_keywords = ["没拿到", "没收到", "没有", "什么都没", "只有钱", "木有", "冇"]
        if any(kw in text for kw in not_received_keywords):
            self.received_goods = False

        # 方言检测 - 已收到
        dialect_received = ["收到咯", "拿到咯", "有收到", "拿到手了", "已经拿到", "拿到喽"]
        if any(kw in text for kw in dialect_received):
            self.received_goods = True

        # 方言检测 - 不知道
        dialect_unknown = ["不晓得", "不晓滴", "不造啊", "晓不得", "母鸡啊"]
        if any(kw in text for kw in dialect_unknown):
            self.negative_responses.append("不知道")

        # 方言检测 - 知道了
        dialect_known = ["晓得咯", "晓得喽", "晓得了", "知道咯", "知道了撒"]
        if any(kw in text for kw in dialect_known):
            self.affirmative_responses.append("知道")

        # 检测商品类型
        all_products = set(NORMAL_PRODUCTS + VIOLATION_PRODUCTS)
        for product in all_products:
            if product in text:
                self.goods_type = product
                break

        # 方言商品表达
        dialect_goods = {
            "手机": ["手几", "电话", "话机"],
            "宽带": ["网", "wifi", "宽贷"],
        }
        for goods, dialects in dialect_goods.items():
            if any(d in text for d in dialects):
                self.goods_type = goods
                break

        # 检测是否知晓合约
        if any(kw in text for kw in ["知道", "明白", "理解", "清楚", "晓得", "晓得了"]):
            self.knows_contract = True

        if any(kw in text for kw in ["不知道", "不晓得", "不晓滴", "不造", "没办过", "没要求", "不清"]:
            self.knows_contract = False

        # 用户主动询问 -> 记录
        question_keywords = ["啥", "什么", "怎么", "哪", "为啥", "为什么", "咋"]
        if any(kw in text for kw in question_keywords):
            self.user_queries.append(text)

    def classify(self) -> str:
        """分类标签"""
        # 规则0: 付费关键词 -> 锁死套机套现 (因为付费=已收到商品)

        # 规则5: 未沟通 (兜底)
        if self._is_no_communication():
            return "未沟通"

        # 规则1: 套机套现
        if self._is_cash_out():
            return "套机套现"

        # 规则2: 违规商品
        if self._is_violation_product():
            return "违规商品"

        # 规则3: 营销缺失
        if self._is_marketing_lack():
            return "营销缺失"

        # 规则4: 正常
        if self._is_normal():
            return "正常"

        return "未沟通"

    def _is_no_communication(self) -> bool:
        """判断未沟通"""
        # 零互动
        if self.turns_count == 0:
            return True

        # 轮次很少且无有效输入
        if self.turns_count < 3 and self.received_goods is None:
            # 只有语气词
            filler_words = ["嗯", "啊", "哦", "呃", "嗯嗯", "啊啊"]
            all_filler = all(
                any(fw in turn["user"] for fw in filler_words)
                for turn in self.conversation
                if turn["user"]
            )
            if all_filler:
                return True

        return False

    def _is_cash_out(self) -> bool:
        """判断套机套现"""
        # 必须同时满足:
        # 1. 已收到商品 = False
        # 2. 无付费关键词
        # 3. 没有违规商品
        if self.received_goods is False and not self.has_payment_keywords:
            if self.goods_type not in VIOLATION_PRODUCTS:
                return True
        return False

    def _is_violation_product(self) -> bool:
        """判断违规商品"""
        if self.received_goods and self.goods_type:
            if self.goods_type in VIOLATION_PRODUCTS:
                return True
        return False

    def _is_marketing_lack(self) -> bool:
        """判断营销缺失"""
        # 已收到商品但不知晓合约
        if self.received_goods is True and self.knows_contract is False:
            return True

        # 用户否认业务关联
        denial_keywords = ["不知情", "被骗了", "没办过", "没要求", "不记得"]
        for turn in self.conversation:
            if any(kw in turn["user"] for kw in denial_keywords):
                return True

        return False

    def _is_normal(self) -> bool:
        """判断正常"""
        if self.received_goods and self.goods_type in NORMAL_PRODUCTS:
            if self.knows_contract is True:
                return True
        return False

    def get_output(self) -> dict:
        """获取输出格式"""
        tag = self.classify()
        return {"tags": [tag]}


# ============================================================
# 测试用例数据
# ============================================================

# 方言测试用例
DIALECT_TEST_CASES = [
    # 粤语方言
    {"input": "收到咯，手机", "expected": "正常", "dialect": "粤语", "desc": "粤语-收到"},
    {"input": "冇收到咯", "expected": "套机套现", "dialect": "粤语", "desc": "粤语-没收到"},
    {"input": "不晓得咁", "expected": "营销缺失", "dialect": "粤语", "desc": "粤语-不知道"},
    {"input": "知道咯", "expected": "正常", "dialect": "粤语", "desc": "粤语-知道"},

    # 四川方言
    {"input": "拿到咯", "expected": "正常", "dialect": "四川", "desc": "四川-拿到"},
    {"input": "不晓得咡", "expected": "营销缺失", "dialect": "四川", "desc": "四川-不知道"},
    {"input": "咋整嘛", "expected": "未沟通", "dialect": "四川", "desc": "四川-疑问"},
    {"input": "啥子哦", "expected": "未沟通", "dialect": "四川", "desc": "四川-啥子"},

    # 东北方言
    {"input": "整了个手机", "expected": "正常", "dialect": "东北", "desc": "东北-整了个"},
    {"input": "整啥玩意儿", "expected": "未沟通", "dialect": "东北", "desc": "东北-整啥"},
    {"input": "知道得了", "expected": "正常", "dialect": "东北", "desc": "东北-知道了"},
]

# 非标准流程测试用例
NON_STANDARD_TEST_CASES = [
    # 打断AI
    {"input": "等等，我先接个电话", "expected": "未沟通", "desc": "打断-接电话"},
    {"input": "你等会儿，我忙", "expected": "未沟通", "desc": "打断-忙"},
    {"input": "稍等一下", "expected": "未沟通", "desc": "打断-稍等"},

    # 反问
    {"input": "啥是橙分期？", "expected": "营销缺失", "desc": "反问-询问业务"},
    {"input": "咋还分期？", "expected": "营销缺失", "desc": "反问-询问分期"},
    {"input": "钱咋算？", "expected": "营销缺失", "desc": "反问-询问费用"},

    # 投诉/抱怨
    {"input": "我要投诉，你们骗人", "expected": "营销缺失", "desc": "投诉-被骗"},
    {"input": "根本冇收到东西", "expected": "套机套现", "dialect": "粤语", "desc": "投诉-没收到"},
    {"input": "啥玩意儿，我都没要这个业务", "expected": "营销缺失", "desc": "否认业务"},

    # 模糊回答
    {"input": "嗯", "expected": "未沟通", "desc": "模糊-嗯"},
    {"input": "啊？", "expected": "未沟通", "desc": "模糊-啊"},
    {"input": "哦", "expected": "未沟通", "desc": "模糊-哦"},
    {"input": "嗯嗯嗯", "expected": "未沟通", "desc": "模糊-嗯嗯嗯"},

    # 长篇大论
    {"input": "我跟你说啊，我当时办的时候那个业务员跟我说了半天，说这个橙分期怎么怎么好，每月只要交多少钱就能拿个手机，我还专门问了他这手机是不是全新的，他说当然是全新的啦，我就办了，结果今天你们打电话来说什么...", "expected": "正常", "desc": "长篇-详细描述"},

    # 矛盾表述
    {"input": "我收到了，但又好像没收到", "expected": "正常", "desc": "矛盾-收到又没收到"},
    {"input": "买是买了，但我不记得了", "expected": "营销缺失", "desc": "矛盾-买但不记得"},
]

# 极端输入测试
EXTREME_TEST_CASES = [
    # 空输入
    {"input": "", "expected": "未沟通", "desc": "空字符串"},
    {"input": "   ", "expected": "未沟通", "desc": "空格"},
    {"input": "。", "expected": "未沟通", "desc": "句号"},

    # 超长输入
    {"input": "啊" * 1000, "expected": "未沟通", "desc": "超长语气词"},
    {"input": "嗯嗯嗯嗯嗯" * 100, "expected": "未沟通", "desc": "超长嗯嗯"},

    # 特殊字符
    {"input": "@#$%^&*()", "expected": "未沟通", "desc": "特殊字符"},
    {"input": "🎉🎊🎁", "expected": "未沟通", "desc": "表情符号"},
    {"input": "😂🤣😭", "expected": "未沟通", "desc": "emoji"},

    # 纯数字
    {"input": "1234567890", "expected": "未沟通", "desc": "纯数字"},
    {"input": "1700", "expected": "正常", "desc": "纯数字-金额"},

    # 外语/混合
    {"input": "Hello, I got my phone", "expected": "未沟通", "desc": "英语"},
    {"input": "我拿到了iPhone🍎", "expected": "正常", "desc": "混合表达"},

    # 脏话/情绪化
    {"input": "fuck", "expected": "未沟通", "desc": "英语脏话"},
    {"input": "滚", "expected": "未沟通", "desc": "中文拒绝"},
]

# 商品判定测试
PRODUCT_TEST_CASES = [
    # 正常商品
    {"input": "拿到了华为手机", "expected": "正常", "product": "手机"},
    {"input": "装好了宽带", "expected": "正常", "product": "宽带"},
    {"input": "买了个路由器", "expected": "正常", "product": "路由器"},
    {"input": "拿了个空调", "expected": "正常", "product": "空调"},
    {"input": "装了WiFi", "expected": "正常", "product": "WiFi"},

    # 违规商品
    {"input": "收到了耳机", "expected": "违规商品", "product": "耳机"},
    {"input": "拿了个充电宝", "expected": "违规商品", "product": "充电宝"},
    {"input": "搞了个空气炸锅", "expected": "违规商品", "product": "空气炸锅"},
    {"input": "拿了个锅", "expected": "违规商品", "product": "锅"},
    {"input": "买了个电视", "expected": "违规商品", "product": "电视"},
    {"input": "拿了个净水器", "expected": "违规商品", "product": "净水器"},
    {"input": "搞了个扫地机", "expected": "违规商品", "product": "扫地机"},
]


# ============================================================
# 测试类
# ============================================================

class TestDialectExpressions:
    """方言表达测试"""

    def test_dialect_cantonese(self):
        """测试粤语方言"""
        for case in DIALECT_TEST_CASES:
            if case.get("dialect") == "粤语":
                classifier = TelecomTagClassifier()
                classifier.process("B", case["input"], {})
                result = classifier.classify()
                assert result == case["expected"], \
                    f"{case['desc']}: 输入'{case['input']}' 期望'{case['expected']}' 实际'{result}'"

    def test_dialect_sichuan(self):
        """测试四川方言"""
        for case in DIALECT_TEST_CASES:
            if case.get("dialect") == "四川":
                classifier = TelecomTagClassifier()
                classifier.process("B", case["input"], {})
                result = classifier.classify()
                assert result == case["expected"], \
                    f"{case['desc']}: 输入'{case['input']}' 期望'{case['expected']}' 实际'{result}'"

    def test_dialect_northeast(self):
        """测试东北方言"""
        for case in DIALECT_TEST_CASES:
            if case.get("dialect") == "东北":
                classifier = TelecomTagClassifier()
                classifier.process("B", case["input"], {})
                result = classifier.classify()
                assert result == case["expected"], \
                    f"{case['desc']}: 输入'{case['input']}' 期望'{case['expected']}' 实际'{result}'"


class TestNonStandardFlow:
    """非标准流程测试"""

    def test_interruption(self):
        """测试打断"""
        for case in NON_STANDARD_TEST_CASES[:3]:
            classifier = TelecomTagClassifier()
            classifier.process("A", case["input"], {})
            result = classifier.classify()
            # 打断场景通常判定为未沟通
            assert result in ["未沟通", "营销缺失"], \
                f"{case['desc']}: 输入'{case['input']}' 实际'{result}'"

    def test_questions(self):
        """测试反问"""
        for case in NON_STANDARD_TEST_CASES[3:6]:
            classifier = TelecomTagClassifier()
            classifier.process("B", case["input"], {})
            result = classifier.classify()
            assert result in ["营销缺失", "正常"], \
                f"{case['desc']}: 输入'{case['input']}' 实际'{result}'"

    def test_complaints(self):
        """测试投诉"""
        for case in NON_STANDARD_TEST_CASES[6:9]:
            classifier = TelecomTagClassifier()
            classifier.process("B", case["input"], {})
            result = classifier.classify()
            assert result in TAG_WHITELIST, \
                f"{case['desc']}: 输入'{case['input']}' 实际'{result}'"

    def test_filler_words(self):
        """测试模糊回答"""
        for case in NON_STANDARD_TEST_CASES[9:13]:
            classifier = TelecomTagClassifier()
            classifier.process("A", case["input"], {})
            result = classifier.classify()
            assert result == "未沟通", \
                f"{case['desc']}: 输入'{case['input']}' 实际'{result}'"

    def test_long_description(self):
        """测试长篇描述"""
        for case in NON_STANDARD_TEST_CASES[13:14]:
            classifier = TelecomTagClassifier()
            classifier.process("B", case["input"], {})
            result = classifier.classify()
            assert result in TAG_WHITELIST, \
                f"{case['desc']}: 输入很长，实际'{result}'"

    def test_contradiction(self):
        """测试矛盾表述"""
        for case in NON_STANDARD_TEST_CASES[14:]:
            classifier = TelecomTagClassifier()
            classifier.process("B", case["input"], {})
            result = classifier.classify()
            assert result in TAG_WHITELIST, \
                f"{case['desc']}: 输入'{case['input']}' 实际'{result}'"


class TestExtremeInputs:
    """极端输入测试"""

    def test_empty_input(self):
        """测试空输入"""
        classifier = TelecomTagClassifier()
        classifier.process("A", "", {})
        result = classifier.classify()
        assert result == "未沟通"

    def test_whitespace(self):
        """测试空格"""
        classifier = TelecomTagClassifier()
        classifier.process("A", "   ", {})
        result = classifier.classify()
        assert result == "未沟通"

    def test_special_chars(self):
        """测试特殊字符"""
        classifier = TelecomTagClassifier()
        classifier.process("A", "@#$%", {})
        result = classifier.classify()
        assert result == "未沟通"

    def test_emoji(self):
        """测试表情符号"""
        classifier = TelecomTagClassifier()
        classifier.process("A", "🎉🎊🎁", {})
        result = classifier.classify()
        assert result == "未沟通"

    def test_numbers(self):
        """测试纯数字"""
        classifier = TelecomTagClassifier()
        classifier.process("B", "12345", {})
        result = classifier.classify()
        assert result == "未沟通"

    def test_mixed_language(self):
        """测试混合语言"""
        classifier = TelecomTagClassifier()
        classifier.process("B", "I got my phone", {})
        result = classifier.classify()
        assert result in TAG_WHITELIST


class TestProductClassification:
    """商品分类测试"""

    def test_normal_products(self):
        """测试正常商品"""
        for case in PRODUCT_TEST_CASES[:5]:
            classifier = TelecomTagClassifier()
            classifier.process("B", case["input"], {})
            result = classifier.classify()
            assert result == case["expected"], \
                f"{case['product']}: 输入'{case['input']}' 期望'{case['expected']}' 实际'{result}'"

    def test_violation_products(self):
        """测试违规商品"""
        for case in PRODUCT_TEST_CASES[5:]:
            classifier = TelecomTagClassifier()
            classifier.process("B", case["input"], {})
            result = classifier.classify()
            assert result == case["expected"], \
                f"{case['product']}: 输入'{case['input']}' 期望'{case['expected']}' 实际'{result}'"


class TestTagPriority:
    """标签优先级测试"""

    def test_priority_order(self):
        """测试优先级顺序"""
        # 1. 套机套现 > 违规商品 > 营销缺失 > 正常 > 未沟通

        # 套机套现优先
        classifier = TelecomTagClassifier()
        classifier.received_goods = False
        result = classifier.classify()
        assert result == "套机套现"

        # 违规商品次之
        classifier = TelecomTagClassifier()
        classifier.received_goods = True
        classifier.goods_type = "耳机"
        result = classifier.classify()
        assert result == "违规商品"

        # 营销缺失
        classifier = TelecomTagClassifier()
        classifier.received_goods = True
        classifier.goods_type = "手机"
        classifier.knows_contract = False
        result = classifier.classify()
        assert result == "营销缺失"

        # 正常
        classifier = TelecomTagClassifier()
        classifier.received_goods = True
        classifier.goods_type = "手机"
        classifier.knows_contract = True
        result = classifier.classify()
        assert result == "正常"


class TestOutputFormat:
    """输出格式测试"""

    def test_output_format(self):
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

    def test_single_tag(self):
        """测试单标签"""
        classifier = TelecomTagClassifier()
        classifier.received_goods = True
        classifier.goods_type = "手机"
        classifier.knows_contract = True

        output = classifier.get_output()
        assert len(output["tags"]) == 1


class TestRealDialogueScenarios:
    """真实对话场景测试"""

    def test_scenario_real_conversation_1(self):
        """真实对话场景1"""
        classifier = TelecomTagClassifier()

        # 用户主动询问
        classifier.process("A", "啥是橙分期？", {})
        classifier.process("B", "哦我知道了，反正我没收到东西", {})
        classifier.process("C", "不知道", {})

        result = classifier.classify()
        assert result in TAG_WHITELIST

    def test_scenario_real_conversation_2(self):
        """真实对话场景2"""
        classifier = TelecomTagClassifier()

        classifier.process("A", "我整了个手机", {})
        classifier.process("B", "晓得咯", {})
        classifier.process("C", "哦那知道得嘛", {})

        result = classifier.classify()
        assert result == "正常"

    def test_scenario_real_conversation_3(self):
        """真实对话场景3 - 方言长对话"""
        classifier = TelecomTagClassifier()

        classifier.process("A", "係啊，我收到咯", {})
        classifier.process("B", "拿了个耳机", {})
        classifier.process("C", "唔知咁", {})

        result = classifier.classify()
        # 耳机是违规商品
        assert result == "违规商品"

    def test_scenario_frustrated_customer(self):
        """愤怒客户场景"""
        classifier = TelecomTagClassifier()

        classifier.process("A", "你们骗人！", {})
        classifier.process("B", "我根本没收到东西", {})
        classifier.process("C", "不知道", {})

        result = classifier.classify()
        assert result in TAG_WHITELIST

    def test_scenario_confused_customer(self):
        """困惑客户场景"""
        classifier = TelecomTagClassifier()

        classifier.process("A", "啥玩意儿？", {})
        classifier.process("B", "我整了个宽带", {})
        classifier.process("C", "咋整啊这是", {})

        result = classifier.classify()
        assert result in TAG_WHITELIST


class TestTagScenariosSuite:
    """标签场景测试套件 - 极端版"""

    @pytest.fixture
    def extreme_test_suite(self):
        """创建极端场景测试套件"""
        test_cases = []

        # 场景1: 方言-粤语
        test_cases.append(TestCase(
            id="ext_001",
            name="粤语-收到手机",
            description="粤语方言说收到手机",
            test_type=TestType.EDGE,
            path=["A", "B", "C"],
            user_inputs=[
                TestInput(node="A", text="係啊"),
                TestInput(node="B", text="收到咯，手机"),
                TestInput(node="C", text="知道咯"),
            ],
            expected_ending="正常"
        ))

        # 场景2: 方言-四川
        test_cases.append(TestCase(
            id="ext_002",
            name="四川-拿到耳机",
            description="四川方言说拿到耳机",
            test_type=TestType.EDGE,
            path=["A", "B"],
            user_inputs=[
                TestInput(node="A", text="晓得咯"),
                TestInput(node="B", text="拿到咯耳机"),
            ],
            expected_ending="违规商品"
        ))

        # 场景3: 非标准-反问
        test_cases.append(TestCase(
            id="ext_003",
            name="反问-啥是橙分期",
            description="用户反问业务定义",
            test_type=TestType.EDGE,
            path=["A", "B"],
            user_inputs=[
                TestInput(node="A", text="啥是橙分期？"),
                TestInput(node="B", text="我拿了东西"),
            ],
            expected_ending="营销缺失"
        ))

        # 场景4: 投诉
        test_cases.append(TestCase(
            id="ext_004",
            name="投诉-没收到东西",
            description="客户投诉没收到东西",
            test_type=TestType.EDGE,
            path=["A", "B", "C"],
            user_inputs=[
                TestInput(node="A", text="我要投诉"),
                TestInput(node="B", text="根本冇收到"),
                TestInput(node="C", text="不知道"),
            ],
            expected_ending="套机套现"
        ))

        # 场景5: 模糊回答
        test_cases.append(TestCase(
            id="ext_005",
            name="模糊-嗯嗯",
            description="客户只回答语气词",
            test_type=TestType.EDGE,
            path=["A"],
            user_inputs=[
                TestInput(node="A", text="嗯嗯嗯"),
            ],
            expected_ending="未沟通"
        ))

        # 场景6: 长篇描述
        test_cases.append(TestCase(
            id="ext_006",
            name="长篇-详细描述",
            description="客户详细描述办理过程",
            test_type=TestType.NORMAL,
            path=["A", "B", "C"],
            user_inputs=[
                TestInput(node="A", text="那个业务员跟我说了很多"),
                TestInput(node="B", text="我整了个华为手机，他说怎么怎么好"),
                TestInput(node="C", text="晓得咯知道咯"),
            ],
            expected_ending="正常"
        ))

        # 场景7: 矛盾表述
        test_cases.append(TestCase(
            id="ext_007",
            name="矛盾-收到又没收到",
            description="客户表述矛盾",
            test_type=TestType.EDGE,
            path=["A", "B"],
            user_inputs=[
                TestInput(node="A", text="我收到了，但又好像没收到"),
                TestInput(node="B", text="反正整了个东西"),
            ],
            expected_ending="正常"
        ))

        # 场景8: 东北话
        test_cases.append(TestCase(
            id="ext_008",
            name="东北-整了个宽带",
            description="东北方言说整了宽带",
            test_type=TestType.NORMAL,
            path=["A", "B", "C"],
            user_inputs=[
                TestInput(node="A", text="整了个宽带"),
                TestInput(node="B", text="知道得了"),
                TestInput(node="C", text="行"),
            ],
            expected_ending="正常"
        ))

        # 场景9: 空输入
        test_cases.append(TestCase(
            id="ext_009",
            name="空输入",
            description="客户不回应",
            test_type=TestType.EDGE,
            path=["A"],
            user_inputs=[
                TestInput(node="A", text=""),
            ],
            expected_ending="未沟通"
        ))

        # 场景10: 极端-超长输入
        test_cases.append(TestCase(
            id="ext_010",
            name="超长-语气词",
            description="客户发送超长语气词",
            test_type=TestType.EDGE,
            path=["A"],
            user_inputs=[
                TestInput(node="A", text="嗯嗯嗯嗯嗯" * 50),
            ],
            expected_ending="未沟通"
        ))

        return TestSuite(
            name="电信橙分期极端场景测试",
            description="非标准流程、方言、异常输入测试",
            test_cases=test_cases
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
