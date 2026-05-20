"""
方言识别与标准化
"""
from typing import Dict, Tuple, Optional


class DialectConverter:
    """方言转换器"""
    
    # 方言映射表
    DIALECT_MAP: Dict[str, str] = {
        # 粤语系
        "得闲": "有空", "有空": "有空",
        "唔得": "不行", "冇得": "没有",
        "睇下": "看看", "睇睇": "看看",
        "系咁先": "就这样吧",
        
        # 四川/重庆系
        "要得": "可以", "好得": "可以",
        "莫得": "没有", "没得": "没有",
        "巴适": "好", "安逸": "好",
        "龟儿子": "",  # 语气词，非辱骂
        "瓜娃子": "",  # 语气词
        
        # 东北系
        "中": "行", "老好了": "好",
        "整一个": "办一个", "整一个": "弄一个",
        "唠唠": "聊聊", "唠嗑": "聊天",
        "得劲": "好", "得劲儿": "好",
        "磨叽": "犹豫", "磨蹭": "犹豫",
        
        # 河南系
        "中": "行", "中中中": "行",
        "弄啥嘞": "干什么",
        
        # 闽南/台湾系
        "ㄟ": "", "欸": "",  # 语气词
        "好康": "优惠",
        
        # 北方口语
        "成": "可以", "成成成": "可以",
        "得嘞": "好的", "得来": "好的",
        "回头说": "再说吧", "再说吧": "再说吧",
        "没门儿": "不行",
        
        # 常见语气词
        "嘎": "", "嘎嘎": "",
        "咯": "", "撒": "", "嘞": "", "噻": "",
        "哈": "", "嘛": "", "呀": "", "哟": "",
        "咧": "", "喽": "", "呗": "",
        
        # ASR转写错误纠正
        "有会": "优惠", "油惠": "优惠", "优会": "优惠",
        "摄像投": "摄像头", "摄橡头": "摄像头",
        "路由期": "路由器", "路友器": "路由器",
        "广猫": "光猫", "光冒": "光猫",
        "电瓷炉": "电磁炉", "电磁路": "电磁炉",
        "给岛": "给到", "给刀": "给到",
        "按": "安", "脏": "装", "哪": "拿", "油": "有",
        
        # 其他常见口语
        "啥": "什么", "咋": "怎么", "咋啦": "怎么了",
        "咋整": "怎么办", "咋办": "怎么办",
        "咋样": "怎么样", "好不好": "可以吗",
        "晓得不": "知道吗",
    }
    
    # 亲属关系词
    FAMILY_KEYWORDS = [
        "爸爸", "父亲", "爸", "老妈", "妈妈", "母亲", "妈",
        "儿子", "女儿", "孩子", "老公", "老婆", "丈夫", "妻子",
        "老公", "媳妇", "老公", "先生", "太太",
        "哥哥", "姐姐", "弟弟", "妹妹", "亲戚", "亲友",
        "朋友", "同事", "秘书", "家人", "家属",
        "本人", "自己"
    ]
    
    def __init__(self):
        self._family_pattern = "|".join(self.FAMILY_KEYWORDS)
    
    def convert(self, text: str) -> str:
        """
        将方言/口语转换为标准表达
        """
        result = text
        for dialect, standard in self.DIALECT_MAP.items():
            if dialect in result:
                result = result.replace(dialect, standard)
        return result
    
    def is_family_related(self, text: str) -> bool:
        """
        检查是否提到亲属关系
        """
        for keyword in self.FAMILY_KEYWORDS:
            if keyword in text:
                return True
        return False
    
    def extract_family_relation(self, text: str) -> Optional[str]:
        """
        提取亲属关系词
        """
        for keyword in self.FAMILY_KEYWORDS:
            if keyword in text:
                return keyword
        return None
    
    def normalize_response(self, text: str) -> Tuple[str, Dict]:
        """
        标准化用户回复
        返回: (标准化文本, 元数据字典)
        """
        original = text
        normalized = self.convert(text)
        
        meta = {
            "was_dialect": original != normalized,
            "is_family": self.is_family_related(normalized),
            "family_relation": self.extract_family_relation(normalized)
        }
        
        return normalized, meta


# 全局实例
dialect_converter = DialectConverter()
