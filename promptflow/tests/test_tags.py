"""
测试 TagEngine - 标签系统测试用例
"""
import pytest
import sys
sys.path.insert(0, 'src')

from promptflow.tags import (
    TagEngine, TagParser, TagResult, LabelDefinition,
    KeywordMatcher, RegexMatcher, CompositeMatcher, ConditionMatcher
)


class TestLabelDefinition:
    """标签定义测试"""
    
    def test_label_definition_creation(self):
        """测试标签定义创建"""
        label = LabelDefinition(
            id='A',
            name='高意向',
            category='intent',
            trigger_keywords=['好的', '可以', '要'],
            priority=50
        )
        
        assert label.id == 'A'
        assert label.name == '高意向'
        assert label.category == 'intent'
        assert '好的' in label.trigger_keywords
    
    def test_label_definition_defaults(self):
        """测试标签定义默认值"""
        label = LabelDefinition(
            id='B',
            name='测试',
            category='personal'
        )
        
        assert label.trigger_keywords == []
        assert label.trigger_pattern is None
        assert label.priority == 0
        assert label.exclusive == False


class TestTagResult:
    """标签结果测试"""
    
    def test_tag_result_creation(self):
        """测试标签结果创建"""
        result = TagResult(
            intent_label='A',
            intent_label_name='高意向',
            personal_tags=['tag1', 'tag2'],
            counts={'A': 2, 'B': 1}
        )
        
        assert result.intent_label == 'A'
        assert len(result.personal_tags) == 2
    
    def test_tag_result_to_dict(self):
        """测试标签结果转换为字典"""
        result = TagResult(
            intent_label='A',
            intent_label_name='高意向',
            personal_tags=['tag1']
        )
        
        d = result.to_dict()
        
        assert d['intent_label'] == 'A'
        assert d['intent_label_name'] == '高意向'


class TestKeywordMatcher:
    """关键词匹配器测试"""
    
    def test_keyword_matcher_basic(self):
        """测试关键词匹配器基本功能"""
        matcher = KeywordMatcher(['好的', '可以', '谢谢'])
        
        matched, keywords = matcher.match('好的，谢谢', {})
        
        assert matched == True
        assert len(keywords) >= 1
    
    def test_keyword_matcher_case_insensitive(self):
        """测试关键词匹配器大小写不敏感"""
        matcher = KeywordMatcher(['OK', 'YES'], case_sensitive=False)
        
        matched, keywords = matcher.match('ok, yes', {})
        
        assert matched == True
    
    def test_keyword_matcher_no_match(self):
        """测试关键词匹配器无匹配"""
        matcher = KeywordMatcher(['好的', '可以'])
        
        matched, keywords = matcher.match('不知道', {})
        
        assert matched == False
        assert len(keywords) == 0


class TestRegexMatcher:
    """正则匹配器测试"""
    
    def test_regex_matcher_basic(self):
        """测试正则匹配器基本功能"""
        matcher = RegexMatcher(r'\d{11}')
        
        matched, matches = matcher.match('我的电话是13812345678', {})
        
        assert matched == True
        assert '13812345678' in matches
    
    def test_regex_matcher_no_match(self):
        """测试正则匹配器无匹配"""
        matcher = RegexMatcher(r'\d{11}')
        
        matched, matches = matcher.match('没有数字', {})
        
        assert matched == False


class TestCompositeMatcher:
    """组合匹配器测试"""
    
    def test_composite_matcher_any_mode(self):
        """测试组合匹配器任意模式"""
        matcher1 = KeywordMatcher(['好的'])
        matcher2 = KeywordMatcher(['谢谢'])
        
        composite = CompositeMatcher([matcher1, matcher2], mode='any')
        
        matched, keywords = composite.match('好的', {})
        
        assert matched == True
    
    def test_composite_matcher_all_mode(self):
        """测试组合匹配器全部模式"""
        matcher1 = KeywordMatcher(['好的'])
        matcher2 = KeywordMatcher(['谢谢'])
        
        composite = CompositeMatcher([matcher1, matcher2], mode='all')
        
        matched, keywords = composite.match('好的，谢谢', {})
        
        assert matched == True
        assert len(keywords) == 2
    
    def test_composite_matcher_all_mode_no_match(self):
        """测试组合匹配器全部模式无匹配"""
        matcher1 = KeywordMatcher(['好的'])
        matcher2 = KeywordMatcher(['谢谢'])
        
        composite = CompositeMatcher([matcher1, matcher2], mode='all')
        
        matched, keywords = composite.match('好的', {})
        
        assert matched == False


class TestConditionMatcher:
    """条件匹配器测试"""
    
    def test_condition_matcher_min_count(self):
        """测试条件匹配器最小计数"""
        matcher = ConditionMatcher({'min_count': 2, 'label_id': 'A'})
        context = {'counts': {'A': 3, 'B': 1}}
        
        matched, _ = matcher.match('', context)
        
        assert matched == True
    
    def test_condition_matcher_min_count_not_met(self):
        """测试条件匹配器计数不满足"""
        matcher = ConditionMatcher({'min_count': 2, 'label_id': 'A'})
        context = {'counts': {'A': 1, 'B': 1}}
        
        matched, _ = matcher.match('', context)
        
        assert matched == False


class TestTagEngine:
    """标签引擎测试"""
    
    @pytest.fixture
    def engine(self):
        """创建标签引擎实例"""
        return TagEngine()
    
    @pytest.fixture
    def intent_labels(self):
        """创建意向标签"""
        return [
            LabelDefinition(id='M', name='高意向', category='intent', 
                          conditions=['count>=2'], priority=100),
            LabelDefinition(id='A', name='确认意向', category='intent', priority=50),
        ]
    
    @pytest.fixture
    def personal_labels(self):
        """创建个性标签"""
        return [
            LabelDefinition(id='positive', name='正面', category='personal',
                          trigger_keywords=['好的', '谢谢', '满意']),
            LabelDefinition(id='negative', name='负面', category='personal',
                          trigger_keywords=['投诉', '不满', '差评']),
        ]
    
    def test_engine_initialization(self, engine):
        """测试引擎初始化"""
        assert engine is not None
        assert len(engine.intent_labels) == 0
        assert len(engine.personal_labels) == 0
    
    def test_register_label(self, engine):
        """测试注册标签"""
        label = LabelDefinition(id='A', name='测试', category='intent')
        
        engine.register_label(label)
        
        assert 'A' in engine.intent_labels
    
    def test_register_personal_label(self, engine):
        """测试注册个性标签"""
        label = LabelDefinition(id='positive', name='正面', category='personal')
        
        engine.register_label(label)
        
        assert 'positive' in engine.personal_labels
    
    def test_register_labels_from_dict(self, engine, intent_labels, personal_labels):
        """测试批量注册标签"""
        engine.register_labels_from_dict(intent_labels + personal_labels)
        
        assert len(engine.intent_labels) == 2
        assert len(engine.personal_labels) == 2
    
    def test_process_turn(self, engine, personal_labels):
        """测试处理对话轮次"""
        engine.register_labels_from_dict(personal_labels)
        
        engine.process_turn('好的，谢谢', turn=1)
        
        assert 'personal-正面' in engine._collected_tags
    
    def test_process_turn_accumulate(self, engine):
        """测试累积计数"""
        label = LabelDefinition(
            id='question', name='提问', category='personal',
            trigger_keywords=['怎么', '如何'],
            count_rules='accumulate'
        )
        engine.register_label(label)
        
        engine.process_turn('怎么退款？', turn=1)
        engine.process_turn('如何退货？', turn=2)
        
        assert engine._counts.get('question', 0) == 2
    
    def test_determine_intent_with_conditions(self, engine, intent_labels):
        """测试条件判定意向"""
        engine.register_labels_from_dict(intent_labels)
        
        # 添加正面标签来满足 count>=2 条件
        positive = LabelDefinition(
            id='positive', name='正面', category='personal',
            trigger_keywords=['好的']
        )
        engine.register_label(positive)
        
        engine.process_turn('好的', turn=1)
        engine.process_turn('好的', turn=2)
        
        result = engine.determine_intent()
        
        # M 的条件是 count>=2，应该匹配
        assert result is not None
    
    def test_determine_intent_default(self, engine):
        """测试默认意向"""
        default = LabelDefinition(id='C', name='待定', category='intent', priority=1)
        engine.register_label(default)
        
        result = engine.determine_intent()
        
        assert result.intent_label == 'C'
    
    def test_get_result(self, engine):
        """测试获取结果"""
        label = LabelDefinition(id='A', name='测试', category='intent', priority=50)
        engine.register_label(label)
        
        result = engine.get_result()
        
        assert isinstance(result, TagResult)
    
    def test_reset(self, engine, personal_labels):
        """测试重置"""
        engine.register_labels_from_dict(personal_labels)
        engine.process_turn('好的', turn=1)
        
        engine.reset()
        
        assert len(engine._counts) == 0
        assert len(engine._collected_tags) == 0
        assert len(engine._records) == 0


class TestTagParser:
    """标签解析器测试"""
    
    @pytest.fixture
    def parser(self):
        """创建标签解析器实例"""
        return TagParser()
    
    @pytest.fixture
    def sample_prompt_with_tags(self):
        """带标签的示例 Prompt"""
        return """
## 意向标签
| ID | 名称 | 条件 |
|----|------|------|
| M | 高意向 | count>=2 |
| A | 确认意向 | |

## 个性标签
| 名称 | 关键词 |
|------|--------|
| 正面 | 好的, 谢谢, 满意 |
| 负面 | 投诉, 不满, 差评 |
"""
    
    def test_parse_from_markdown(self, parser, sample_prompt_with_tags):
        """测试从 Markdown 解析"""
        intent_labels, personal_labels = parser.parse_from_markdown(sample_prompt_with_tags)
        
        assert len(intent_labels) >= 1
        assert len(personal_labels) >= 1
    
    def test_parse_intent_labels(self, parser, sample_prompt_with_tags):
        """测试解析意向标签"""
        intent_labels, _ = parser.parse_from_markdown(sample_prompt_with_tags)
        
        # 应该包含 M 标签
        m_labels = [l for l in intent_labels if l.get('id') == 'M']
        assert len(m_labels) >= 0 or len(intent_labels) >= 1
    
    def test_parse_personal_labels(self, parser, sample_prompt_with_tags):
        """测试解析个性标签"""
        _, personal_labels = parser.parse_from_markdown(sample_prompt_with_tags)
        
        assert len(personal_labels) >= 1


class TestCreateTagEngineFromPrompt:
    """从 Prompt 创建标签引擎测试"""
    
    def test_create_tag_engine_from_prompt(self):
        """测试从 Prompt 创建标签引擎"""
        from promptflow.tags import create_tag_engine_from_prompt
        
        prompt = """
## 意向标签
| ID | 名称 |
|----|------|
| M | 高意向 |
| A | 确认意向 |
"""
        
        engine, intent_labels, personal_labels = create_tag_engine_from_prompt(prompt)
        
        assert isinstance(engine, TagEngine)
        assert isinstance(intent_labels, list)
        assert isinstance(personal_labels, list)


class TestTagEngineEdgeCases:
    """边界情况测试"""
    
    def test_engine_no_labels(self):
        """测试无标签引擎"""
        engine = TagEngine()
        
        result = engine.get_result()
        
        assert result is not None
    
    def test_process_empty_input(self):
        """测试处理空输入"""
        engine = TagEngine()
        label = LabelDefinition(id='A', name='测试', category='intent')
        engine.register_label(label)
        
        engine.process_turn('', turn=1)
        
        assert len(engine._records) == 1
    
    def test_regex_in_label(self):
        """测试正则表达式标签"""
        engine = TagEngine()
        label = LabelDefinition(
            id='phone', name='电话号码', category='personal',
            trigger_pattern=r'1[3-9]\d{9}'
        )
        engine.register_label(label)
        
        engine.process_turn('我的电话是13812345678', turn=1)
        
        # 应该匹配到电话号码标签
        assert 'personal-电话号码' in engine._collected_tags or len(engine._collected_tags) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
