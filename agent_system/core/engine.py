"""
对话引擎 - 核心编排器
"""
from typing import Tuple, Optional, Dict, Any
from .state import DialogState, CustomerInfo, NodeType, ScenarioType
from .context import ContextBuilder
from ..rules.products import product_matcher
from ..rules.dialect import dialect_converter
from ..rules.semantics import semantic_analyzer, IntentType
from ..rules.nodes import NodeIds


class AgentEngine:
    """Agent对话引擎"""
    
    def __init__(self, customer_info: CustomerInfo):
        self.state = DialogState(
            current_node=NodeType.A,
            customer=customer_info
        )
        self.context_builder = ContextBuilder()
        self._llm_client = None  # 外部注入
    
    def set_llm_client(self, client):
        """设置LLM客户端"""
        self._llm_client = client
    
    def process_turn(self, user_input: str) -> Tuple[str, str]:
        """
        处理一轮对话
        返回: (agent回复, 下一节点ID)
        """
        # 0. 预处理
        normalized_input, meta = dialect_converter.normalize_response(user_input)
        
        # 1. 检查用户是否在询问橙分期
        is_asking_installment = self._check_asking_installment(normalized_input)
        
        # 2. 执行当前节点的处理器
        current_handler = self._get_node_handler(self.state.current_node)
        if current_handler:
            response, next_node = current_handler(self.state, normalized_input, meta)
        else:
            response = "抱歉，系统需要更多信息。"
            next_node = NodeType.END
        
        # 3. 记录对话
        self.state.add_record(
            node=self.state.current_node.value,
            user_input=user_input,
            agent_response=response
        )
        
        # 4. 更新状态
        self.state.last_node = self.state.current_node
        self.state.current_node = next_node
        self.state.is_first_turn = False
        
        return response, next_node.value
    
    def _check_asking_installment(self, text: str) -> bool:
        """检查用户是否在询问橙分期"""
        keywords = ["什么是橙分期", "橙分期是什么", "什么业务", "什么意思"]
        for kw in keywords:
            if kw in text:
                return True
        return False
    
    def _get_node_handler(self, node_type: NodeType):
        """获取节点处理器"""
        handlers = {
            NodeType.A: self._handle_node_a,
            NodeType.B: self._handle_node_b,
            NodeType.D: self._handle_node_d,
            NodeType.E: self._handle_node_e,
            NodeType.F: self._handle_node_f,
            NodeType.G: self._handle_node_g,
            NodeType.H: self._handle_node_h,
            NodeType.I: self._handle_node_i,
            NodeType.J: self._handle_node_j,
            NodeType.K: self._handle_node_k,
            NodeType.L: self._handle_node_l,
            NodeType.M: self._handle_node_m,
            NodeType.N: self._handle_node_n,
            NodeType.O: self._handle_node_o,
            NodeType.P: self._handle_node_p,
            NodeType.Q: self._handle_node_q,
            NodeType.T: self._handle_node_t,
            NodeType.U: self._handle_node_u,
        }
        return handlers.get(node_type)
    
    # ============ 节点处理器 ============
    
    def _handle_node_a(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点A: 确认本人"""
        # 标准化分析
        intent, confidence, _ = semantic_analyzer.analyze(user_input)
        
        # 非本人
        if semantic_analyzer.is_not_self(user_input):
            return self._generate_ask_if_know_response(state), NodeType.B
        
        # 亲属关系处理
        if meta.get("is_family"):
            return self._generate_ask_if_know_response(state), NodeType.B
        
        # 本人
        if intent == IntentType.AFFIRMATIVE:
            return self._generate_permission_request(state), NodeType.D
        
        # 不明确 - 再次确认
        return "请问您是{}本人吗？".format(state.customer.name), NodeType.A
    
    def _handle_node_b(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点B: 非本人处理 - 询问是否认识"""
        # 检查是否认识
        if meta.get("is_family") or "认识" in user_input:
            return self._generate_transfer_message(state), NodeType.U
        
        # 不认识
        return self._generate_not_know_ending(), NodeType.T
    
    def _handle_node_d(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点D: 获取回访许可"""
        intent, _, _ = semantic_analyzer.analyze(user_input)
        
        if semantic_analyzer.is_refusal(user_input):
            return self._generate_refusal_response(state), NodeType.E
        
        if semantic_analyzer.is_busy(user_input):
            return self._generate_busy_response(state), NodeType.F
        
        if semantic_analyzer.is_complaint(user_input):
            return self._generate_complaint_listen(), NodeType.G
        
        if intent == IntentType.AFFIRMATIVE:
            return self._generate_contract_query(state), NodeType.K
        
        # 不明确 - 继续
        return self._generate_contract_query(state), NodeType.K
    
    def _handle_node_k(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点K: 核实合约期"""
        # K节点规则：除明确中断外，所有回复都推进到下一节点
        intent, _, _ = semantic_analyzer.analyze(user_input)
        
        if semantic_analyzer.is_refusal(user_input):
            return "", NodeType.E
        
        if semantic_analyzer.is_busy(user_input):
            return self._generate_busy_first_response(), NodeType.F
        
        if semantic_analyzer.is_complaint(user_input):
            return self._generate_complaint_listen(), NodeType.G
        
        # 进入手机核实
        return self._generate_phone_query(state), NodeType.L
    
    def _handle_node_l(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点L: 核实手机类"""
        # 检查是否拿到了手机/优惠
        has_phone = product_matcher.has_phone(user_input)
        has_discount_mention = "优惠" in user_input
        
        if has_phone or has_discount_mention:
            state.has_phone = True
            state.scenario = ScenarioType.A
            return self._generate_installment_query(state), NodeType.N
        
        # 继续到宽带
        return self._generate_broadband_query(state), NodeType.M
    
    def _handle_node_m(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点M: 核实宽带类"""
        has_broadband = product_matcher.has_broadband(user_input)
        
        if has_broadband:
            state.has_broadband = True
            state.scenario = ScenarioType.A
            return self._generate_installment_query(state), NodeType.N
        
        # 继续到家电
        return self._generate_appliance_query(state), NodeType.O
    
    def _handle_node_n(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点N: 核实分期"""
        state.in_installment_query = True
        intent, _, _ = semantic_analyzer.analyze(user_input, "installment_query")
        
        # 特殊规则：折现/什么都没收到 → 强制J节点
        if state.is_cash_conversion or state.is_nothing_received:
            return "", NodeType.J
        
        # 明确知道
        if intent == IntentType.AFFIRMATIVE:
            return "", NodeType.H
        
        # 不知道/模糊 → I节点
        return "", NodeType.I
    
    def _handle_node_o(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点O: 核实家电类"""
        has_appliance = product_matcher.has_appliance(user_input)
        
        if has_appliance:
            state.has_appliance = True
            state.scenario = ScenarioType.A
            return self._generate_installment_query(state), NodeType.N
        
        # 继续到折现
        return self._generate_cash_query(state), NodeType.P
    
    def _handle_node_p(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点P: 核实折现"""
        has_cash = "折现" in user_input or "现金" in user_input
        
        if has_cash:
            state.has_cash = True
            state.is_cash_conversion = True
            state.scenario = ScenarioType.B
            return self._generate_installment_query(state), NodeType.N
        
        # 继续到拍照
        return self._generate_camera_query(state), NodeType.Q
    
    def _handle_node_q(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点Q: 核实拍照类"""
        # 检查是否收到
        if semantic_analyzer.is_affirmative(user_input):
            state.has_camera_item = True
            state.scenario = ScenarioType.A
            return self._generate_installment_query(state), NodeType.N
        
        if semantic_analyzer.is_negative(user_input):
            state.is_nothing_received = True
            state.scenario = ScenarioType.B
            return self._generate_installment_query(state), NodeType.N
        
        # 中性 → 继续到分期
        return self._generate_installment_query(state), NodeType.N
    
    def _handle_node_e(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点E: 礼貌拒绝"""
        count = state.increment_refusal()
        
        if count >= 2:
            return self._generate_refusal_ending(state), NodeType.END
        
        # 挽留
        return self._generate_retention_response(), NodeType.E
    
    def _handle_node_f(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点F: 忙碌处理"""
        count = state.increment_busy()
        
        if count >= 2:
            return self._generate_busy_ending(), NodeType.END
        
        # 挽留
        return self._generate_busy_retention(), NodeType.F
    
    def _handle_node_g(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点G: 投诉处理"""
        return self._generate_complaint_response(state), NodeType.G
    
    def _handle_node_h(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点H: 礼貌挂机"""
        return self._generate_polite_ending(state), NodeType.END
    
    def _handle_node_i(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点I: 分期解释挂机"""
        return self._generate_installment_explain_ending(state), NodeType.END
    
    def _handle_node_j(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点J: 登记挂机"""
        return self._generate_register_ending(), NodeType.END
    
    def _handle_node_t(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点T: 不认识本人结束"""
        return "好的，那不好意思打扰您了，祝您生活愉快，再见！", NodeType.END
    
    def _handle_node_u(self, state: DialogState, user_input: str, meta: Dict) -> Tuple[str, NodeType]:
        """节点U: 认识本人结束"""
        return self._generate_transfer_message(state), NodeType.END
    
    # ============ 话术生成器 ============
    
    def _generate_ask_if_know_response(self, state: DialogState) -> str:
        return "请问您认识{}吗？".format(state.customer.name)
    
    def _generate_permission_request(self, state: DialogState) -> str:
        return "您在{}办理了一个电信套餐，耽误您一分钟时间跟您做个回访可以吗？".format(
            state.customer.formal_date
        )
    
    def _generate_transfer_message(self, state: DialogState) -> str:
        return (
            "麻烦您转告下{}，他{}在电信办了套餐业务，请提醒他每月初务必记得缴纳话费，"
            "电信号码用满{}，避免欠费影响他的正常使用，顺便可以提醒他，他办单后有话费抵用券等免费福利可领取，"
            "具体他可登陆翼支付APP，进入橙分期的福利中心查看，千万不要错过！感谢您的接听，再见！".format(
                state.customer.name,
                state.customer.formal_date,
                state.customer.format_loan_months()
            )
        )
    
    def _generate_not_know_ending(self) -> str:
        return "好的，那不好意思打扰您了，祝您生活愉快，再见！"
    
    def _generate_refusal_response(self, state: DialogState) -> str:
        return "我明白您可能不感兴趣，不过这个确认很快，能和我简单说说吗"
    
    def _generate_refusal_ending(self, state: DialogState) -> str:
        return "好的，您办理的电信套餐业务已经生效，请您保持接听号码用满{}，避免您办理的橙分期逾期。那就不打扰您了，再见。".format(
            state.customer.format_loan_months()
        )
    
    def _generate_busy_response(self, state: DialogState) -> str:
        return "我理解您现在忙，不过这个确认很快的，能占用您一分钟吗？"
    
    def _generate_busy_first_response(self) -> str:
        return "喂？您能听到吗？"
    
    def _generate_busy_retention(self) -> str:
        return "我理解您现在忙，不过这个确认很快的，能占用您一分钟吗？"
    
    def _generate_busy_ending(self) -> str:
        return "好的，那我就不打扰您了，祝您一切顺利，再见。"
    
    def _generate_complaint_listen(self) -> str:
        return "好的，您说一下，看是否在我处理范围内呢？"
    
    def _generate_complaint_response(self, state: DialogState) -> str:
        return "很抱歉给您带来不好的体验，您可以拨打客服热线一万号咨询。"
    
    def _generate_contract_query(self, state: DialogState) -> str:
        return "您这次办理的套餐业务需要正常使用{}，中间不能停机、离网，您这边清楚么？".format(
            state.customer.format_loan_months()
        )
    
    def _generate_phone_query(self, state: DialogState) -> str:
        return "那跟您核实一下，您这次办理业务拿到什么商品了吗？比如手机或其他优惠？"
    
    def _generate_broadband_query(self, state: DialogState) -> str:
        return "那这次的套餐有没有包含宽带设备、光猫，路由器，机顶盒，千兆光纤呢？"
    
    def _generate_appliance_query(self, state: DialogState) -> str:
        return "每个客户都不一样的，那有没有比如家用电器、小度、智能门锁、摄像头、手表手环呢？"
    
    def _generate_cash_query(self, state: DialogState) -> str:
        return "那没有给您商品，有没有把商品折成现金给您？"
    
    def _generate_camera_query(self, state: DialogState) -> str:
        return "那您当时拿在手里拍照的东西给您了吗？"
    
    def _generate_installment_query(self, state: DialogState) -> str:
        if state.scenario == ScenarioType.A:
            return "您拿到的商品是在我们这边办的橙分期业务，请问这个您知道吗？"
        else:
            return "您当时成功办理了橙分期业务的，请问这个您知道吗？"
    
    def _generate_polite_ending(self, state: DialogState) -> str:
        return (
            "好的，提醒一下，您已经成功办理了橙分期业务，请保持电信合约号码用满{}，"
            "避免影响您电信号码正常使用。另外我们业务是仅面向非学生客户办理的，"
            "如果您有疑问，可以咨询客服电话95106，感谢您的接听，再见！".format(
                state.customer.format_loan_months()
            )
        )
    
    def _generate_installment_explain_ending(self, state: DialogState) -> str:
        return (
            "好的，跟您解释下，橙分期是翼支付提供给客户的商品分期服务。"
            "您获取的商品或享受的优惠就是办理的橙分期，需要您电信号码正常使用，"
            "月初缴纳话费，电信会返还红包帮您还分期，不需要您额外还分期款。"
            "请保持电信合约号码用满{}，避免影响您电信号码正常使用。"
            "另外我们业务是仅面向非学生客户办理的，如果您有疑问，可以咨询客服电话95106，感谢您的接听，再见".format(
                state.customer.format_loan_months()
            )
        )
    
    def _generate_register_ending(self) -> str:
        return "您说的这个情况我这边记录反馈，为了保护您的个人权益，预计在一个工作日内会有专业人员再次给您致电，请您保持电话畅通注意接听。"
    
    def _generate_retention_response(self) -> str:
        return "我明白您可能不感兴趣，不过这个确认很快，能和我简单说说吗？"


# 创建Agent实例的工厂函数
def create_agent(customer_name: str, formal_date: str, loan_months: int) -> AgentEngine:
    """创建Agent实例"""
    customer = CustomerInfo(
        name=customer_name,
        formal_date=formal_date,
        loan_months=loan_months
    )
    return AgentEngine(customer)
