"""
语义分析与校准
"""
from typing import Tuple, Dict, Optional, List
from enum import Enum
import re


class IntentType(Enum):
    """意图类型"""
    AFFIRMATIVE = "affirmative"      # 肯定
    NEGATIVE = "negative"           # 否定
    NEUTRAL = "neutral"            # 中性/模糊
    REFUSAL = "refusal"             # 拒绝
    BUSY = "busy"                  # 忙碌
    COMPLAINT = "complaint"         # 投诉
    QUESTION = "question"          # 提问
    NOT_SELF = "not_self"          # 非本人
    UNKNOWN = "unknown"             # 未知


class SemanticAnalyzer:
    """语义分析器"""
    
    # 肯定词
    AFFIRMATIVE_WORDS = [
        "是", "对的", "正确", "好的", "行", "可以", "嗯", "啊", "哦", "好",
        "知道", "清楚", "明白", "懂了", "了解", "清楚了", "没问题", "没问题",
        "清楚了", "确实", "的确", "收到", "拿到了", "有", "有的", "在", "在呢",
        "对", "是啊", "对的", "嗯嗯", "收到", "好的好的", "行吧", "好吧"
    ]
    
    # 否定词
    NEGATIVE_WORDS = [
        "不是", "没有", "没", "不", "否", "不对", "不行", "不可以", "别", "莫",
        "没拿到", "没收到", "不知道", "不清楚", "不明白", "不懂", "不了解",
        "不清楚", "没办", "没办理", "没申请", "没参与", "没参加"
    ]
    
    # 拒绝意图词
    REFUSAL_WORDS = [
        "不需要", "不感兴趣", "不要", "不需要", "不用", "拒绝", "算了",
        "别打了", "挂了", "不需要", "不想要", "不想说", "不想聊", "没兴趣",
        "不需要", "不要问", "别问了", "挂了", "挂电话"
    ]
    
    # 忙碌词
    BUSY_WORDS = [
        "忙", "没空", "不方便", "在开会", "在开车", "在吃饭", "在工作",
        "等会", "等一下", "待会", "回头再说", "晚点", "稍后", "现在不方便",
        "没时间", "没功夫", "正在忙"
    ]
    
    # 投诉意图词
    COMPLAINT_WORDS = [
        "投诉", "举报", "告", "举报", "要投诉", "要举报", "曝光", "差评",
        "反馈", "意见", "不满意", "要投诉", "找经理", "找领导", "升级"
    ]
    
    # 非本人词
    NOT_SELF_WORDS = [
        "不是我", "不是本人", "打错了", "打错", "不是我接的", "别人接的",
        "朋友", "家人", "亲戚"
    ]
    
    # 中性词（语气词）
    NEUTRAL_WORDS = [
        "嗯", "啊", "哦", "呃", "嗯嗯", "啊啊啊", "啥", "什么", "哈",
        "咋", "啦", "嘛", "呀", "哟", "咧"
    ]
    
    # 敷衍性肯定（不算真正肯定）
    VAGUE_AFFIRMATIVE = [
        "嗯嗯", "好的好的", "行吧", "还行", "凑合", "大概", "应该", "可能"
    ]
    
    # 反问类（不算肯定）
    RHETORICAL_WORDS = [
        "什么意思", "什么意思?", "啥意思", "什么意思啊", "问这个干嘛",
        "为什么", "为什么呢", "有必要吗", "我为什么要"
    ]
    
    def __init__(self):
        self._build_patterns()
    
    def _build_patterns(self):
        """预编译模式"""
        self._affirmative_pattern = self._build_pattern(self.AFFIRMATIVE_WORDS)
        self._negative_pattern = self._build_pattern(self.NEGATIVE_WORDS)
        self._refusal_pattern = self._build_pattern(self.REFUSAL_WORDS)
        self._busy_pattern = self._build_pattern(self.BUSY_WORDS)
        self._complaint_pattern = self._build_pattern(self.COMPLAINT_WORDS)
        self._not_self_pattern = self._build_pattern(self.NOT_SELF_WORDS)
        self._neutral_pattern = self._build_pattern(self.NEUTRAL_WORDS)
        self._rhetorical_pattern = self._build_pattern(self.RHETORICAL_WORDS)
    
    def _build_pattern(self, words: List[str]) -> re.Pattern:
        """构建正则模式"""
        escaped = [re.escape(w) for w in words]
        return re.compile("|".join(escaped), re.IGNORECASE)
    
    def analyze(self, text: str, context: str = "normal") -> Tuple[IntentType, float, Dict]:
        """
        分析用户意图
        context: 分析上下文 (normal/phone_query/broadband_query/appliance_query/cash_query/installment_query)
        """
        text_lower = text.lower().strip()
        
        result = {
            "original_text": text,
            "analyzed_text": text_lower,
            "context": context
        }
        
        # 按优先级检查
        
        # 1. 投诉
        if self._complaint_pattern.search(text_lower):
            return IntentType.COMPLAINT, 1.0, result
        
        # 2. 拒绝
        if self._refusal_pattern.search(text_lower):
            return IntentType.REFUSAL, 1.0, result
        
        # 3. 忙碌
        if self._busy_pattern.search(text_lower):
            return IntentType.BUSY, 1.0, result
        
        # 4. 非本人
        if self._not_self_pattern.search(text_lower):
            return IntentType.NOT_SELF, 1.0, result
        
        # 5. 反问/质疑（不算肯定）
        if self._rhetorical_pattern.search(text_lower):
            return IntentType.NEUTRAL, 0.5, result
        
        # 6. 否定
        if self._negative_pattern.search(text_lower):
            return IntentType.NEGATIVE, 0.9, result
        
        # 7. 中性语气词
        if self._neutral_pattern.fullmatch(text_lower):
            return IntentType.NEUTRAL, 0.5, result
        
        # 8. 提问
        if "?" in text or "？" in text:
            return IntentType.QUESTION, 0.8, result
        
        # 9. 肯定
        if self._affirmative_pattern.search(text_lower):
            return IntentType.AFFIRMATIVE, 0.9, result
        
        return IntentType.UNKNOWN, 0.5, result
    
    def is_affirmative(self, text: str, context: str = "normal") -> bool:
        """判断是否为肯定回复"""
        intent, confidence, _ = self.analyze(text, context)
        return intent == IntentType.AFFIRMATIVE and confidence >= 0.8
    
    def is_negative(self, text: str, context: str = "normal") -> bool:
        """判断是否为否定回复"""
        intent, confidence, _ = self.analyze(text, context)
        return intent == IntentType.NEGATIVE and confidence >= 0.8
    
    def is_neutral(self, text: str, context: str = "normal") -> bool:
        """判断是否为中性回复"""
        intent, confidence, _ = self.analyze(text, context)
        return intent == IntentType.NEUTRAL
    
    def is_refusal(self, text: str) -> bool:
        """判断是否为拒绝"""
        intent, confidence, _ = self.analyze(text)
        return intent == IntentType.REFUSAL
    
    def is_busy(self, text: str) -> bool:
        """判断是否为忙碌"""
        intent, confidence, _ = self.analyze(text)
        return intent == IntentType.BUSY
    
    def is_complaint(self, text: str) -> bool:
        """判断是否为投诉"""
        intent, confidence, _ = self.analyze(text)
        return intent == IntentType.COMPLAINT
    
    def is_not_self(self, text: str) -> bool:
        """判断是否非本人"""
        intent, confidence, _ = self.analyze(text)
        return intent == IntentType.NOT_SELF
    
    def handle_double_negative_product(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        处理否定词+商品库的情况
        例如："没有没有我就拿了手机"
        返回: (商品库命中, 匹配的商品)
        """
        # 检查是否同时包含否定和商品
        has_negative = self._negative_pattern.search(text)
        # 这里需要在外部配合商品库检查
        return False, None
    
    def get_installment_query_response(self, context: str, customer_info: dict) -> str:
        """
        获取橙分期定义回复
        context: 环节上下文 (normal/installment_query)
        """
        if context == "installment_query":
            return (
                "橙分期是针对电信优质客户提供的一款分期产品，您拿到的折现款项就是通过"
                "在电信办理橙分期业务获得的，请问这个您清楚吗？"
            )
        else:
            return (
                "橙分期是翼支付提供给客户的商品分期服务。您获取的商品或优惠就是办理的橙分期，"
                "需要您电信号码正常使用，月初缴纳话费，电信会返还红包帮您还分期，"
                "不需要您额外还分期款。"
            )


# 全局实例
semantic_analyzer = SemanticAnalyzer()
