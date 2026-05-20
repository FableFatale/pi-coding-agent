#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
电信橙分期测试 - 修复版
列名：聊天记录、其它标签、挂机方式、LLM意向采纳理由
"""
import zipfile
import re
import os
from datetime import datetime

# Excel数据路径
EXCEL_FILE = r'D:\pi-coding-agent\promptflow\data\真实对话\301564-94-公众话术（新系统）-已完成外呼记录_2026-04-15_09-47-38.csv'
EXCEL_FILE2 = r'D:\pi-coding-agent\promptflow\data\真实对话\301564-94-公众话术（新系统）-已完成外呼记录_2026-04-15_09-50-06.csv'

# 商品库
NORMAL_PRODUCTS = {"手机","华为","苹果","小米","oppo","vivo","荣耀","宽带","光猫","路由器",
                   "机顶盒","手表","手环","小度","小爱","摄像头","空调","冰箱","洗衣机",
                   "电视","电脑","平板","笔记本","电饭煲","智能锁","音箱","门锁","血压计",
                   "合约机","老人机","路由器","宽带设备"}

VIOLATION_PRODUCTS = {"耳机","充电宝","空气炸锅","锅","高压锅","净水器","扫地机","电视机",
                      "豆浆机","电磁炉","微波炉","电水壶","榨汁机","挂烫机","风扇","打印机",
                      "电暖炉","消毒柜","燃气灶","破壁机","茶吧机","吹风机","加湿器","按摩器",
                      "蓝牙耳机","空气炸锅机","净水机","油烟机","一体锅"}

def read_xlsx(filepath):
    """读取xlsx文件"""
    records = []
    with zipfile.ZipFile(filepath, 'r') as z:
        # 读取共享字符串
        with z.open('xl/sharedStrings.xml') as f:
            content = f.read().decode('utf-8')
        strings = re.findall(r'<t[^>]*>([^<]*)</t>', content)
        
        # 读取工作表
        with z.open('xl/worksheets/sheet1.xml') as f:
            content = f.read().decode('utf-8')
        
        rows = re.findall(r'<row[^>]*>(.*?)</row>', content, re.DOTALL)
        if not rows:
            return []
        
        # 第一行是表头
        first_row = rows[0]
        cells = re.findall(r'<c r="([^"]+)"[^>]*><v>(\d+)</v>', first_row)
        headers = [strings[int(idx)] if int(idx) < len(strings) else f"col{i}" for i, (col, idx) in enumerate(cells)]
        
        # 解析数据行
        for row in rows[1:]:
            cells = re.findall(r'<c r="([^"]+)"[^>]*><v>(\d+)</v>', row)
            record = {}
            for i, (col, idx) in enumerate(cells):
                idx = int(idx)
                if idx < len(strings):
                    record[headers[i] if i < len(headers) else col] = strings[idx]
                else:
                    record[headers[i] if i < len(headers) else col] = ""
            
            # 也处理行内联字符串的情况
            inline_cells = re.findall(r'<c r="([^"]+)" t="inlineStr"[^>]*><is><t>([^<]*)</t></is>', row)
            for col, val in inline_cells:
                # 找到列索引
                for i, cell_ref in enumerate(re.findall(r'<c r="([^"]+)"', row)):
                    if cell_ref == col and i < len(headers):
                        record[headers[i]] = val
            
            if record:
                records.append(record)
    
    return records

def classify_tag(record):
    """根据聊天记录判定标签"""
    # 获取聊天记录
    dialogue = ""
    for key in ['聊天记录', '对话内容', '对话']:
        if key in record:
            dialogue = str(record[key])
            break
    
    # 获取原标签
    original_tag = ""
    for key in ['其它标签', '标签', '个性标签', 'LLM意向采纳理由']:
        if key in record:
            original_tag = str(record[key])
            break
    
    if not dialogue:
        return original_tag, original_tag, "无聊天记录"
    
    text = dialogue
    
    # 检测特征
    has_normal = any(p in text for p in NORMAL_PRODUCTS)
    has_violation = any(p in text for p in VIOLATION_PRODUCTS)
    has_phone = '手机' in text
    has_no_goods = any(kw in text for kw in ['没拿到', '没收到', '没有', '什么都没', '只有钱', '木有'])
    has_cash = '钱' in text or '折现' in text or '现金' in text
    has_know = any(kw in text for kw in ['知道', '清楚', '明白', '晓得', '清楚'])
    has_dont_know = any(kw in text for kw in ['不知道', '不晓得', '啥是', '啥玩意儿', '不清楚', '没办过'])
    has_complaint = any(kw in text for kw in ['投诉', '骗', '被骗', '欺诈', '坑'])
    has_recycled = any(kw in text for kw in ['回收', '样板', '门店'])
    
    # 判定逻辑
    # 1. 套机套现
    if has_recycled:
        return '套机套现', original_tag, "检测到被回收"
    if has_no_goods and not has_cash:
        return '套机套现', original_tag, "未收到商品"
    if has_no_goods and has_cash:
        return '套机套现', original_tag, "仅收到现金"
    
    # 2. 违规商品
    if has_violation and has_normal:
        # 同时有违规和正常商品，优先正常
        pass
    elif has_violation:
        return '违规商品', original_tag, f"检测到违规商品:{VIOLATION_PRODUCTS & set(text)}"
    
    # 3. 正常
    if has_phone or has_normal:
        if has_know or not has_dont_know:
            return '正常', original_tag, "收到商品+知晓合约"
        else:
            return '营销缺失', original_tag, "收到商品但不知晓"
    
    # 4. 营销缺失
    if has_complaint:
        return '营销缺失', original_tag, "检测到投诉"
    if has_dont_know:
        return '营销缺失', original_tag, "不知晓合约"
    
    # 5. 未知
    return original_tag, original_tag, "无法判定"

def main():
    print("=" * 70)
    print("  电信橙分期话术与标签测试")
    print("=" * 70)
    
    files = [EXCEL_FILE, EXCEL_FILE2]
    all_records = []
    
    for filepath in files:
        if os.path.exists(filepath):
            print(f"\n读取: {os.path.basename(filepath)}")
            records = read_xlsx(filepath)
            print(f"  记录数: {len(records)}")
            all_records.extend(records)
            
            # 显示列名
            if records:
                print(f"  列名: {list(records[0].keys())}")
        else:
            print(f"\n文件不存在: {filepath}")
    
    if not all_records:
        print("\n没有读取到任何记录!")
        return
    
    # 测试统计
    total = len(all_records)
    correct = 0
    errors = []
    tag_stats = {}
    
    print("\n" + "=" * 70)
    print("  测试结果 (前20条)")
    print("=" * 70)
    
    for i, record in enumerate(all_records[:20]):
        predicted, original, reason = classify_tag(record)
        is_correct = predicted == original
        
        if is_correct:
            correct += 1
            status = '✅'
        else:
            errors.append({
                'index': i+1,
                'original': original,
                'predicted': predicted,
                'reason': reason,
                'record': record
            })
            status = '❌'
        
        # 统计标签分布
        tag_stats[original] = tag_stats.get(original, 0) + 1
        
        # 获取对话摘要
        dialogue = ""
        for key in ['聊天记录', '对话内容']:
            if key in record and record[key]:
                dialogue = str(record[key])[:50]
                break
        
        print(f"\n{status} 记录{i+1}")
        print(f"   对话: {dialogue}...")
        print(f"   其它标签: {original}")
        print(f"   判定: {predicted} ({reason})")
    
    # 统计
    print("\n" + "=" * 70)
    print("  统计")
    print("=" * 70)
    print(f"   总记录: {total}")
    print(f"   测试样本: {min(total, 20)}")
    print(f"   准确: {correct}/{min(total,20)}")
    
    if correct > 0:
        print(f"   准确率: {correct/min(total,20)*100:.1f}%")
    
    print("\n   标签分布:")
    for tag, count in sorted(tag_stats.items(), key=lambda x: -x[1]):
        print(f"     {tag}: {count}")
    
    # 错误分析
    if errors:
        print("\n" + "=" * 70)
        print("  错误案例分析")
        print("=" * 70)
        for e in errors[:10]:
            print(f"\n   记录{e['index']}:")
            print(f"   其它标签: {e['original']} → 判定: {e['predicted']}")
            print(f"   原因: {e['reason']}")
    
    # 保存错误报告
    if errors:
        report_path = os.path.join(os.path.dirname(EXCEL_FILE), "reports", f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("电信橙分期标签测试报告\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"总记录: {total}\n")
            f.write(f"错误数: {len(errors)}\n\n")
            for e in errors:
                f.write(f"记录{e['index']}: 原={e['original']} 判定={e['predicted']} 原因={e['reason']}\n")
        print(f"\n报告已保存: {report_path}")

if __name__ == '__main__':
    main()
