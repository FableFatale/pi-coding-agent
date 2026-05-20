"""
商品库匹配规则
"""
from typing import List, Tuple, Optional
import re


class ProductMatcher:
    """商品库匹配器"""
    
    # 违规商品库 - 命中即为违规
    VIOLATION_KEYWORDS = [
        "三轮车", "油卡", "加油券", "购物券", "购物卡", "加油卡", "超市卡", 
        "物业费", "代金券", "耳机", "蓝牙", "蓝牙耳机", "按摩器", "按摩仪", 
        "光盘", "词典笔", "扫描笔", "智能笔", "学习笔", "读写笔", "投影仪", 
        "投影", "电子笔", "家具礼包", "家用电器", "家电套装", "家电", "家具", 
        "厨房用品", "厨房用具", "智家大礼包", "智家礼包", "油烟机", "智电炸锅", 
        "消毒柜", "燃气灶", "打印机", "打印器", "扫地机", "扫地器", "净化器", 
        "净化机", "净水机", "净水器", "电动车", "电动汽车", "电瓶车", 
        "电动自行车", "摩托", "电车", "自行车", "汽车", "电动的汽车", "电动的车", 
        "山地车", "洗碗机", "阿尔法", "阿尔法蛋", "翻译机", "电子产品", "电子设备", 
        "电器", "话费券", "电暖桌", "吸尘器", "吸尘机", "热风机", "热风器", 
        "压力煲", "压力高", "高压锅", "高压包", "壶", "焖锅", "空气炸锅", 
        "料理锅", "涮烤锅", "炸锅", "电火锅", "烤火的", "烤火炉", "电压锅", 
        "饮水机", "饮水器", "一体锅", "烤炉", "烤锅", "蒸锅", "鸳鸯锅", 
        "烤涮一体锅", "烤涮锅", "豆浆机", "电水壶", "水壶", "电暖炉", "暖炉", 
        "榨汁机", "榨汁器", "挂烫机", "挂烫器", "电风扇", "暖风扇", "循环扇", 
        "风扇", "电扇", "电蒸锅", "电热锅", "电力压锅", "压锅", "电锅", 
        "养生壶", "电饼铛", "电饼档", "茶具", "炒锅", "电磁炉", "磁炉", "炉子", 
        "茶吧机", "破壁机", "茶吧器", "破壁器", "微波炉", "压力锅", "烤箱", 
        "多功能锅", "保温杯", "吹风机", "吹风器", "电吹风", "吹风", "吹头发的", 
        "电炸锅", "蒸汽锅", "烤盘", "烧水壶", "除螨仪", "除螨机", "除螨器", 
        "绞肉机", "绞肉器", "空气炸锅机", "剃须刀", "刮胡刀", "筋膜枪", "加湿器", 
        "料理器", "料理机", "充电宝", "充电线", "鼠标", "模型", "飞机模型", 
        "高铁模型", "火车模型", "唱歌设备", "唱歌的设备", "收音机", "录音机", 
        "小礼品", "礼品", "礼包", "大礼包", "赠品", "奖品", "礼物", "被子", 
        "棉被", "空调被", "羽绒被", "绒被", "蚕丝被", "电热毯解压器", "电热壶", 
        "转换器", "行李箱", "热水壶", "电动牙刷", "足浴桶", "泡脚的", "泡脚桶", 
        "取暖器", "取暖机", "取暖的", "话费", "购机券", "购金券", "购机款", "充值卡"
    ]
    
    # 合规商品库 - 命中即为正常/营销缺失
    NORMAL_KEYWORDS = [
        "手机", "天翼", "小E", "优惠", "打折", "折扣", "国补", "设备", "关猫", 
        "魅族", "联想", "摩托罗拉", "索尼", "华硕", "华为", "oppo", "vivo", 
        "红米", "小米", "荣耀", "苹果", "mate60", "iphone", "中兴", "三星", 
        "全光", "一加", "真我", "合约机", "电话", "话机", "智能机", "购机优惠", 
        "财务覆盖", "全屋组网", "全屋覆盖", "全部覆盖", "全屋", "Fttr", "fttr",
        "FTP", "表", "手表", "手环", "小天才", "电话手表", "儿童手表", "电子表", 
        "云电脑", "VR", "电脑", "平板电脑", "笔记本", "平板", "iPad", "ipad", 
        "pad", "爱拍", "爱派", "i派", "派", "Pad", "PAD", "光猫", "机顶盒", "盒", 
        "猫", "网", "网关", "二宽", "千兆", "光纤", "宽带", "WiFi", "wifi", 
        "无线", "网线", "路由", "路由器", "无线路由", "无线网", "无线路由器", 
        "小爱同学", "小爱", "小猪", "角度", "小豆", "小杜", "小艾", "小度", 
        "小肚", "小翼管家", "小翼", "天猫精灵", "天猫", "精灵", "智能遥控", 
        "智能音响", "智能猫眼", "智能门锁", "智能门铃", "密码锁", "指纹密码锁", 
        "电子锁", "门锁", "智能报警器", "智能开关", "门铃", "音响", "音箱", 
        "猫眼", "指纹锁", "锁", "报警器", "智能产品", "智能锁", "消防烟感器", 
        "智慧屏", "智慧大屏", "空调", "冰箱", "洗衣机", "点读笔", "伴读机", 
        "AC", "AP", "体感游戏", "打游戏的", "遥控", "开关", "卫星终端", "卫星", 
        "智能传感器", "传感器", "智能窗帘电机", "智能机器人", "机器人", 
        "智能学习桌椅套", "桌椅套", "学习桌", "智能胸卡", "胸卡", "学生证", 
        "助听器", "助听机", "热水器", "游戏机", "学习机", "家教机", "家教器", 
        "收银音箱", "老人陪伴机", "陪伴机", "智能陪伴机", "收银一体机", "收银机", 
        "收银设备", "收银的", "收款机", "扫码终端", "扫码的终端", "扫码枪", 
        "扫码设备", "扫码的", "血氧仪", "血氧机", "台灯", "体脂秤", "电子秤", 
        "体重秤", "声控灯", "智能灯", "感应灯", "太阳能灯", "灯", "秤", 
        "电饭煲", "电饭锅", "饭煲", "饭锅", "煮饭的", "煮饭锅", "煮饭煲", 
        "插头", "插座", "插排", "插板", "排插", "智能插排", "智能插头", 
        "智能排插", "POS机", "话筒", "固话机", "固定电话", "智能康养遥控器", 
        "遥控器", "老人机", "老年机", "摄像头"
    ]
    
    # 锅/堡类特殊处理 - 不属于以下则为违规
    ALLOWED_POT_KEYWORDS = ["电饭煲", "电饭锅", "饭煲", "饭锅", "煮饭的", "煮饭锅", "煮饭煲"]
    
    # 手机/宽带类关键词
    PHONE_KEYWORDS = ["手机", "电话", "话机", "合约机", "智能机", "mate60", "iphone", 
                      "华为", "小米", "oppo", "vivo", "苹果", "荣耀", "中兴", "三星"]
    BROADBAND_KEYWORDS = ["光猫", "机顶盒", "宽带", "wifi", "WiFi", "光纤", "路由器", 
                         "网关", "网线", "fttr", "Fttr", "全光", "全屋"]
    
    # 家电类关键词
    APPLIANCE_KEYWORDS = ["空调", "冰箱", "洗衣机", "热水器", "电视", "抽油烟机", 
                         "油烟机", "小度", "智能门锁", "摄像头", "手环", "手表"]
    
    def __init__(self):
        self._build_patterns()
    
    def _build_patterns(self):
        """预编译正则表达式"""
        self._violation_pattern = self._build_pattern(self.VIOLATION_KEYWORDS)
        self._normal_pattern = self._build_pattern(self.NORMAL_KEYWORDS)
        self._phone_pattern = self._build_pattern(self.PHONE_KEYWORDS)
        self._broadband_pattern = self._build_pattern(self.BROADBAND_KEYWORDS)
        self._appliance_pattern = self._build_pattern(self.APPLIANCE_KEYWORDS)
        self._allowed_pot_pattern = self._build_pattern(self.ALLOWED_POT_KEYWORDS)
    
    def _build_pattern(self, keywords: List[str]) -> re.Pattern:
        """构建正则模式"""
        # 转义特殊字符并用|连接
        escaped = [re.escape(k) for k in keywords]
        return re.compile("|".join(escaped), re.IGNORECASE)
    
    def is_pot_keyword(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        检查是否为锅/堡类关键词
        返回: (是否为锅堡类, 匹配到的词或None)
        """
        # 先检查是否匹配到锅/堡类
        pot_match = re.search(r"锅|堡", text)
        if pot_match:
            matched_word = pot_match.group()
            # 检查是否在允许列表中
            if self._allowed_pot_pattern.search(text):
                return False, None
            return True, matched_word
        return False, None
    
    def is_violation(self, text: str) -> Tuple[bool, List[str]]:
        """
        检查是否命中违规商品库
        返回: (是否违规, 匹配的关键词列表)
        """
        matches = []
        
        # 特殊检查锅/堡类
        is_pot, _ = self.is_pot_keyword(text)
        if is_pot:
            matches.append("违规锅堡类")
        
        # 检查违规关键词
        violation_matches = self._violation_pattern.findall(text)
        matches.extend(violation_matches)
        
        return len(matches) > 0, matches
    
    def is_normal_product(self, text: str) -> Tuple[bool, List[str]]:
        """
        检查是否命中合规商品库
        返回: (是否合规商品, 匹配的关键词列表)
        """
        matches = self._normal_pattern.findall(text)
        return len(matches) > 0, matches
    
    def has_phone(self, text: str) -> bool:
        """检查是否提到手机类"""
        return bool(self._phone_pattern.search(text))
    
    def has_broadband(self, text: str) -> bool:
        """检查是否提到宽带类"""
        return bool(self._broadband_pattern.search(text))
    
    def has_appliance(self, text: str) -> bool:
        """检查是否提到家电类"""
        return bool(self._appliance_pattern.search(text))
    
    def match_category(self, text: str) -> str:
        """
        匹配商品类别
        返回: "phone" | "broadband" | "appliance" | "violation" | "unknown"
        """
        if self.has_phone(text):
            return "phone"
        if self.has_broadband(text):
            return "broadband"
        if self.has_appliance(text):
            return "appliance"
        if self.is_violation(text)[0]:
            return "violation"
        return "unknown"


# 全局实例
product_matcher = ProductMatcher()
