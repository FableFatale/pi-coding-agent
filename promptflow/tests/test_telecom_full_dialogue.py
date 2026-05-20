"""
电信橙分期个性标签判定 - 完整对话测试
基于整个外呼对话上下文判定标签
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
# 标签分类器 - 基于完整对话上下文
# ============================================================

class TelecomTagClassifier:
    """
    电信标签分类器 - 基于完整对话上下文

    判定逻辑：
    1. 分析整个对话历史，提取关键信息
    2. 按照优先级判断标签
    3. 考虑中途挂机、方言、矛盾表述等因素
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """重置分类器"""
        self.conversation = []  # 完整对话历史
        self.user_inputs = []    # 用户输入列表
        self.full_text = ""      # 完整文本
        self.turns = 0

        # 关键信息提取
        self.received_goods = None      # 是否收到商品
        self.received_goods_confirmed = False  # 是否明确确认
        self.goods_type = None          # 商品类型
        self.has_payment = False         # 是否有付费
        self.knows_contract = None      # 是否知晓合约
        self.knows_contract_confirmed = False  # 合约知晓是否确认
        self.is_cancelled = False        # 是否取消业务
        self.is_fraud = False           # 是否被骗
        self.is_complaint = False       # 是否投诉
        self.is_transfer = False         # 是否转人工

        # 状态标记
        self.hung_up = False            # 是否挂机
        self.no_response = False        # 是否无响应
        self.incomplete = True           # 是否对话未完成

    def process_dialogue(self, conversation: list):
        """
        处理完整对话

        Args:
            conversation: 对话列表 [{"user": "...", "ai": "..."}, ...]
        """
        self.conversation = conversation
        self.turns = len(conversation)

        # 合并所有用户输入
        all_user_text = " ".join([turn.get("user", "") for turn in conversation])
        self.full_text = all_user_text
        self.user_inputs = [turn.get("user", "") for turn in conversation]

        # 提取关键信息
        self._extract_goods_info()
        self._extract_contract_info()
        self._extract_attitude_info()
        self._check_ending_status()

    def _extract_goods_info(self):
        """提取商品信息"""
        text = self.full_text

        # 检测付费关键词 -> 已收到商品
        payment_keywords = ["付费", "花钱", "自费", "买", "花了", "花了钱", "花咯", "花啦",
                          "整咯", "整了个", "入手", "购买", "买的", "买咯"]
        if any(kw in text for kw in payment_keywords):
            self.has_payment = True
            self.received_goods = True

        # 检测已收到商品
        received_keywords = ["拿到了", "收到了", "有", "拿到了", "收到咯", "拿到咯",
                           "有收到", "拿到手了", "已经拿到", "拿到喽", "整了个", "装好了",
                           "安装好了", "买咯", "买了个", "搞了个"]
        if any(kw in text for kw in received_keywords):
            self.received_goods = True
            self.received_goods_confirmed = True

        # 检测未收到商品
        not_received_keywords = ["没拿到", "没收到", "没有", "什么都没", "只有钱",
                               "木有", "冇", "根本冇", "根本没", "没得", "未收到",
                               "没有收到", "未拿到", "没有拿到", "啥都没"]
        if any(kw in text for kw in not_received_keywords):
            self.received_goods = False

        # 方言检测-收到
        dialect_received = ["收到咯", "拿到咯", "收到啰", "拿到啰"]
        if any(kw in text for kw in dialect_received):
            self.received_goods = True
            self.received_goods_confirmed = True

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

    def _extract_contract_info(self):
        """提取合约信息"""
        text = self.full_text

        # 知晓合约
        knows_keywords = ["知道", "明白", "理解", "清楚", "晓得", "晓得了",
                         "知道咯", "晓得咯", "了解", "清楚了"]
        if any(kw in text for kw in knows_keywords):
            self.knows_contract = True
            self.knows_contract_confirmed = True

        # 不知晓合约
        not_knows_keywords = ["不知道", "不晓得", "不晓滴", "不造啊", "不造",
                             "没办过", "没要求", "不清", "不知道啥", "啥是", "啥玩意儿",
                             "咋还", "咋整", "咋回事", "不理解", "不晓得啥"]
        if any(kw in text for kw in not_knows_keywords):
            self.knows_contract = False

        # 方言
        dialect_known = ["晓得咯", "晓得喽", "晓得了", "知道得嘛", "知道得了"]
        dialect_unknown = ["不晓得咡", "不晓得咯", "母鸡啊"]
        if any(kw in text for kw in dialect_known):
            self.knows_contract = True
        if any(kw in text for kw in dialect_unknown):
            self.knows_contract = False

        # 用户主动询问 -> 说明不知晓
        question_keywords = ["啥", "什么", "怎么", "哪", "为啥", "为什么",
                          "咋", "咋整", "咋回事", "啥意思", "啥情况"]
        if any(kw in text for kw in question_keywords):
            # 如果只是简单询问，不一定不知晓
            pass

    def _extract_attitude_info(self):
        """提取态度信息"""
        text = self.full_text

        # 投诉
        complaint_keywords = ["投诉", "骗", "骗人", "被骗", "欺诈", "虚假",
                            "坑", "坑人", "垃圾", "太差", "不满", "不满意"]
        if any(kw in text for kw in complaint_keywords):
            self.is_complaint = True

        # 被骗
        fraud_keywords = ["被骗了", "被骗咯", "被坑", "被坑咯", "欺诈"]
        if any(kw in text for kw in fraud_keywords):
            self.is_fraud = True

        # 取消
        cancel_keywords = ["取消", "注销", "退了", "退掉", "不要了", "不办了"]
        if any(kw in text for kw in cancel_keywords):
            self.is_cancelled = True

        # 转人工
        transfer_keywords = ["转人工", "人工", "客服", "投诉"]
        if any(kw in text for kw in transfer_keywords):
            self.is_transfer = True

    def _check_ending_status(self):
        """检查结束状态"""
        # 检查最后一条用户输入
        if self.user_inputs:
            last_input = self.user_inputs[-1].strip()

            # 挂机关键词
            hangup_keywords = ["", "嗯", "啊", "哦", "挂", "滚", "拜", "再见",
                             "行", "好", "就这样", "挂了", "拜拜"]
            if last_input in ["", "嗯", "啊", "哦", "嗯嗯", "啊啊"]:
                self.hung_up = True

            # 零互动
            if len(self.user_inputs) == 1 and last_input == "":
                self.no_response = True

        # 如果轮次很少且无有效信息
        if self.turns < 2 and self.received_goods is None:
            self.hung_up = True

    def classify(self) -> str:
        """
        分类标签 - 基于完整对话上下文

        优先级:
        1. 未沟通 - 零互动/挂机
        2. 套机套现 - 未收到商品
        3. 违规商品 - 收到违规商品
        4. 营销缺失 - 收到商品但不知晓
        5. 正常 - 收到商品且知晓
        """
        # 规则0: 零互动/挂机 -> 未沟通
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

        # 兜底: 营销缺失
        return "营销缺失"

    def _is_no_communication(self) -> bool:
        """判断未沟通"""
        # 零互动
        if self.no_response:
            return True

        # 轮次<2且无有效信息
        if self.turns < 2 and self.received_goods is None:
            return True

        # 只有语气词
        if self.turns <= 2:
            filler_only = all(
                inp.strip() in ["", "嗯", "啊", "哦", "嗯嗯", "啊啊", "嗯嗯嗯"]
                for inp in self.user_inputs
            )
            if filler_only:
                return True

        return False

    def _is_cash_out(self) -> bool:
        """判断套机套现"""
        # 已收到商品=false 且 无付费
        if self.received_goods is False and not self.has_payment:
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

        # 被骗/投诉
        if self.is_fraud:
            return True

        # 被骗但拿到东西 -> 营销缺失
        if self.is_complaint and self.received_goods:
            return True

        # 不知道啥是橙分期 -> 营销缺失
        if "啥是" in self.full_text or "啥玩意儿" in self.full_text:
            if self.received_goods:
                return True

        return False

    def _is_normal(self) -> bool:
        """判断正常"""
        if self.received_goods and self.goods_type:
            # 必须是正常商品
            if self.goods_type in NORMAL_PRODUCTS:
                # 且知晓合约
                if self.knows_contract is True:
                    return True
        return False

    def get_output(self) -> dict:
        """获取输出"""
        return {"tags": [self.classify()]}

    def get_context_summary(self) -> dict:
        """获取上下文摘要"""
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
# 测试用例数据 - 基于完整对话
# ============================================================

# 完整对话测试用例
FULL_DIALOGUE_CASES = [
    # === 未沟通场景 ===
    {
        "name": "零互动-直接挂断",
        "dialogue": [
            {"user": "", "ai": "您好，请问是王先生吗？"}
        ],
        "expected": "未沟通",
        "reason": "用户零互动，直接挂断"
    },
    {
        "name": "短轮次-只说嗯",
        "dialogue": [
            {"user": "嗯", "ai": "您好，我是电信客服..."},
            {"user": "嗯嗯", "ai": "请问您知道橙分期业务吗？"}
        ],
        "expected": "未沟通",
        "reason": "用户只回复语气词"
    },
    {
        "name": "中途挂机-说话说到一半",
        "dialogue": [
            {"user": "我在办理的时候...", "ai": "请问您当时办理的是什么业务？"},
            {"user": "等一下我先", "ai": "好的请说"},
            {"user": "", "ai": "喂？"}
        ],
        "expected": "未沟通",
        "reason": "用户中途离开挂机"
    },
    {
        "name": "多次无响应",
        "dialogue": [
            {"user": "你好", "ai": "您好，请问您知道橙分期吗？"},
            {"user": "", "ai": "您好？"},
            {"user": "", "ai": "那打扰了，再见"}
        ],
        "expected": "未沟通",
        "reason": "多次无响应"
    },

    # === 正常场景 ===
    {
        "name": "正常-完整对话收到手机",
        "dialogue": [
            {"user": "是的我知道", "ai": "请问您当时办理橙分期拿到手机了吗？"},
            {"user": "拿到了，华为的", "ai": "好的，请问您知道每月需要还款吗？"},
            {"user": "知道，每月198", "ai": "好的，感谢您的配合"}
        ],
        "expected": "正常",
        "reason": "收到手机且知晓合约"
    },
    {
        "name": "正常-宽带安装",
        "dialogue": [
            {"user": "装好了宽带", "ai": "请问您知道橙分期的合约规则吗？"},
            {"user": "晓得咯，每月要还款", "ai": "好的，感谢配合"}
        ],
        "expected": "正常",
        "reason": "安装宽带且知晓合约"
    },
    {
        "name": "正常-方言确认",
        "dialogue": [
            {"user": "係啊收到咯", "ai": "请问您拿到的什么商品？"},
            {"user": "整了个路由器", "ai": "请问您知道合约规则吗？"},
            {"user": "知道得嘛", "ai": "好的"}
        ],
        "expected": "正常",
        "reason": "收到路由器，方言确认知晓"
    },

    # === 套机套现场景 ===
    {
        "name": "套机套现-只收到钱",
        "dialogue": [
            {"user": "我只收到钱，没拿到东西", "ai": "请问您知道橙分期业务吗？"},
            {"user": "知道啊", "ai": "好的"}
        ],
        "expected": "套机套现",
        "reason": "用户明确表示只收到钱"
    },
    {
        "name": "套机套现-什么都没收",
        "dialogue": [
            {"user": "我啥都没收到", "ai": "请问您办理的业务是什么情况？"},
            {"user": "就收到了折现", "ai": "好的明白了"}
        ],
        "expected": "套机套现",
        "reason": "用户什么都没收到"
    },
    {
        "name": "套机套现-方言",
        "dialogue": [
            {"user": "根本冇收到咯", "ai": "请问是什么情况？"},
            {"user": "只有钱", "ai": "好的"}
        ],
        "expected": "套机套现",
        "reason": "粤语方言说没收到"
    },

    # === 违规商品场景 ===
    {
        "name": "违规商品-耳机",
        "dialogue": [
            {"user": "我拿到了耳机", "ai": "请问您知道橙分期业务吗？"},
            {"user": "知道", "ai": "好的"}
        ],
        "expected": "违规商品",
        "reason": "耳机是违规商品"
    },
    {
        "name": "违规商品-空气炸锅",
        "dialogue": [
            {"user": "整了个空气炸锅", "ai": "请问您知道合约规则吗？"},
            {"user": "晓得咯", "ai": "好的"}
        ],
        "expected": "违规商品",
        "reason": "空气炸锅是违规商品"
    },
    {
        "name": "违规商品-锅",
        "dialogue": [
            {"user": "我拿了个锅", "ai": "请问您知道橙分期吗？"},
            {"user": "知道", "ai": "好的"}
        ],
        "expected": "违规商品",
        "reason": "锅是违规商品"
    },
    {
        "name": "违规商品-充电宝",
        "dialogue": [
            {"user": "拿到了个充电宝", "ai": "请问您知道合约吗？"},
            {"user": "知道", "ai": "好的"}
        ],
        "expected": "违规商品",
        "reason": "充电宝是违规商品"
    },

    # === 营销缺失场景 ===
    {
        "name": "营销缺失-不知道业务",
        "dialogue": [
            {"user": "我不知道啥是橙分期", "ai": "请问您当时办理的是...？"},
            {"user": "我整了个手机", "ai": "好的"}
        ],
        "expected": "营销缺失",
        "reason": "用户不知道业务定义"
    },
    {
        "name": "营销缺失-被询问后否认",
        "dialogue": [
            {"user": "我没办过这个业务", "ai": "请问您确定吗？"},
            {"user": "不记得", "ai": "好的"}
        ],
        "expected": "营销缺失",
        "reason": "用户否认办理过业务"
    },
    {
        "name": "营销缺失-投诉",
        "dialogue": [
            {"user": "我要投诉", "ai": "请问是什么问题？"},
            {"user": "他们骗人", "ai": "非常抱歉"}
        ],
        "expected": "营销缺失",
        "reason": "用户投诉被骗"
    },
    {
        "name": "营销缺失-反问",
        "dialogue": [
            {"user": "啥是橙分期？", "ai": "橙分期是..."},
            {"user": "咋还分期？", "ai": "每月需要..."}
        ],
        "expected": "营销缺失",
        "reason": "用户询问业务定义和还款方式"
    },
    {
        "name": "营销缺失-收到东西但不知晓",
        "dialogue": [
            {"user": "我收到了个东西", "ai": "请问您知道橙分期业务吗？"},
            {"user": "不知道", "ai": "好的"}
        ],
        "expected": "营销缺失",
        "reason": "收到商品但不知晓合约"
    },
    {
        "name": "营销缺失-被骗",
        "dialogue": [
            {"user": "我被骗了", "ai": "请问是什么情况？"},
            {"user": "当时说免费结果扣钱了", "ai": "非常抱歉"}
        ],
        "expected": "营销缺失",
        "reason": "用户表示被骗"
    },

    # === 边界场景 ===
    {
        "name": "边界-付费但收到违规商品",
        "dialogue": [
            {"user": "我花钱买的耳机", "ai": "好的"},
        ],
        "expected": "违规商品",
        "reason": "虽然付费，但耳机仍是违规商品"
    },
    {
        "name": "边界-方言长对话",
        "dialogue": [
            {"user": "係啊收到咯", "ai": "请问您拿到的是什么？"},
            {"user": "整了个耳机", "ai": "好的请问您知道合约吗？"},
            {"user": "晓得咯", "ai": "好的"}
        ],
        "expected": "违规商品",
        "reason": "粤语方言确认收到耳机"
    },
    {
        "name": "边界-矛盾表述",
        "dialogue": [
            {"user": "我收到了但好像又没收到", "ai": "请问具体是什么情况？"},
            {"user": "反正整了个东西", "ai": "好的请问您知道合约吗？"},
            {"user": "知道", "ai": "好的"}
        ],
        "expected": "正常",
        "reason": "矛盾表述但最终确认收到手机"
    },
    {
        "name": "边界-超长对话",
        "dialogue": [
            {"user": "我当时办的时候业务员说了一堆", "ai": "好的请问您记得吗？"},
            {"user": "他说每月只要付很少的钱就能拿个手机", "ai": "请问您当时拿到了吗？"},
            {"user": "拿到了，华为的", "ai": "好的请问您知道合约规则吗？"},
            {"user": "知道，每月要还款198", "ai": "好的感谢配合"}
        ],
        "expected": "正常",
        "reason": "长对话但信息完整确认"
    },
]


# ============================================================
# 测试类
# ============================================================

class TestFullDialogueClassification:
    """完整对话分类测试"""

    @pytest.fixture
    def classifier(self):
        return TelecomTagClassifier()

    @pytest.mark.parametrize("case", FULL_DIALOGUE_CASES, ids=lambda c: c["name"])
    def test_dialogue_classification(self, classifier, case):
        """测试对话分类"""
        classifier.reset()
        classifier.process_dialogue(case["dialogue"])
        result = classifier.classify()

        assert result == case["expected"], \
            f"{case['name']}: 期望'{case['expected']}' 实际'{result}' | 原因: {case['reason']}"


class TestNoCommunication:
    """未沟通场景测试"""

    @pytest.fixture
    def classifier(self):
        return TelecomTagClassifier()

    def test_zero_interaction(self, classifier):
        """测试零互动"""
        dialogue = [{"user": "", "ai": "您好"}]
        classifier.process_dialogue(dialogue)
        assert classifier.classify() == "未沟通"

    def test_only_filler_words(self, classifier):
        """测试只有语气词"""
        dialogue = [
            {"user": "嗯", "ai": "您好"},
            {"user": "嗯嗯", "ai": "请问您知道..."}
        ]
        classifier.process_dialogue(dialogue)
        assert classifier.classify() == "未沟通"

    def test_hung_up_mid_conversation(self, classifier):
        """测试中途挂机"""
        dialogue = [
            {"user": "等一下", "ai": "好的"},
            {"user": "", "ai": "喂？"}
        ]
        classifier.process_dialogue(dialogue)
        assert classifier.classify() == "未沟通"


class TestNormalScenario:
    """正常场景测试"""

    @pytest.fixture
    def classifier(self):
        return TelecomTagClassifier()

    def test_phone_with_contract_knowledge(self, classifier):
        """测试手机+知晓合约"""
        dialogue = [
            {"user": "拿到了华为手机", "ai": "好的"},
            {"user": "知道，每月要还款", "ai": "好的"}
        ]
        classifier.process_dialogue(dialogue)
        assert classifier.classify() == "正常"

    def test_broadband_installed(self, classifier):
        """测试宽带安装"""
        dialogue = [
            {"user": "装好了宽带", "ai": "好的"},
            {"user": "晓得咯", "ai": "好的"}
        ]
        classifier.process_dialogue(dialogue)
        assert classifier.classify() == "正常"

    def test_dialect_normal(self, classifier):
        """测试方言正常"""
        dialogue = [
            {"user": "係啊收到咯", "ai": "请问是什么商品？"},
            {"user": "整了个路由器", "ai": "好的"},
            {"user": "知道得嘛", "ai": "好的"}
        ]
        classifier.process_dialogue(dialogue)
        assert classifier.classify() == "正常"


class TestCashOutScenario:
    """套机套现场景测试"""

    @pytest.fixture
    def classifier(self):
        return TelecomTagClassifier()

    def test_only_cash_received(self, classifier):
        """测试只收到现金"""
        dialogue = [
            {"user": "我只收到钱，没拿东西", "ai": "好的"}
        ]
        classifier.process_dialogue(dialogue)
        assert classifier.classify() == "套机套现"

    def test_nothing_received(self, classifier):
        """测试什么都没收到"""
        dialogue = [
            {"user": "啥都没收到", "ai": "请问是什么情况？"},
            {"user": "就收到了折现", "ai": "好的"}
        ]
        classifier.process_dialogue(dialogue)
        assert classifier.classify() == "套机套现"

    def test_dialect_cash_out(self, classifier):
        """测试方言套机套现"""
        dialogue = [
            {"user": "根本冇收到咯", "ai": "请问？"},
            {"user": "只有钱", "ai": "好的"}
        ]
        classifier.process_dialogue(dialogue)
        assert classifier.classify() == "套机套现"


class TestViolationProductScenario:
    """违规商品场景测试"""

    @pytest.fixture
    def classifier(self):
        return TelecomTagClassifier()

    @pytest.mark.parametrize("product", ["耳机", "充电宝", "空气炸锅", "锅", "电视"])
    def test_violation_products(self, classifier, product):
        """测试各种违规商品"""
        dialogue = [
            {"user": f"拿到了{product}", "ai": "好的"},
            {"user": "知道", "ai": "好的"}
        ]
        classifier.process_dialogue(dialogue)
        assert classifier.classify() == "违规商品"


class TestMarketingLackScenario:
    """营销缺失场景测试"""

    @pytest.fixture
    def classifier(self):
        return TelecomTagClassifier()

    def test_dont_know_business(self, classifier):
        """测试不知道业务"""
        dialogue = [
            {"user": "我不知道啥是橙分期", "ai": "请问您办的是什么业务？"},
            {"user": "整了个手机", "ai": "好的"}
        ]
        classifier.process_dialogue(dialogue)
        assert classifier.classify() == "营销缺失"

    def test_complaint(self, classifier):
        """测试投诉"""
        dialogue = [
            {"user": "我要投诉", "ai": "请问是什么问题？"},
            {"user": "被骗了", "ai": "非常抱歉"}
        ]
        classifier.process_dialogue(dialogue)
        assert classifier.classify() == "营销缺失"

    def test_questions_about_business(self, classifier):
        """测试询问业务"""
        dialogue = [
            {"user": "啥是橙分期？", "ai": "橙分期是..."},
            {"user": "咋还钱？", "ai": "每月需要..."}
        ]
        classifier.process_dialogue(dialogue)
        assert classifier.classify() == "营销缺失"


class TestContextSummary:
    """上下文摘要测试"""

    def test_get_context_summary(self):
        """测试获取上下文摘要"""
        classifier = TelecomTagClassifier()
        dialogue = [
            {"user": "拿到了华为手机", "ai": "好的"},
            {"user": "知道", "ai": "好的"}
        ]
        classifier.process_dialogue(dialogue)
        summary = classifier.get_context_summary()

        assert "turns" in summary
        assert "received_goods" in summary
        assert "goods_type" in summary
        assert "label" in summary
        assert summary["goods_type"] == "手机"


class TestOutputFormat:
    """输出格式测试"""

    def test_output_format(self):
        """测试输出格式"""
        import json

        classifier = TelecomTagClassifier()
        dialogue = [{"user": "拿到了手机", "ai": "好的"}, {"user": "知道", "ai": "好的"}]
        classifier.process_dialogue(dialogue)

        output = classifier.get_output()
        result = json.dumps(output)

        assert "tags" in result
        assert len(output["tags"]) == 1
        assert output["tags"][0] in TAG_WHITELIST


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
