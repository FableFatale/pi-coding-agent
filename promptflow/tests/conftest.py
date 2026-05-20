"""
Pytest 配置和共享 fixtures
"""
import pytest
import sys

# 确保 src 目录在路径中
sys.path.insert(0, 'src')


@pytest.fixture(scope="session")
def project_root():
    """项目根目录"""
    import os
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def src_path(project_root):
    """源代码目录"""
    import os
    return os.path.join(project_root, 'src')


@pytest.fixture
def sample_node_definitions():
    """示例节点定义"""
    from promptflow.parser import NodeDefinition
    return {
        'A': NodeDefinition(id='A', name='开始', prompt='开始节点'),
        'B': NodeDefinition(id='B', name='中间', prompt='中间节点'),
        'C': NodeDefinition(id='C', name='结束', prompt='结束节点', is_ending=True),
    }


@pytest.fixture
def sample_flow_edges():
    """示例流程边"""
    from promptflow.flow_builder import FlowEdge
    return [
        FlowEdge(source='A', target='B'),
        FlowEdge(source='B', target='C'),
    ]


@pytest.fixture
def simple_prompt_text():
    """简单的 Prompt 文本"""
    return """
# 角色
简单客服

## 总目标
回答问题

# 节点 A
欢迎

# 节点 B
处理

# 节点 C
结束
结束节点
"""


@pytest.fixture
def complex_prompt_text():
    """复杂的 Prompt 文本"""
    return """
# 角色
智能客服

## 总目标
处理客户问题

# 节点 A
欢迎
您好，请问有什么可以帮您？

> 用户：我想咨询
> 客服：好的，请说

节点prompt：简单问候

# 节点 B
确认问题
请问具体是什么问题？

节点prompt：确认问题

# 节点 C
问题解答
我来帮您解答。

节点prompt：提供解答

# 节点 D
问题解决
还有其他问题吗？

节点prompt：确认问题解决
结束节点

# 节点 E
转人工
正在转接人工客服。

节点prompt：转接人工
结束节点

## 全流程通用全局执行规则
1. 保持友好态度
2. 及时响应
3. 复杂问题转人工

## 语义规则
- 如果用户多次询问，给予更详细的解释
- 如果用户表达不满，增加道歉

### 正面词库
好的, 谢谢, 满意, 可以, 没问题

### 负面词库
投诉, 不满, 差评, 退货, 退款
"""
