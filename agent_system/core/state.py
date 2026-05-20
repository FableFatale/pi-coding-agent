"""
对话状态管理
维护对话过程中的所有状态信息
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class NodeType(Enum):
    """节点类型"""
    A = "A"           # 确认本人
    B = "B"           # 非本人处理
    D = "D"           # 获取回访许可
    E = "E"           # 礼貌拒绝
    F = "F"           # 忙碌处理
    G = "G"           # 投诉处理
    H = "H"           # 礼貌挂机
    I = "I"           # 分期解释挂机
    J = "J"           # 登记挂机
    K = "K"           # 核实合约期
    L = "L"           # 核实手机类
    M = "M"           # 核实宽带类
    N = "N"           # 核实分期
    O = "O"           # 核实家电类
    P = "P"           # 核实折现
    Q = "Q"           # 核实拍照类
    T = "T"           # 不认识本人结束
    U = "U"           # 认识本人结束
    C = "C"           # 全局规则
    END = "END"       # 流程结束


class ScenarioType(Enum):
    """分期核实场景类型"""
    A = "A"  # 拿到了商品/服务
    B = "B"  # 仅折现或什么都没收到


@dataclass
class CustomerInfo:
    """客户信息"""
    name: str = ""                    # 姓名
    formal_date: str = ""             # 正式日期（含年）
    loan_months: int = 0              # 贷款期限（月）
    
    def format_loan_months(self) -> str:
        """将数字转为中文拼音"""
        chinese_nums = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 
                       6: "六", 7: "七", 8: "八", 9: "九", 10: "十",
                       11: "十一", 12: "十二"}
        if self.loan_months in chinese_nums:
            return f"{chinese_nums[self.loan_months]}个月"
        return f"{self.loan_months}个月"


@dataclass
class DialogRecord:
    """对话记录"""
    node: str
    user_input: str
    agent_response: str
    timestamp: float = 0


@dataclass
class DialogState:
    """对话状态"""
    # 当前节点
    current_node: NodeType = NodeType.A
    
    # 客户信息
    customer: CustomerInfo = field(default_factory=CustomerInfo)
    
    # 对话历史
    history: List[DialogRecord] = field(default_factory=list)
    
    # 流程状态
    is_first_turn: bool = True           # 是否第一轮
    refusal_count: int = 0              # 拒绝次数累计
    busy_count: int = 0                 # 忙碌次数累计
    
    # 场景判定
    scenario: Optional[ScenarioType] = None  # 分期核实场景
    
    # 商品确认状态
    received_items: List[str] = field(default_factory=list)  # 收到的商品
    has_phone: bool = False             # 是否有手机类
    has_broadband: bool = False         # 是否有宽带类
    has_appliance: bool = False         # 是否有家电类
    has_cash: bool = False              # 是否有折现
    has_camera_item: bool = False       # 是否有拍照类
    
    # 标签
    tags: List[str] = field(default_factory=list)
    
    # 特殊标记
    is_cash_conversion: bool = False     # 是否为商品折现
    is_nothing_received: bool = False   # 是否什么都没收到
    in_installment_query: bool = False   # 是否在核实分期环节
    asking_about_installment: bool = False  # 用户是否在询问橙分期
    
    # 流程控制
    last_node: Optional[NodeType] = None  # 上一个节点
    pending_return_node: Optional[NodeType] = None  # 待返回的节点（询问橙分期后）
    
    def add_record(self, node: str, user_input: str, agent_response: str):
        """添加对话记录"""
        self.history.append(DialogRecord(
            node=node,
            user_input=user_input,
            agent_response=agent_response
        ))
    
    def increment_refusal(self) -> int:
        """增加拒绝计数，返回当前计数"""
        self.refusal_count += 1
        return self.refusal_count
    
    def increment_busy(self) -> int:
        """增加忙碌计数，返回当前计数"""
        self.busy_count += 1
        return self.busy_count
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "current_node": self.current_node.value,
            "customer": {
                "name": self.customer.name,
                "formal_date": self.customer.formal_date,
                "loan_months": self.customer.loan_months,
                "loan_months_cn": self.customer.format_loan_months()
            },
            "history_count": len(self.history),
            "refusal_count": self.refusal_count,
            "busy_count": self.busy_count,
            "scenario": self.scenario.value if self.scenario else None,
            "received_items": self.received_items,
            "has_phone": self.has_phone,
            "has_broadband": self.has_broadband,
            "has_appliance": self.has_appliance,
            "has_cash": self.has_cash,
            "has_camera_item": self.has_camera_item,
            "is_cash_conversion": self.is_cash_conversion,
            "is_nothing_received": self.is_nothing_received,
            "tags": self.tags
        }
