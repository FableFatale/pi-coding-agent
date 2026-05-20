"""
上下文构建器
根据当前状态和节点构建完整的prompt上下文
"""
from typing import Dict, List, Optional, Any
from .state import DialogState, CustomerInfo, NodeType, ScenarioType


class ContextBuilder:
    """上下文构建器"""
    
    # 禁用词汇
    FORBIDDEN_WORDS = [
        "了解", "好的", "明白", "知道了", "我刚刚已经说过啦", "我解释过啦",
        "多次解释了", "刚刚跟你说过了", "就像我刚刚说的", "我再跟你说",
        "刚刚给您解释过了", "要不您别问了", "手机号给我",
        "您这样一直纠结", "纠缠", "重复提问",
        "那可太棒了呢", "好的呢", "哈哈哈", "那太好了", "同意领取那就太好了",
        "太有用了", "太好啦"
    ]
    
    # 需要避免重复的承上启下词
    BRIDGE_WORDS = ["了解", "好的", "明白", "知道了", "好的好的", "好的"]
    
    def __init__(self):
        self._used_bridge_words: List[str] = []
    
    def reset(self):
        """重置上下文"""
        self._used_bridge_words = []
    
    def build_node_context(self, state: DialogState, node_id: str) -> str:
        """
        构建节点上下文
        """
        customer = state.customer
        
        # 基础角色设定
        base_prompt = f"""你是中国电信翼支付回访客服，负责通过与客户的对话来核实信息。
你的目标是通过流畅的对话方式收集信息。

【客户信息】
- 姓名: {customer.name}
- 办理日期: {customer.formal_date}
- 合约期: {customer.format_loan_months()}

【当前状态】
- 当前节点: {node_id}
- 对话轮次: {len(state.history) + 1}
"""
        
        # 添加已确认的信息
        confirmed_info = self._build_confirmed_info(state)
        if confirmed_info:
            base_prompt += f"\n【已确认信息】\n{confirmed_info}\n"
        
        # 添加流程状态
        if state.refusal_count > 0:
            base_prompt += f"- 累计拒绝次数: {state.refusal_count}\n"
        if state.busy_count > 0:
            base_prompt += f"- 累计忙碌次数: {state.busy_count}\n"
        
        # 添加场景判定
        if state.scenario:
            base_prompt += f"- 场景类型: {state.scenario.value}\n"
        
        return base_prompt
    
    def _build_confirmed_info(self, state: DialogState) -> str:
        """构建已确认信息"""
        info_parts = []
        
        if state.has_phone:
            info_parts.append("- 用户确认收到手机类商品")
        if state.has_broadband:
            info_parts.append("- 用户确认收到宽带设备")
        if state.has_appliance:
            info_parts.append("- 用户确认收到家电类商品")
        if state.has_cash:
            info_parts.append("- 用户确认收到折现")
        if state.has_camera_item:
            info_parts.append("- 用户确认收到拍照类商品")
        if state.is_cash_conversion:
            info_parts.append("- 确认为商品折现场景")
        if state.is_nothing_received:
            info_parts.append("- 确认为什么都没收到")
        
        return "\n".join(info_parts)
    
    def build_global_rules(self) -> str:
        """
        构建全局规则
        """
        return """
【全局规则 - 所有节点必须遵守】

1. 话术重复规则：
   - 用户要求重复时，仅重复上一句，不得新增内容
   - 用户无回复时，禁止连续追问

2. 禁止行为：
   - 禁止使用: 了解、好的、明白、知道了 等承上启下词
   - 禁止复述用户信息
   - 禁止诱导用户
   - 禁止承诺无法确定的处理结果

3. 流程闭环：
   - 用户在其他环节提问，回答后必须继续推进原有流程
   - 禁止直接挂机

4. 商品确认：
   - 用户表示"拿到"即视为已收到，不重复询问
   - 用户提到"优惠"也视为收到商品

5. 橙分期定义回复：
   - 非核实分期环节询问：标准定义回复
   - 核实分期环节询问：分期场景解释+反问
"""
    
    def build_node_prompt(self, state: DialogState, node_id: str, 
                          additional_rules: str = "") -> str:
        """
        构建完整的节点prompt
        """
        context = self.build_node_context(state, node_id)
        global_rules = self.build_global_rules()
        
        full_prompt = f"""
{context}

{global_rules}

{additional_rules}

请以自然、友好、专业的方式回复用户。
"""
        return full_prompt
    
    def select_bridge_word(self) -> str:
        """
        选择一个未使用过的承上启下词
        """
        available = [w for w in self.BRIDGE_WORDS if w not in self._used_bridge_words]
        if available:
            word = available[0]
            self._used_bridge_words.append(word)
            return word
        # 如果都用过了，返回空字符串
        return ""
    
    def check_forbidden_words(self, text: str) -> List[str]:
        """
        检查文本中是否包含禁用词
        """
        found = []
        for word in self.FORBIDDEN_WORDS:
            if word in text:
                found.append(word)
        return found


# 全局实例
context_builder = ContextBuilder()
