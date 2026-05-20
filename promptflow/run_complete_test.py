#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
电信橙分期话术与标签测试 - 完整版
功能：
1. 解析真实Excel/CSV对话记录
2. 批量测试所有对话
3. 详细分析错误案例
4. 生成HTML可视化报告
5. 规则优化建议
"""
import sys
import os
import csv
import json
import glob
from datetime import datetime
from collections import defaultdict

# ============================================================
# 配置
# ============================================================

VERSION = "2.0"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")


# ============================================================
# 商品库 (来自个性标签.md)
# ============================================================

NORMAL_PRODUCTS = [
    "手机", "天翼", "小E", "优惠", "打折", "折扣", "国补", "设备", "关猫",
    "魅族", "联想", "摩托罗拉", "索尼", "华硕", "华为", "oppo", "vivo",
    "红米", "小米", "荣耀", "苹果", "mate60", "iphone", "中兴", "三星",
    "全光", "一加", "真我", "合约机", "电话", "话机", "智能机", "购机优惠",
    "财务覆盖", "全屋组网", "全屋覆盖", "全部覆盖", "全屋", "Fttr", "fttr",
    "表", "手表", "手环", "小天才", "电话手表", "儿童手表", "电子表",
    "云电脑", "VR", "电脑", "平板电脑", "笔记本", "平板", "iPad", "ipad",
    "pad", "爱拍", "爱派", "派", "Pad", "PAD", "光猫", "机顶盒", "盒",
    "猫", "网", "网关", "二宽", "千兆", "光纤", "宽带", "WiFi", "wifi",
    "无线", "网线", "路由", "路由器", "无线路由", "无线网", "小爱同学",
    "小爱", "小猪", "小豆", "小杜", "小艾", "小度", "小肚", "小翼管家",
    "小翼", "天猫精灵", "天猫", "精灵", "智能遥控", "智能音响", "智能猫眼",
    "智能门锁", "智能门铃", "密码锁", "指纹密码锁", "电子锁", "门锁",
    "智能报警器", "智能开关", "门铃", "音响", "音箱", "猫眼", "指纹锁",
    "锁", "报警器", "智能产品", "智能锁", "消防烟感器", "智慧屏", "智慧大屏",
    "空调", "冰箱", "洗衣机", "点读笔", "伴读机", "AC", "AP", "体感游戏",
    "遥控", "开关", "卫星终端", "卫星", "智能传感器", "传感器", "智能窗帘电机",
    "智能机器人", "机器人", "智能学习桌椅套", "桌椅套", "学习桌", "智能胸卡",
    "胸卡", "学生证", "助听器", "助听机", "热水器", "游戏机", "学习机",
    "家教机", "家教器", "收银音箱", "老人陪伴机", "陪伴机", "智能陪伴机",
    "收银一体机", "收银机", "收银设备", "收银的", "收款机", "扫码终端",
    "扫码的终端", "扫码枪", "扫码设备", "扫码的", "血氧仪", "血氧机",
    "台灯", "体脂秤", "电子秤", "体重秤", "声控灯", "智能灯", "感应灯",
    "太阳能灯", "灯", "秤", "电饭煲", "电饭锅", "饭煲", "饭锅", "煮饭的",
    "煮饭锅", "煮饭煲", "插头", "插座", "插排", "插板", "排插", "智能插排",
    "智能插头", "智能排插", "POS机", "话筒", "固话机", "固定电话",
    "智能康养遥控器", "遥控器", "老人机", "老年机", "摄像头"
]

VIOLATION_PRODUCTS = [
    "购机券", "三轮车", "购金券", "购机款", "充值卡", "购物券", "油卡",
    "加油券", "优惠券", "购物卡", "加油卡", "超市卡", "物业费", "代金券",
    "耳机", "蓝牙", "蓝牙耳机", "按摩器", "按摩仪", "光盘", "词典笔",
    "扫描笔", "智能笔", "学习笔", "读写笔", "投影仪", "投影", "电子笔",
    "家具礼包", "家用电器", "家电套装", "家电", "家具", "厨房用品",
    "厨房用具", "智家大礼包", "智家礼包", "油烟机", "智电炸锅", "消毒柜",
    "燃气灶", "打印机", "扫地机", "打印器", "扫地器", "净化器", "净化机",
    "净水机", "净水器", "电动车", "电动汽车", "电瓶车", "电动自行车",
    "摩托", "电车", "自行车", "汽车", "电动的汽车", "电动的车", "山地车",
    "洗碗机", "阿尔法", "阿尔法蛋", "翻译机", "电子产品", "电子设备",
    "电器", "话费券", "电暖桌", "吸尘器", "吸尘机", "热风机", "热风器",
    "压力煲", "压力高", "高压锅", "高压包", "壶", "焖锅", "空气炸锅",
    "料理锅", "涮烤锅", "炸锅", "电火锅", "烤火的", "烤火炉", "电压锅",
    "饮水机", "饮水器", "一体锅", "烤炉", "烤锅", "蒸锅", "鸳鸯锅",
    "烤涮一体锅", "烤涮锅", "豆浆机", "电水壶", "水壶", "电暖炉", "暖炉",
    "榨汁机", "榨汁器", "挂烫机", "挂烫器", "电风扇", "暖风扇", "循环扇",
    "风扇", "电扇", "电蒸锅", "电热锅", "电力压锅", "压锅", "电锅",
    "养生壶", "电饼铛", "电饼档", "茶具", "炒锅", "电磁炉", "磁炉",
    "炉子", "茶吧机", "破壁机", "茶吧器", "破壁器", "微波炉", "压力锅",
    "烤箱", "多功能锅", "保温杯", "吹风机", "吹风器", "电吹风", "吹风",
    "吹头发的", "电炸锅", "蒸汽锅", "烤盘", "烧水壶", "除螨仪", "除螨机",
    "除螨器", "绞肉机", "绞肉器", "空气炸锅机", "剃须刀", "刮胡刀",
    "筋膜枪", "加湿器", "料理器", "料理机", "充电宝", "充电线", "鼠标",
    "模型", "飞机模型", "高铁模型", "火车模型", "唱歌设备", "唱歌的设备",
    "收音机", "录音机", "小礼品", "礼品", "礼包", "大礼包", "赠品",
    "奖品", "礼物", "被子", "棉被", "空调被", "羽绒被", "绒被", "蚕丝被",
    "电热毯解压器", "电热壶", "转换器", "行李箱", "热水壶", "电动牙刷",
    "足浴桶", "泡脚的", "泡脚桶", "取暖器", "取暖机", "取暖的", "话费"
]


# ============================================================
# 方言映射
# ============================================================

DIALECT_MAP = {
    "收到咯": "收到了", "拿到咯": "拿到了", "冇": "没有", "係啊": "是的",
    "不晓得咡": "不知道", "知道得嘛": "知道了", "得嘛": "知道了",
    "整咯": "买了", "整了个": "买了个", "晓得咯": "知道了", "啥子": "什么",
    "咋整": "怎么回事", "要得": "好的", "知道得了": "知道了", "中": "好的",
    "整一个": "买了一个", "没得": "没有", "莫得": "没有"
}


# ============================================================
# 标签分类器 (优化版)
# ============================================================

class OptimizedTagClassifier:
    """
    优化版标签分类器
    修复问题.txt中的错误案例
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.full_text = ""
        self.turns = 0
        self.received_goods = None
        self.has_payment = False
        self.goods_type = None
        self.knows_contract = None
        self.is_complaint = False
        self.is_fraud = False
        self.is_cash_out = False
        self.is_recycled = False  # 手机被回收
        self.dialogue_history = []

    def process_dialogue(self, conversation: list):
        self.dialogue_history = conversation
        self.turns = len(conversation)

        all_user_text = " ".join([turn.get("user", "") for turn in conversation])
        self.full_text = all_user_text

        # 转换方言
        for dialect, standard in DIALECT_MAP.items():
            self.full_text = self.full_text.replace(dialect, standard)

        self._extract_features()

    def _extract_features(self):
        text = self.full_text

        # 1. 回收/样板检测 (修复2246037)
        recycled_keywords = ["回收", "样板", "做样板", "被门店"]
        if any(kw in text for kw in recycled_keywords):
            self.is_recycled = True
            self.received_goods = False  # 被回收 = 未持有

        # 2. 付费关键词检测
        payment_keywords = ["花钱", "付费", "自费", "买", "花了", "花咯", "花啦",
                           "付了", "付款", "购买", "买的", "整咯", "整了个"]
        if any(kw in text for kw in payment_keywords):
            self.has_payment = True
            self.received_goods = True

        # 3. 收到商品关键词
        received_keywords = ["拿到了", "收到了", "有", "有收到", "拿到手",
                           "已经拿到", "拿到喽", "装好了", "安装好了",
                           "买咯", "买了个", "搞了个", "优惠", "用上"]
        if any(kw in text for kw in received_keywords):
            self.received_goods = True

        # 4. 未收到商品关键词
        not_received_keywords = ["没拿到", "没收到", "没有", "什么都没",
                                "只有钱", "木有", "冇", "根本冇", "根本没",
                                "没得", "未收到", "没有收到", "未拿到",
                                "没有拿到", "啥都没"]
        if any(kw in text for kw in not_received_keywords):
            self.received_goods = False
            if "钱" in text or "折现" in text:
                self.is_cash_out = True

        # 5. 商品类型检测
        for product in NORMAL_PRODUCTS + VIOLATION_PRODUCTS:
            if product in text:
                self.goods_type = product
                break

        # 6. 知晓合约检测 (修复2246359 - "嗯"不算否定)
        # 明确知晓
        knows_keywords = ["知道", "明白", "理解", "清楚", "晓得", "晓得了",
                         "了解了", "清楚了"]
        # 明确不知晓
        not_knows_keywords = ["不知道", "不晓得", "不晓滴", "不造", "没办过",
                             "没要求", "不清", "啥是", "啥玩意儿", "咋还",
                             "咋整", "咋回事", "不理解", "没听过", "不清楚"]
        if any(kw in text for kw in knows_keywords):
            self.knows_contract = True
        if any(kw in text for kw in not_knows_keywords):
            self.knows_contract = False

        # 7. 投诉/欺诈检测
        complaint_keywords = ["投诉", "骗", "骗人", "被骗", "欺诈", "虚假",
                            "坑", "坑人", "垃圾", "太差", "不满"]
        fraud_keywords = ["被骗了", "被骗咯", "被坑", "被坑咯", "欺诈"]
        if any(kw in text for kw in complaint_keywords):
            self.is_complaint = True
        if any(kw in text for kw in fraud_keywords):
            self.is_fraud = True

    def classify(self) -> str:
        """
        标签分类
        优先级: 套机套现 > 违规商品 > 营销缺失 > 正常 > 未沟通
        """

        # 1. 套机套现 (优先级1)
        # 条件: 未收到商品 + 无付费 + (未持有 或 被回收)
        if self.received_goods is False or self.is_recycled:
            if not self.has_payment:
                return "套机套现"

        # 2. 违规商品 (优先级2)
        if self.received_goods and self.goods_type:
            if self.goods_type in VIOLATION_PRODUCTS:
                return "违规商品"

        # 3. 营销缺失 (优先级3)
        if self.received_goods and self.knows_contract is False:
            return "营销缺失"
        if self.is_fraud:
            return "营销缺失"
        if self.is_complaint and self.received_goods:
            return "营销缺失"
        if "啥是" in self.full_text or "啥玩意儿" in self.full_text:
            if self.received_goods:
                return "营销缺失"

        # 4. 正常 (优先级4)
        if self.received_goods and self.goods_type:
            if self.goods_type in NORMAL_PRODUCTS:
                # 收到正常商品 + 知晓合约 或 中性回答 都算正常
                if self.knows_contract is True or self.knows_contract is None:
                    return "正常"

        if self.received_goods:
            return "正常"

        # 5. 未沟通 (优先级5)
        if self.turns < 2 and self.received_goods is None:
            return "未沟通"

        return "营销缺失"

    def get_context(self) -> dict:
        return {
            "turns": self.turns,
            "received_goods": self.received_goods,
            "goods_type": self.goods_type,
            "has_payment": self.has_payment,
            "knows_contract": self.knows_contract,
            "is_complaint": self.is_complaint,
            "is_fraud": self.is_fraud,
            "is_cash_out": self.is_cash_out,
            "is_recycled": self.is_recycled,
            "label": self.classify()
        }


# ============================================================
# CSV/Excel 解析器
# ============================================================

def parse_dialogue_file(filepath: str) -> list:
    """解析对话记录文件"""
    dialogues = []

    # 首先检测文件实际格式（通过文件头）
    with open(filepath, 'rb') as f:
        header = f.read(8)
    
    # PK header = ZIP (xlsx/docx等Office格式)
    # %PDF = PDF
    # 其他 = 可能是CSV或文本
    is_excel = header[:2] == b'PK' or header[:4] == b'%PDF'
    
    if is_excel:
        # Excel格式
        try:
            import openpyxl
            wb = openpyxl.load_workbook(filepath, read_only=True)
            sheet = wb.active
            
            # 获取表头
            headers = [cell.value for cell in sheet[1]]
            
            # 读取数据行
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if any(cell is not None for cell in row):  # 跳过空行
                    record = {headers[i]: row[i] for i in range(len(headers))}
                    dialogues.append(record)
            wb.close()
        except ImportError:
            print(f"   ⚠️ 需要安装 openpyxl: pip install openpyxl")
        except Exception as e:
            print(f"   ⚠️ 无法解析Excel: {filepath} - {e}")
    else:
        # CSV格式
        try:
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            dialogues.append(row)
                    break
                except UnicodeDecodeError:
                    continue
        except Exception as e:
            print(f"   ⚠️ 无法解析CSV: {filepath} - {e}")

    return dialogues


def find_dialogue_files() -> dict:
    """查找所有对话记录文件"""
    files = {
        "真实对话": [],
        "话术数据": [],
        "个性标签": []
    }

    # 查找真实对话文件
    real_dir = os.path.join(DATA_DIR, "真实对话")
    if os.path.exists(real_dir):
        for ext in ["*.csv", "*.xlsx", "*.xls"]:
            files["真实对话"].extend(glob.glob(os.path.join(real_dir, ext)))

    # 查找话术数据文件
    script_dir = os.path.join(DATA_DIR, "话术数据")
    if os.path.exists(script_dir):
        for ext in ["*.md", "*.txt", "*.csv"]:
            files["话术数据"].extend(glob.glob(os.path.join(script_dir, ext)))

    # 查找个性标签文件
    tag_file = os.path.join(DATA_DIR, "个性标签.md")
    if os.path.exists(tag_file):
        files["个性标签"].append(tag_file)

    return files


# ============================================================
# 测试用例
# ============================================================

ERROR_CASES = [
    {
        "id": "2245940",
        "description": "标签出错，应该是正常",
        "expected": "正常",
        "reason": "用户说'拿到了手机'且'知道'，应判定为正常",
        "dialogue": [
            {"user": "我拿到了手机", "ai": "请问您知道橙分期吗？"},
            {"user": "知道", "ai": "好的"}
        ]
    },
    {
        "id": "2246337",
        "description": "标签出错，应该是正常",
        "expected": "正常",
        "reason": "用户说'拿到了'且'知道'，应判定为正常",
        "dialogue": [
            {"user": "拿到了", "ai": "请问您知道合约吗？"},
            {"user": "知道", "ai": "好的"}
        ]
    },
    {
        "id": "2246052",
        "description": "核实流程出错，用户表示没有拿到手机，应该继续问有没有拿到宽带",
        "expected": "营销缺失",
        "reason": "流程错误，话术应继续问宽带/家电，不是直接结束",
        "dialogue": [
            {"user": "我没有拿到手机", "ai": "好的"},  # 错误：应该继续问
            {"user": "", "ai": ""}
        ]
    },
    {
        "id": "2246359",
        "description": "标签出错，应该是正常，用户没有明确说自己不知道橙分期",
        "expected": "正常",
        "reason": "用户只回复'嗯'，不是明确否定，应视为中性/正常",
        "dialogue": [
            {"user": "拿到了手机", "ai": "请问您知道橙分期吗？"},
            {"user": "嗯", "ai": "好的"}
        ]
    },
    {
        "id": "2246143",
        "description": "标签出错，应该是正常",
        "expected": "正常",
        "reason": "用户明确说'拿到了手机'且'知道'",
        "dialogue": [
            {"user": "我办理了橙分期，拿到了手机", "ai": "请问您知道合约吗？"},
            {"user": "知道", "ai": "好的"}
        ]
    },
    {
        "id": "2246037",
        "description": "用户表示手机被门店回收了，要做样板机，实际情况应该是套机套现",
        "expected": "套机套现",
        "reason": "'手机被回收/做样板' = 未持有商品，应判定套机套现",
        "dialogue": [
            {"user": "手机被门店回收了，要做样板机", "ai": "请问您知道橙分期吗？"},
            {"user": "知道", "ai": "好的"}
        ]
    }
]


# ============================================================
# HTML报告生成器
# ============================================================

def generate_html_report(results: dict) -> str:
    """生成HTML可视化报告"""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 统计数据
    error_total = results["error_cases"]["total"]
    error_passed = results["error_cases"]["passed"]
    error_failed = error_total - error_passed

    batch_total = results["batch_test"]["total"]
    batch_passed = results["batch_test"]["passed"]
    batch_failed = batch_total - batch_passed

    # 分类统计
    category_stats = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0})
    for case_id, case in results["error_cases"]["details"].items():
        cat = case.get("category", "其他")
        category_stats[cat]["total"] += 1
        if case["passed"]:
            category_stats[cat]["passed"] += 1
        else:
            category_stats[cat]["failed"] += 1

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>电信橙分期话术与标签测试报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Microsoft YaHei', 'PingFang SC', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}

        /* 头部 */
        .header {{ background: white; border-radius: 16px; padding: 30px; margin-bottom: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }}
        .header h1 {{ color: #333; font-size: 28px; margin-bottom: 10px; }}
        .header .subtitle {{ color: #666; font-size: 14px; }}
        .header .version {{ background: #667eea; color: white; padding: 5px 15px; border-radius: 20px; display: inline-block; margin-top: 10px; font-size: 12px; }}

        /* 统计卡片 */
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .stat-card {{ background: white; border-radius: 16px; padding: 25px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }}
        .stat-card h3 {{ color: #666; font-size: 14px; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }}
        .stat-card .value {{ font-size: 42px; font-weight: bold; margin-bottom: 5px; }}
        .stat-card .sub {{ color: #999; font-size: 13px; }}
        .stat-card.total {{ border-top: 4px solid #3498db; }}
        .stat-card.total .value {{ color: #3498db; }}
        .stat-card.passed {{ border-top: 4px solid #27ae60; }}
        .stat-card.passed .value {{ color: #27ae60; }}
        .stat-card.failed {{ border-top: 4px solid #e74c3c; }}
        .stat-card.failed .value {{ color: #e74c3c; }}
        .stat-card.rate {{ border-top: 4px solid #f39c12; }}
        .stat-card.rate .value {{ color: #f39c12; }}

        /* 标签 */
        .section {{ background: white; border-radius: 16px; padding: 25px; margin-bottom: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #333; font-size: 20px; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #f0f0f0; }}
        .section h2 .icon {{ margin-right: 10px; }}

        /* 测试卡片 */
        .test-card {{ background: #f8f9fa; border-radius: 12px; padding: 20px; margin-bottom: 15px; border-left: 4px solid #ddd; transition: all 0.3s; }}
        .test-card:hover {{ transform: translateX(5px); box-shadow: 0 5px 20px rgba(0,0,0,0.1); }}
        .test-card.pass {{ border-left-color: #27ae60; background: #f0fff4; }}
        .test-card.fail {{ border-left-color: #e74c3c; background: #fff5f5; }}

        .test-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .test-id {{ background: #667eea; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        .test-status {{ padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        .test-status.pass {{ background: #27ae60; color: white; }}
        .test-status.fail {{ background: #e74c3c; color: white; }}

        .test-name {{ font-weight: bold; color: #333; margin-bottom: 8px; }}
        .test-desc {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
        .test-reason {{ background: #fff3cd; padding: 10px; border-radius: 8px; font-size: 13px; color: #856404; margin-bottom: 10px; }}

        .dialogue-box {{ background: white; border-radius: 8px; padding: 15px; margin-top: 10px; }}
        .dialogue-item {{ margin: 8px 0; padding: 8px 12px; border-radius: 8px; }}
        .dialogue-item.user {{ background: #e8f5e9; margin-left: 20px; }}
        .dialogue-item.ai {{ background: #e3f2fd; margin-right: 20px; }}
        .dialogue-item .label {{ font-size: 11px; color: #666; margin-bottom: 3px; }}
        .dialogue-item .text {{ color: #333; }}

        .context-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 10px; }}
        .context-item {{ background: white; padding: 8px 12px; border-radius: 8px; text-align: center; }}
        .context-item .label {{ font-size: 11px; color: #999; }}
        .context-item .value {{ font-size: 14px; font-weight: bold; color: #333; }}

        .result-compare {{ display: flex; gap: 20px; margin-top: 10px; }}
        .result-item {{ flex: 1; padding: 10px; border-radius: 8px; text-align: center; }}
        .result-item.expected {{ background: #d4edda; }}
        .result-item.actual {{ background: #f8d7da; }}
        .result-item .label {{ font-size: 11px; color: #666; }}
        .result-item .value {{ font-size: 16px; font-weight: bold; }}
        .result-item.expected .value {{ color: #155724; }}
        .result-item.actual .value {{ color: #721c24; }}

        /* 优化建议 */
        .suggestion {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; margin-top: 15px; }}
        .suggestion h4 {{ margin-bottom: 10px; font-size: 16px; }}
        .suggestion ul {{ margin-left: 20px; line-height: 1.8; }}
        .suggestion li {{ margin-bottom: 5px; }}

        /* 表格 */
        .data-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .data-table th, .data-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        .data-table th {{ background: #f8f9fa; color: #666; font-weight: 600; font-size: 13px; text-transform: uppercase; }}
        .data-table tr:hover {{ background: #f8f9fa; }}
        .data-table .badge {{ padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        .badge.pass {{ background: #27ae60; color: white; }}
        .badge.fail {{ background: #e74c3c; color: white; }}
        .badge.normal {{ background: #3498db; color: white; }}
        .badge.warning {{ background: #f39c12; color: white; }}

        /* 页脚 */
        .footer {{ text-align: center; color: rgba(255,255,255,0.7); padding: 20px; font-size: 13px; }}

        /* 动画 */
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .section, .stat-card {{ animation: fadeIn 0.5s ease-out; }}
        .stat-card:nth-child(2) {{ animation-delay: 0.1s; }}
        .stat-card:nth-child(3) {{ animation-delay: 0.2s; }}
        .stat-card:nth-child(4) {{ animation-delay: 0.3s; }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <h1>📊 电信橙分期话术与标签测试报告</h1>
            <div class="subtitle">版本 {VERSION} | 生成时间: {timestamp}</div>
            <span class="version">完整版测试</span>
        </div>

        <!-- 统计卡片 -->
        <div class="stats-grid">
            <div class="stat-card total">
                <h3>错误案例测试</h3>
                <div class="value">{error_total}</div>
                <div class="sub">总测试数</div>
            </div>
            <div class="stat-card passed">
                <h3>通过</h3>
                <div class="value">{error_passed}</div>
                <div class="sub">正确判定</div>
            </div>
            <div class="stat-card failed">
                <h3>失败</h3>
                <div class="value">{error_failed}</div>
                <div class="sub">需要优化</div>
            </div>
            <div class="stat-card rate">
                <h3>通过率</h3>
                <div class="value">{error_passed/error_total*100:.0f}%</div>
                <div class="sub">判定准确度</div>
            </div>
        </div>

        <!-- 错误案例分析 -->
        <div class="section">
            <h2><span class="icon">🔍</span>错误案例详细分析</h2>
"""

    # 添加每个错误案例
    for case in ERROR_CASES:
        result = results["error_cases"]["details"].get(case["id"], {})
        passed = result.get("passed", False)
        actual = result.get("actual", "未知")
        context = result.get("context", {})

        card_class = "pass" if passed else "fail"
        status_class = "pass" if passed else "fail"
        status_text = "✅ 通过" if passed else "❌ 失败"

        # 对话HTML
        dialogue_html = ""
        for turn in case["dialogue"]:
            user = turn.get("user", "") or "(无输入)"
            ai = turn.get("ai", "") or ""
            dialogue_html += f'''
            <div class="dialogue-item user">
                <div class="label">👤 用户</div>
                <div class="text">{user}</div>
            </div>'''
            if ai:
                dialogue_html += f'''
            <div class="dialogue-item ai">
                <div class="label">🤖 AI</div>
                <div class="text">{ai}</div>
            </div>'''

        html += f'''
            <div class="test-card {card_class}">
                <div class="test-header">
                    <span class="test-id">案例 {case["id"]}</span>
                    <span class="test-status {status_class}">{status_text}</span>
                </div>
                <div class="test-name">{case["description"]}</div>
                <div class="test-reason">💡 {case["reason"]}</div>

                <div class="result-compare">
                    <div class="result-item expected">
                        <div class="label">期望标签</div>
                        <div class="value">{case["expected"]}</div>
                    </div>
                    <div class="result-item actual">
                        <div class="label">实际判定</div>
                        <div class="value">{actual}</div>
                    </div>
                </div>

                <div class="dialogue-box">
                    <strong>对话记录:</strong>
                    {dialogue_html}
                </div>

                <div class="context-grid">
                    <div class="context-item">
                        <div class="label">收到商品</div>
                        <div class="value">{context.get("received_goods", "N/A")}</div>
                    </div>
                    <div class="context-item">
                        <div class="label">商品类型</div>
                        <div class="value">{context.get("goods_type", "N/A")}</div>
                    </div>
                    <div class="context-item">
                        <div class="label">知晓合约</div>
                        <div class="value">{context.get("knows_contract", "N/A")}</div>
                    </div>
                    <div class="context-item">
                        <div class="label">付费</div>
                        <div class="value">{context.get("has_payment", False)}</div>
                    </div>
                    <div class="context-item">
                        <div class="label">被回收</div>
                        <div class="value">{context.get("is_recycled", False)}</div>
                    </div>
                    <div class="context-item">
                        <div class="label">投诉</div>
                        <div class="value">{context.get("is_complaint", False)}</div>
                    </div>
                </div>
            </div>
'''

    html += f'''
        </div>

        <!-- 规则优化建议 -->
        <div class="section">
            <h2><span class="icon">⚙️</span>规则优化建议</h2>

            <div class="suggestion">
                <h4>🔧 根据错误案例，需要优化以下规则：</h4>
                <ul>
                    <li><strong>2246359 - "嗯"处理</strong>：在商品确认环节，"嗯"应识别为中性词，不应触发"营销缺失"</li>
                    <li><strong>2246037 - 回收检测</strong>：增加"被回收/做样板/门店回收"关键词 → 触发"套机套现"</li>
                    <li><strong>2246052 - 流程完整性</strong>：用户说没拿到手机，应继续问宽带/家电，不是直接结束</li>
                    <li><strong>商品类型优先级</strong>：优先检测是否被回收，再判断商品库</li>
                    <li><strong>知晓合约判断</strong>：只有明确说"不知道/不晓得/啥是"才算否定，"嗯/啊/哦"不算</li>
                </ul>
            </div>
        </div>

        <!-- 文件列表 -->
        <div class="section">
            <h2><span class="icon">📁</span>数据文件</h2>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>类别</th>
                        <th>文件路径</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
'''

    # 添加文件列表
    files = results.get("files", {})
    for category, file_list in files.items():
        for filepath in file_list:
            filename = os.path.basename(filepath)
            exists = "✅ 存在" if os.path.exists(filepath) else "❌ 缺失"
            badge_class = "pass" if os.path.exists(filepath) else "fail"
            html += f'''
                    <tr>
                        <td>{category}</td>
                        <td>{filepath}</td>
                        <td><span class="badge {badge_class}">{exists}</span></td>
                    </tr>
'''

    html += '''
                </tbody>
            </table>
        </div>

        <!-- 页脚 -->
        <div class="footer">
            <p>电信橙分期话术与标签优化系统 v{VERSION}</p>
            <p>报告自动生成 | PromptFlow Framework</p>
        </div>
    </div>
</body>
</html>
'''

    return html


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 70)
    print("  电信橙分期话术与标签测试 - 完整版")
    print("=" * 70)

    # 初始化
    classifier = OptimizedTagClassifier()
    results = {
        "error_cases": {
            "total": 0,
            "passed": 0,
            "details": {}
        },
        "batch_test": {
            "total": 0,
            "passed": 0
        },
        "files": {}
    }

    # 1. 查找数据文件
    print("\n[1/5] 扫描数据文件...")
    files = find_dialogue_files()
    results["files"] = files

    for category, file_list in files.items():
        print(f"   {category}: {len(file_list)} 个文件")
        for f in file_list[:3]:  # 只显示前3个
            print(f"      - {os.path.basename(f)}")

    # 2. 测试错误案例
    print("\n[2/5] 测试错误案例...")
    for case in ERROR_CASES:
        classifier.reset()
        classifier.process_dialogue(case["dialogue"])
        actual = classifier.classify()
        context = classifier.get_context()
        passed = actual == case["expected"]

        results["error_cases"]["total"] += 1
        if passed:
            results["error_cases"]["passed"] += 1

        results["error_cases"]["details"][case["id"]] = {
            "expected": case["expected"],
            "actual": actual,
            "passed": passed,
            "context": context,
            "dialogue": case["dialogue"],
            "description": case["description"],
            "reason": case["reason"]
        }

        status = "✅" if passed else "❌"
        print(f"   {status} {case['id']}: 期望={case['expected']}, 实际={actual}")

    # 3. 批量测试真实对话
    print("\n[3/5] 批量测试真实对话...")

    real_files = files.get("真实对话", [])
    if real_files:
        all_dialogues = []
        for filepath in real_files:
            dialogues = parse_dialogue_file(filepath)
            all_dialogues.extend(dialogues)
            print(f"   加载: {os.path.basename(filepath)} - {len(dialogues)} 条记录")

        results["batch_test"]["total"] = len(all_dialogues)
        # TODO: 批量分类测试
    else:
        print("   ⚠️ 未找到对话记录文件，跳过批量测试")

    # 4. 生成报告
    print("\n[4/5] 生成HTML报告...")

    # 确保目录存在
    os.makedirs(REPORT_DIR, exist_ok=True)

    # 生成报告
    report_html = generate_html_report(results)

    report_path = os.path.join(
        REPORT_DIR,
        f"COMPLETE_TEST_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    )

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_html)

    print(f"   ✅ 报告已保存: {report_path}")

    # 5. 打印摘要
    print("\n[5/5] 测试摘要")

    error_stats = results["error_cases"]
    print("\n" + "=" * 70)
    print("  📊 错误案例测试结果")
    print("=" * 70)
    print(f"   总测试: {error_stats['total']}")
    print(f"   通过: {error_stats['passed']}")
    print(f"   失败: {error_stats['total'] - error_stats['passed']}")
    print(f"   通过率: {error_stats['passed']/error_stats['total']*100:.1f}%")

    print("\n" + "=" * 70)
    print("  ⚙️ 优化建议")
    print("=" * 70)
    print("""
   1. 增加"被回收/做样板"检测 → 触发套机套现
   2. "嗯/啊/哦"在商品确认环节 → 视为中性，不触发营销缺失
   3. 用户说没拿到手机 → 应继续问宽带/家电
   4. 明确"不知道/不晓得"才算否定
   5. 优先检测是否被回收，再判断商品库
    """)

    print("\n" + "=" * 70)
    failed = error_stats['total'] - error_stats['passed']
    if failed == 0:
        print("  🎉 所有错误案例已修复！")
    else:
        print(f"  ⚠️  {failed} 个案例需要进一步优化")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
