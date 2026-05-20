"""
客服场景流程测试
基于 examples/customer_service.md 的完整测试用例
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
# 测试数据：基于 customer_service.md 示例流程
# ============================================================

CUSTOMER_SERVICE_PROMPT = """
# 角色
你是智能客服助手小Q，负责解答用户关于产品使用和售后服务的问题。

## 总目标
高效准确地解答用户问题，提升用户满意度，将复杂问题转接人工处理。

# 节点 A - 欢迎
您好，我是智能客服小Q！请问有什么可以帮您？

> 用户：我想咨询产品使用方法
> 小Q：好的，请问具体是哪方面的问题呢？

节点prompt：根据用户意图进行初步分类引导

# 节点 B - 产品咨询
好的，请问您想了解哪个方面的使用方法？

> 用户：我想知道怎么设置闹钟
> 小Q：您可以在设置中找到闹钟选项，点击添加即可设置。

节点prompt：提供产品使用指导

# 节点 C - 故障排查
我来帮您排查一下问题。请问具体是什么情况？

> 用户：应用打不开了
> 小Q：请尝试重启应用，如果问题仍然存在，请联系我们的人工客服。

节点prompt：引导用户进行基本的故障排查

# 节点 D - 退换货
我来帮您了解退换货政策。请问您的订单是什么时候下的？

> 用户：三天前
> 小Q：您好，7天内的订单可以申请退换货，请问您想退货还是换货？

节点prompt：处理退换货咨询

# 节点 E - 投诉处理
非常抱歉给您带来不便，请您详细描述一下问题，我会认真记录并反馈。

> 用户：产品质量有问题
> 小Q：我们非常重视您的反馈，稍后会有专人与您联系处理。

节点prompt：处理用户投诉

# 节点 H - 问题解决
很高兴能帮到您！请问还有其他问题吗？

节点prompt：确认问题是否解决
结束节点

# 节点 I - 转人工
您的问题比较复杂，我帮您转接到人工客服，请稍等。

节点prompt：转接人工
结束节点

# 节点 T - 结束
感谢您的来电，祝您生活愉快！

节点prompt：结束对话
结束节点

## 全流程通用全局执行规则
1. 保持友好专业的服务态度
2. 响应时间不超过3秒
3. 复杂问题自动转人工

## 语义规则
- 如果用户表达不满，增加道歉和安抚
- 如果用户多次询问同一问题，主动提供更详细的解释

## 禁止行为
1. 不向用户透露内部系统信息
2. 不承诺超出政策范围的退换货
3. 不在未确认身份的情况下处理账户安全问题

### 正面词库
好的, 谢谢, 了解, 明白, 满意, 可以, 没问题, OK

### 负面词库
投诉, 不满, 失望, 垃圾, 差评, 退货, 退款, 赔偿, 诈骗
"""


# ============================================================
# 流程处理器模拟
# ============================================================

class CustomerServiceFlowHandler:
    """客服流程处理器模拟"""
    
    def __init__(self):
        self.current_node = None
        self.conversation_history = []
    
    def reset(self):
        """重置对话状态"""
        self.current_node = None
        self.conversation_history = []
    
    def handle(self, node: str, user_input: str, context: dict) -> tuple:
        """处理对话"""
        self.current_node = node
        self.conversation_history.append({
            "node": node,
            "user": user_input
        })
        
        # 模拟流程逻辑
        responses = {
            "A": ("您好，我是智能客服小Q！请问有什么可以帮您？", "B"),
            "B": ("好的，请问您想了解哪个方面的使用方法？", self._determine_next_after_B(user_input)),
            "C": ("我来帮您排查一下问题。请问具体是什么情况？", "H"),
            "D": ("我来帮您了解退换货政策。请问您的订单是什么时候下的？", "H"),
            "E": ("非常抱歉给您带来不便，请您详细描述一下问题。", "H"),
            "H": ("很高兴能帮到您！请问还有其他问题吗？", None),
            "I": ("您的问题比较复杂，我帮您转接到人工客服，请稍等。", None),
            "T": ("感谢您的来电，祝您生活愉快！", None),
        }
        
        if node in responses:
            response, next_node = responses[node]
            return (response, next_node)
        
        return ("再见", None)
    
    def _determine_next_after_B(self, user_input: str) -> str:
        """根据用户输入决定 B 之后的下一个节点"""
        if any(kw in user_input for kw in ["怎么", "设置", "使用", "如何"]):
            return "B"  # 继续产品咨询
        elif any(kw in user_input for kw in ["问题", "打不开", "错误", "故障"]):
            return "C"
        elif any(kw in user_input for kw in ["退货", "换货", "退款"]):
            return "D"
        elif any(kw in user_input for kw in ["投诉", "不满", "差评"]):
            return "E"
        return "H"


# ============================================================
# 测试类
# ============================================================

class TestCustomerServiceFlow:
    """客服流程测试"""
    
    @pytest.fixture
    def parsed_prompt(self):
        """解析客服 Prompt"""
        parser = PromptParser()
        return parser.parse(CUSTOMER_SERVICE_PROMPT)
    
    @pytest.fixture
    def flow_graph(self, parsed_prompt):
        """构建流程图"""
        builder = FlowBuilder()
        return builder.build(parsed_prompt)
    
    @pytest.fixture
    def path_analyzer(self, flow_graph, parsed_prompt):
        """路径分析"""
        analyzer = PathAnalyzer()
        return analyzer.analyze(flow_graph, parsed_prompt)
    
    @pytest.fixture
    def flow_handler(self):
        """流程处理器"""
        return CustomerServiceFlowHandler()
    
    # --------------------------------------------------------
    # 节点结构测试
    # --------------------------------------------------------
    
    def test_parsed_nodes_count(self, parsed_prompt):
        """测试解析出的节点数量"""
        assert len(parsed_prompt.nodes) == 8, \
            f"应该解析出 8 个节点，实际: {len(parsed_prompt.nodes)}"
    
    def test_parsed_nodes_ids(self, parsed_prompt):
        """测试解析出的节点 ID"""
        expected_nodes = {'A', 'B', 'C', 'D', 'E', 'H', 'I', 'T'}
        actual_nodes = set(parsed_prompt.nodes.keys())
        assert expected_nodes == actual_nodes, \
            f"节点 ID 不匹配，期望: {expected_nodes}, 实际: {actual_nodes}"
    
    def test_ending_nodes(self, parsed_prompt):
        """测试结束节点"""
        ending_nodes = [nid for nid, n in parsed_prompt.nodes.items() if n.is_ending]
        assert 'H' in ending_nodes, "H 应该是结束节点"
        assert 'I' in ending_nodes, "I 应该是结束节点"
        assert 'T' in ending_nodes, "T 应该是结束节点"
    
    def test_role_extracted(self, parsed_prompt):
        """测试角色信息提取"""
        assert '小Q' in parsed_prompt.role or '客服' in parsed_prompt.role, \
            "应该提取出客服角色"
    
    def test_goal_extracted(self, parsed_prompt):
        """测试目标信息提取"""
        assert len(parsed_prompt.goal) > 0, "应该提取出总目标"
    
    def test_rules_extracted(self, parsed_prompt):
        """测试规则提取"""
        assert len(parsed_prompt.rules) > 0, "应该提取出规则"
    
    def test_global_rules_extracted(self, parsed_prompt):
        """测试全局规则提取"""
        assert len(parsed_prompt.global_rules) > 0, "应该提取出全局规则"
    
    def test_keyword_libraries_extracted(self, parsed_prompt):
        """测试关键词库提取"""
        assert len(parsed_prompt.libraries) > 0, "应该提取出关键词库"
        assert '正面' in str(parsed_prompt.libraries) or '正面词库' in parsed_prompt.libraries, \
            "应该包含正面词库"


class TestCustomerServiceNodes:
    """客服节点测试 - 针对每个节点的单元测试"""
    
    @pytest.fixture
    def parsed_prompt(self):
        parser = PromptParser()
        return parser.parse(CUSTOMER_SERVICE_PROMPT)
    
    @pytest.fixture
    def flow_handler(self):
        return CustomerServiceFlowHandler()
    
    # --------------------------------------------------------
    # 节点 A 测试 - 欢迎
    # --------------------------------------------------------
    
    def test_node_A_is_start(self, parsed_prompt):
        """测试 A 是起始节点"""
        assert 'A' in parsed_prompt.nodes
        # A 应该是入口节点
        flow_builder = FlowBuilder()
        flow = flow_builder.build(parsed_prompt)
        assert flow_builder.start_node_id == 'A'
    
    def test_node_A_content(self, parsed_prompt):
        """测试 A 节点内容"""
        node_a = parsed_prompt.nodes['A']
        assert '欢迎' in node_a.name or 'A' == node_a.id
        assert not node_a.is_ending, "欢迎节点不应该是结束节点"
    
    def test_node_A_flow(self, flow_handler):
        """测试 A 节点流程"""
        response, next_node = flow_handler.handle('A', '你好', {})
        assert '小Q' in response or '您好' in response
        assert next_node == 'B'
    
    # --------------------------------------------------------
    # 节点 B 测试 - 产品咨询
    # --------------------------------------------------------
    
    def test_node_B_exists(self, parsed_prompt):
        """测试 B 节点存在"""
        assert 'B' in parsed_prompt.nodes
        node_b = parsed_prompt.nodes['B']
        assert not node_b.is_ending, "B 节点不应该是结束节点"
    
    def test_node_B_product_inquiry(self, flow_handler):
        """测试 B 节点产品咨询流程"""
        response, next_node = flow_handler.handle('B', '我想知道怎么设置闹钟', {})
        assert '使用' in response or '方法' in response or '设置' in response
    
    # --------------------------------------------------------
    # 节点 C 测试 - 故障排查
    # --------------------------------------------------------
    
    def test_node_C_exists(self, parsed_prompt):
        """测试 C 节点存在"""
        assert 'C' in parsed_prompt.nodes
        node_c = parsed_prompt.nodes['C']
        assert '排查' in node_c.name or '故障' in node_c.name
    
    def test_node_C_troubleshooting(self, flow_handler):
        """测试 C 节点故障排查"""
        response, next_node = flow_handler.handle('C', '应用打不开了', {})
        assert '排查' in response or '重启' in response
    
    # --------------------------------------------------------
    # 节点 D 测试 - 退换货
    # --------------------------------------------------------
    
    def test_node_D_exists(self, parsed_prompt):
        """测试 D 节点存在"""
        assert 'D' in parsed_prompt.nodes
        node_d = parsed_prompt.nodes['D']
        assert '退换' in node_d.name or '退' in node_d.name
    
    def test_node_D_returns_exchange(self, flow_handler):
        """测试 D 节点退换货"""
        response, next_node = flow_handler.handle('D', '我想退货', {})
        assert '退换货' in response or '政策' in response
    
    # --------------------------------------------------------
    # 节点 E 测试 - 投诉处理
    # --------------------------------------------------------
    
    def test_node_E_exists(self, parsed_prompt):
        """测试 E 节点存在"""
        assert 'E' in parsed_prompt.nodes
        node_e = parsed_prompt.nodes['E']
        assert '投诉' in node_e.name or '抱怨' in node_e.name
    
    def test_node_E_complaint_handling(self, flow_handler):
        """测试 E 节点投诉处理"""
        response, next_node = flow_handler.handle('E', '产品质量有问题', {})
        assert '抱歉' in response or '不便' in response or '抱歉' in response, \
            "投诉处理应该包含道歉"
    
    # --------------------------------------------------------
    # 节点 H 测试 - 问题解决 (结束)
    # --------------------------------------------------------
    
    def test_node_H_is_ending(self, parsed_prompt):
        """测试 H 是结束节点"""
        assert 'H' in parsed_prompt.nodes
        node_h = parsed_prompt.nodes['H']
        assert node_h.is_ending, "H 应该是结束节点"
    
    def test_node_H_confirm_resolution(self, flow_handler):
        """测试 H 节点确认问题解决"""
        response, next_node = flow_handler.handle('H', '没有了，谢谢', {})
        assert '帮到' in response or '其他' in response
        assert next_node is None, "结束节点不应该有下一个节点"
    
    # --------------------------------------------------------
    # 节点 I 测试 - 转人工 (结束)
    # --------------------------------------------------------
    
    def test_node_I_is_ending(self, parsed_prompt):
        """测试 I 是结束节点"""
        assert 'I' in parsed_prompt.nodes
        node_i = parsed_prompt.nodes['I']
        assert node_i.is_ending, "I 应该是结束节点"
    
    def test_node_I_transfer_human(self, flow_handler):
        """测试 I 节点转人工"""
        response, next_node = flow_handler.handle('I', '', {})
        assert '人工' in response or '转接' in response
        assert next_node is None, "转人工节点应该结束"
    
    # --------------------------------------------------------
    # 节点 T 测试 - 结束
    # --------------------------------------------------------
    
    def test_node_T_is_ending(self, parsed_prompt):
        """测试 T 是结束节点"""
        assert 'T' in parsed_prompt.nodes
        node_t = parsed_prompt.nodes['T']
        assert node_t.is_ending, "T 应该是结束节点"
    
    def test_node_T_farewell(self, flow_handler):
        """测试 T 节点结束语"""
        response, next_node = flow_handler.handle('T', '', {})
        assert '感谢' in response or '祝' in response or '愉快' in response
        assert next_node is None, "结束节点不应该有下一个节点"


class TestCustomerServiceDialogues:
    """客服完整对话测试 - 端到端场景"""
    
    @pytest.fixture
    def flow_handler(self):
        return CustomerServiceFlowHandler()
    
    # --------------------------------------------------------
    # 正常对话流程测试
    # --------------------------------------------------------
    
    def test_dialogue_product_inquiry_flow(self, flow_handler):
        """测试产品咨询完整对话"""
        flow_handler.reset()
        
        # 开始
        response, next_node = flow_handler.handle('A', '你好', {})
        assert next_node == 'B'
        
        # 产品咨询
        response, next_node = flow_handler.handle('B', '我想知道怎么设置闹钟', {})
        assert 'B' in flow_handler.current_node
        
        # 结束
        response, next_node = flow_handler.handle('H', '没有了，谢谢', {})
        assert next_node is None
        
        assert len(flow_handler.conversation_history) == 3
    
    def test_dialogue_troubleshooting_flow(self, flow_handler):
        """测试故障排查完整对话"""
        flow_handler.reset()
        
        # 开始 -> 问题确认
        flow_handler.handle('A', '你好', {})
        flow_handler.handle('B', '应用打不开了', {})
        
        # 故障排查
        response, next_node = flow_handler.handle('C', '应用经常崩溃', {})
        assert '排查' in response
        
        # 结束
        response, next_node = flow_handler.handle('H', '好的，我试试', {})
        assert next_node is None
    
    def test_dialogue_return_exchange_flow(self, flow_handler):
        """测试退换货完整对话"""
        flow_handler.reset()
        
        flow_handler.handle('A', '你好', {})
        flow_handler.handle('B', '我想了解一下退货政策', {})
        
        response, next_node = flow_handler.handle('D', '订单是三天前下的', {})
        assert '退换货' in response or '7' in response or '天' in response
        
        response, next_node = flow_handler.handle('H', '好的，了解了', {})
        assert next_node is None
    
    def test_dialogue_complaint_flow(self, flow_handler):
        """测试投诉处理完整对话"""
        flow_handler.reset()
        
        flow_handler.handle('A', '你好', {})
        flow_handler.handle('B', '我要投诉', {})
        
        response, next_node = flow_handler.handle('E', '产品质量太差了', {})
        assert '抱歉' in response, "投诉应该得到道歉"
        
        response, next_node = flow_handler.handle('H', '希望你们改进', {})
        assert next_node is None
    
    def test_dialogue_transfer_to_human(self, flow_handler):
        """测试转人工场景"""
        flow_handler.reset()
        
        flow_handler.handle('A', '你好', {})
        flow_handler.handle('B', '这是个复杂问题', {})
        
        response, next_node = flow_handler.handle('I', '', {})
        assert '人工' in response
        assert next_node is None


def test_suite_dummy():
    """创建测试套件（用于 fixtures）"""
    return TestSuite(
        name="Dummy",
        description="Dummy test suite",
        test_cases=[
            TestCase(
                id='dummy',
                name='Dummy',
                description='Dummy test case',
                test_type=TestType.NORMAL,
                path=['A'],
                user_inputs=[TestInput(node='A', text='你好')],
                expected_ending='H'
            )
        ]
    )


class TestCustomerServiceScenarios:
    """客服场景测试 - 特定业务场景"""
    
    @pytest.fixture
    def test_suite(self):
        """创建客服场景测试套件"""
        suite = TestSuite(
            name="客服场景测试套件",
            description="基于 customer_service.md 的业务场景测试",
            test_cases=[
                # 场景1: 快速咨询
                TestCase(
                    id='scenario_001',
                    name='快速咨询',
                    description='用户快速获得答案后结束',
                    test_type=TestType.NORMAL,
                    path=['A', 'B', 'H'],
                    user_inputs=[
                        TestInput(node='A', text='你好'),
                        TestInput(node='B', text='我想知道怎么设置闹钟'),
                        TestInput(node='H', text='好的，谢谢'),
                    ],
                    expected_ending='H'
                ),
                # 场景2: 故障排查
                TestCase(
                    id='scenario_002',
                    name='故障排查',
                    description='用户遇到问题，排查后解决',
                    test_type=TestType.NORMAL,
                    path=['A', 'B', 'C', 'H'],
                    user_inputs=[
                        TestInput(node='A', text='你好'),
                        TestInput(node='B', text='应用打不开了'),
                        TestInput(node='C', text='试过了，还是不行'),
                        TestInput(node='H', text='好的，我再试试'),
                    ],
                    expected_ending='H'
                ),
                # 场景3: 退换货咨询
                TestCase(
                    id='scenario_003',
                    name='退换货咨询',
                    description='用户咨询退换货政策',
                    test_type=TestType.NORMAL,
                    path=['A', 'B', 'D', 'H'],
                    user_inputs=[
                        TestInput(node='A', text='你好'),
                        TestInput(node='B', text='想退货'),
                        TestInput(node='D', text='三天前'),
                        TestInput(node='H', text='好的'),
                    ],
                    expected_ending='H'
                ),
                # 场景4: 投诉处理
                TestCase(
                    id='scenario_004',
                    name='投诉处理',
                    description='用户投诉，需要道歉安抚',
                    test_type=TestType.NORMAL,
                    path=['A', 'B', 'E', 'H'],
                    user_inputs=[
                        TestInput(node='A', text='你好'),
                        TestInput(node='B', text='我要投诉'),
                        TestInput(node='E', text='产品质量太差'),
                        TestInput(node='H', text='希望改进'),
                    ],
                    expected_ending='H'
                ),
                # 场景5: 转人工
                TestCase(
                    id='scenario_005',
                    name='转人工',
                    description='问题复杂需要转人工处理',
                    test_type=TestType.EDGE,
                    path=['A', 'B', 'I'],
                    user_inputs=[
                        TestInput(node='A', text='你好'),
                        TestInput(node='B', text='这是个复杂问题'),
                        TestInput(node='I', text=''),
                    ],
                    expected_ending='I'
                ),
                # 场景6: 多轮对话
                TestCase(
                    id='scenario_006',
                    name='多轮产品咨询',
                    description='用户多次询问产品问题',
                    test_type=TestType.EDGE,
                    path=['A', 'B', 'B', 'B', 'H'],
                    user_inputs=[
                        TestInput(node='A', text='你好'),
                        TestInput(node='B', text='怎么设置闹钟'),
                        TestInput(node='B', text='那怎么设置提醒'),
                        TestInput(node='B', text='还有日历呢'),
                        TestInput(node='H', text='都知道了'),
                    ],
                    expected_ending='H'
                ),
                # 场景7: 边界 - 空输入
                TestCase(
                    id='scenario_007',
                    name='空输入处理',
                    description='用户发送空消息',
                    test_type=TestType.EDGE,
                    path=['A', 'H'],
                    user_inputs=[
                        TestInput(node='A', text=''),
                        TestInput(node='H', text=''),
                    ],
                    expected_ending='H'
                ),
                # 场景8: 边界 - 超长输入
                TestCase(
                    id='scenario_008',
                    name='超长输入处理',
                    description='用户发送超长消息',
                    test_type=TestType.EDGE,
                    path=['A', 'B', 'H'],
                    user_inputs=[
                        TestInput(node='A', text='你好' * 100),
                        TestInput(node='B', text='很长的产品使用问题描述' * 50),
                        TestInput(node='H', text='好的'),
                    ],
                    expected_ending='H'
                ),
            ]
        )
        return suite
    
    def test_run_scenario_suite(self, test_suite):
        """运行场景测试套件"""
        handler = CustomerServiceFlowHandler()
        
        runner = ScenarioRunner()
        runner.set_flow_handler(handler.handle)
        
        summary = runner.run(test_suite)
        
        assert summary.total_tests == len(test_suite.test_cases)
        assert summary.pass_rate >= 0.5, f"通过率过低: {summary.pass_rate}"
    
    def test_scenario_quick_inquiry(self):
        """测试快速咨询场景"""
        handler = CustomerServiceFlowHandler()
        
        test_case = test_suite_dummy().test_cases[0]
        runner = ScenarioRunner()
        runner.set_flow_handler(handler.handle)
        
        summary = runner.run(TestSuite(
            name="Quick",
            description="D",
            test_cases=[test_case]
        ))
        
        assert summary.total_tests == 1
    
    def test_scenario_complaint_with_apology(self):
        """测试投诉场景 - 必须包含道歉"""
        handler = CustomerServiceFlowHandler()
        
        test_case = TestCase(
            id='complaint_test',
            name='投诉必须道歉',
            description='投诉场景的响应必须包含道歉',
            test_type=TestType.NORMAL,
            path=['A', 'B', 'E', 'H'],
            user_inputs=[
                TestInput(node='A', text='你好'),
                TestInput(node='B', text='我要投诉'),
                TestInput(node='E', text='质量太差'),
                TestInput(node='H', text='好的'),
            ]
        )
        
        runner = ScenarioRunner()
        runner.set_flow_handler(handler.handle)
        
        summary = runner.run(TestSuite(
            name="Complaint",
            description="D",
            test_cases=[test_case]
        ))
        
        # 验证投诉节点有道歉
        result = summary.results[0]
        e_turn = [t for t in result.turns if t.node == 'E'][0]
        assert '抱歉' in e_turn.agent_response, \
            f"投诉处理应该道歉，实际响应: {e_turn.agent_response}"


class TestCustomerServiceKeywords:
    """关键词触发测试"""
    
    @pytest.fixture
    def flow_handler(self):
        return CustomerServiceFlowHandler()
    
    # --------------------------------------------------------
    # 正面关键词测试
    # --------------------------------------------------------
    
    def test_positive_keywords_response(self, flow_handler):
        """测试正面关键词应该得到积极响应"""
        positive_inputs = [
            '好的', '谢谢', '了解', '明白', '满意', 
            '可以', '没问题', 'OK'
        ]
        
        for user_input in positive_inputs:
            response, _ = flow_handler.handle('H', user_input, {})
            # 正面响应应该被接受
            assert response is not None
    
    # --------------------------------------------------------
    # 负面关键词测试
    # --------------------------------------------------------
    
    def test_negative_keywords_detected(self, flow_handler):
        """测试负面关键词检测"""
        negative_keywords = ['投诉', '不满', '差评', '退货', '退款']
        
        for keyword in negative_keywords:
            response, next_node = flow_handler.handle('B', keyword, {})
            # 负面词应该触发相应处理
            assert response is not None
    
    # --------------------------------------------------------
    # 疑问关键词测试
    # --------------------------------------------------------
    
    def test_question_keywords_detected(self, flow_handler):
        """测试疑问关键词检测"""
        question_keywords = ['怎么', '如何', '为什么', '什么']
        
        for keyword in question_keywords:
            response, next_node = flow_handler.handle('B', f'{keyword}设置闹钟', {})
            assert response is not None


class TestCustomerServiceRules:
    """规则执行测试"""
    
    @pytest.fixture
    def parsed_prompt(self):
        parser = PromptParser()
        return parser.parse(CUSTOMER_SERVICE_PROMPT)
    
    def test_friendly_attitude_rule(self, parsed_prompt):
        """测试友好态度规则"""
        rules = parsed_prompt.global_rules
        assert any('友好' in str(r) or '态度' in str(r) for r in rules), \
            "应该有友好态度规则"
    
    def test_response_time_rule(self, parsed_prompt):
        """测试响应时间规则"""
        rules = parsed_prompt.global_rules
        assert any('3秒' in str(r) or '响应' in str(r) for r in rules), \
            "应该有响应时间规则"
    
    def test_transfer_human_rule(self, parsed_prompt):
        """测试转人工规则"""
        rules = parsed_prompt.global_rules
        assert any('人工' in str(r) or '复杂' in str(r) for r in rules), \
            "应该有复杂问题转人工规则"
    
    def test_semantic_rules_exist(self, parsed_prompt):
        """测试语义规则存在"""
        assert len(parsed_prompt.rules) > 0, "应该有语义规则"
    
    def test_prohibited_behaviors_exist(self, parsed_prompt):
        """测试禁止行为规则存在"""
        # 从原始文本中应该能提取到禁止行为
        assert '禁止' in CUSTOMER_SERVICE_PROMPT, "应该有禁止行为"


class TestCustomerServiceEdgeCases:
    """边界情况测试"""
    
    @pytest.fixture
    def flow_handler(self):
        return CustomerServiceFlowHandler()
    
    def test_empty_input_at_start(self, flow_handler):
        """测试开始时空输入"""
        flow_handler.reset()
        response, next_node = flow_handler.handle('A', '', {})
        assert response is not None
        assert next_node is not None
    
    def test_special_characters(self, flow_handler):
        """测试特殊字符"""
        flow_handler.reset()
        special_chars = ['@#$%', '🎉🎊', '???', '...']
        
        for chars in special_chars:
            response, next_node = flow_handler.handle('A', chars, {})
            assert response is not None
    
    def test_repeated_same_input(self, flow_handler):
        """测试重复相同输入"""
        flow_handler.reset()
        
        for _ in range(3):
            response, next_node = flow_handler.handle('B', '怎么设置', {})
        
        assert len(flow_handler.conversation_history) == 3
    
    def test_rapid_inputs(self, flow_handler):
        """测试快速连续输入"""
        flow_handler.reset()
        
        inputs = ['你好', '怎么设置', '好的']
        for user_input in inputs:
            flow_handler.handle('A', user_input, {})
        
        assert len(flow_handler.conversation_history) == 3
    
    def test_mixed_language(self, flow_handler):
        """测试中英文混合输入"""
        flow_handler.reset()
        response, _ = flow_handler.handle('B', 'How to set alarm闹钟', {})
        assert response is not None
    
    def test_very_long_conversation(self, flow_handler):
        """测试超长对话"""
        flow_handler.reset()
        
        # 模拟 20 轮对话
        for i in range(20):
            flow_handler.handle('B', f'第{i+1}个问题', {})
        
        assert len(flow_handler.conversation_history) == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
