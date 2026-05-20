"""
节点定义与注册
"""
from typing import Dict, Type, Callable, Optional
from dataclasses import dataclass


@dataclass
class NodeDefinition:
    """节点定义"""
    name: str
    node_id: str
    description: str
    next_nodes: Dict[str, str]  # 条件 -> 下一节点
    is_ending: bool = False
    handler: Optional[Callable] = None


class NodeRegistry:
    """节点注册表"""
    
    _nodes: Dict[str, NodeDefinition] = {}
    _handlers: Dict[str, Callable] = {}
    
    @classmethod
    def register(cls, node_id: str, name: str, description: str = "", 
                 next_nodes: Optional[Dict[str, str]] = None,
                 is_ending: bool = False):
        """注册节点"""
        def decorator(func: Callable):
            cls._nodes[node_id] = NodeDefinition(
                name=name,
                node_id=node_id,
                description=description,
                next_nodes=next_nodes or {},
                is_ending=is_ending,
                handler=func
            )
            cls._handlers[node_id] = func
            return func
        return decorator
    
    @classmethod
    def get_handler(cls, node_id: str) -> Optional[Callable]:
        """获取节点处理器"""
        return cls._handlers.get(node_id)
    
    @classmethod
    def get_definition(cls, node_id: str) -> Optional[NodeDefinition]:
        """获取节点定义"""
        return cls._nodes.get(node_id)
    
    @classmethod
    def get_all_nodes(cls) -> Dict[str, NodeDefinition]:
        """获取所有节点"""
        return cls._nodes.copy()
    
    @classmethod
    def get_next_nodes(cls, node_id: str) -> Dict[str, str]:
        """获取下一节点映射"""
        node = cls._nodes.get(node_id)
        return node.next_nodes if node else {}


# 节点ID常量
class NodeIds:
    """节点ID常量"""
    A = "A"           # 确认本人
    B = "B"           # 非本人处理
    C = "C"           # 全局规则
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
    END = "END"       # 流程结束
