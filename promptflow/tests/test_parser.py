"""
测试 PromptParser - 解析器测试用例
"""
import pytest
import sys
sys.path.insert(0, 'src')

from promptflow.parser import PromptParser, ParsedPrompt, NodeDefinition


class TestPromptParser:
    """PromptParser 测试类"""
    
    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return PromptParser()
    
    @pytest.fixture
    def sample_prompt(self):
        """示例 Prompt 文本"""
        return """# 角色
你是智能客服助手。

## 总目标
解答用户问题。

# 节点 A
欢迎用户

> 用户：你好
> 客服：您好

节点prompt：简单问候

# 节点 B
处理咨询

节点prompt：处理用户咨询

# 节点 H - 结束
再见

结束节点
"""
    
    def test_parser_initialization(self, parser):
        """测试解析器初始化"""
        assert parser is not None
        assert hasattr(parser, '_patterns')
        assert 'node_header' in parser._patterns
    
    def test_parse_basic_structure(self, parser, sample_prompt):
        """测试基本结构解析"""
        result = parser.parse(sample_prompt)
        
        assert isinstance(result, ParsedPrompt)
        assert result.role == "智能客服助手"
        assert result.goal == "解答用户问题"
    
    def test_parse_nodes(self, parser, sample_prompt):
        """测试节点解析"""
        result = parser.parse(sample_prompt)
        
        assert len(result.nodes) >= 2
        assert 'A' in result.nodes
        assert 'B' in result.nodes
        assert 'H' in result.nodes
    
    def test_parse_ending_node(self, parser, sample_prompt):
        """测试结束节点识别"""
        result = parser.parse(sample_prompt)
        
        assert result.nodes['H'].is_ending == True
        assert result.nodes['A'].is_ending == False
    
    def test_parse_dialogue_examples(self, parser, sample_prompt):
        """测试对话示例提取"""
        result = parser.parse(sample_prompt)
        
        # A 节点应该有对话示例
        assert result.nodes['A'].example_dialogue is not None
        assert '你好' in result.nodes['A'].example_dialogue
    
    def test_parse_empty_prompt(self, parser):
        """测试空 Prompt"""
        result = parser.parse("")
        
        assert result.raw_text == ""
        assert result.role == ""
        assert len(result.nodes) == 0
    
    def test_parse_variables(self, parser):
        """测试变量提取"""
        prompt = """
        # 节点 A
        你好 {username}，请问有什么需要帮助？
        
        # 节点 B
        您的订单{order_id}已经发货
        """
        
        result = parser.parse(prompt)
        
        assert 'username' in result.variables
        assert 'order_id' in result.variables
    
    def test_parse_node_headers(self, parser):
        """测试不同级别的节点标题"""
        prompt = """
        # A1 主要节点
        内容1
        
        ## A2 次要节点
        内容2
        
        ### A3 辅助节点
        内容3
        """
        
        result = parser.parse(prompt)
        
        assert 'A1' in result.nodes
        assert 'A2' in result.nodes
        assert 'A3' in result.nodes
    
    def test_parse_global_rules(self, parser):
        """测试全局规则提取"""
        prompt = """
        # 角色
        客服
        
        【全流程通用全局执行规则】
        1. 保持友好态度
        2. 及时响应
        """
        
        result = parser.parse(prompt)
        
        assert len(result.global_rules) > 0
        assert '友好态度' in result.global_rules[0] or '友好' in str(result.global_rules)
    
    def test_parse_libraries(self, parser):
        """测试关键词库提取"""
        prompt = """
        ### 正面词库
        好的, 谢谢, 满意
        
        ### 负面词库
        投诉, 退货, 退款
        """
        
        result = parser.parse(prompt)
        
        assert len(result.libraries) > 0
    
    def test_parse_multi_word_node_name(self, parser):
        """测试多字节点名称"""
        prompt = """
        # 节点 确认订单
        请确认您的订单信息
        """
        
        result = parser.parse(prompt)
        
        assert '节点' in result.nodes or '确认订单' in result.nodes or '确认' in result.nodes


class TestPromptParserEdgeCases:
    """边界情况测试"""
    
    def test_parse_only_role(self):
        """测试只有角色的 Prompt"""
        parser = PromptParser()
        prompt = "# 角色\n我是客服"
        
        result = parser.parse(prompt)
        
        assert result.role == "客服"
        assert len(result.nodes) == 0
    
    def test_parse_no_role(self):
        """测试没有角色的 Prompt"""
        parser = PromptParser()
        prompt = "# 节点 A\n内容"
        
        result = parser.parse(prompt)
        
        assert result.role == ""
        assert 'A' in result.nodes
    
    def test_parse_special_characters_in_node(self):
        """测试节点中的特殊字符"""
        parser = PromptParser()
        prompt = """
        # 节点 1.1
        测试内容：特殊字符 @#$%
        """
        
        result = parser.parse(prompt)
        
        assert '1.1' in result.nodes or '1' in result.nodes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
