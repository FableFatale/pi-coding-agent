#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
电信橙分期 - 问题分析与Prompt优化
分析错误标签案例，反推问题根因，优化话术和标签Prompt
"""
import zipfile
import re
import os
from datetime import datetime
from collections import defaultdict

# Excel数据路径
EXCEL_FILES = [
    r'D:\pi-coding-agent\promptflow\data\真实对话\301564-94-公众话术（新系统）-已完成外呼记录_2026-04-15_09-47-38.csv',
    r'D:\pi-coding-agent\promptflow\data\真实对话\301564-94-公众话术（新系统）-已完成外呼记录_2026-04-15_09-50-06.csv'
]

def read_xlsx(filepath):
    """读取xlsx文件"""
    records = []
    with zipfile.ZipFile(filepath, 'r') as z:
        with z.open('xl/sharedStrings.xml') as f:
            content = f.read().decode('utf-8')
        strings = re.findall(r'<t[^>]*>([^<]*)</t>', content)
        
        with z.open('xl/worksheets/sheet1.xml') as f:
            content = f.read().decode('utf-8')
        
        rows = re.findall(r'<row[^>]*>(.*?)</row>', content, re.DOTALL)
        if not rows:
            return []
        
        # 表头
        first_row = rows[0]
        cells = re.findall(r'<c r="([^"]+)"[^>]*><v>(\d+)</v>', first_row)
        headers = [strings[int(idx)] if int(idx) < len(strings) else f"col{i}" for i, (col, idx) in enumerate(cells)]
        
        # 数据行
        for row in rows[1:]:
            cells = re.findall(r'<c r="([^"]+)"[^>]*><v>(\d+)</v>', row)
            record = {}
            for i, (col, idx) in enumerate(cells):
                idx = int(idx)
                record[headers[i] if i < len(headers) else col] = strings[idx] if idx < len(strings) else ""
            
            # 处理行内联字符串
            inline_cells = re.findall(r'<c r="([^"]+)" t="inlineStr"[^>]*><is><t>([^<]*)</t></is>', row)
            for col, val in inline_cells:
                for i, cell_ref in enumerate(re.findall(r'<c r="([^"]+)"', row)):
                    if cell_ref == col and i < len(headers):
                        record[headers[i]] = val
            
            if record:
                records.append(record)
    
    return records

def analyze_record(record):
    """分析单条记录"""
    # 获取关键字段
    dialogue = record.get('聊天记录', '')
    original_tag = record.get('其它标签', '')
    llm_reason = record.get('LLM意向采纳理由', '')
    hangup = record.get('挂机方式', '')
    
    return {
        'dialogue': dialogue,
        'original_tag': original_tag,
        'llm_reason': llm_reason,
        'hangup': hangup
    }

def main():
    print("=" * 70)
    print("  电信橙分期 - 问题分析与Prompt优化")
    print("=" * 70)
    
    all_records = []
    
    for filepath in EXCEL_FILES:
        if os.path.exists(filepath):
            print(f"\n读取: {os.path.basename(filepath)}")
            records = read_xlsx(filepath)
            print(f"  记录数: {len(records)}")
            all_records.extend(records)
    
    if not all_records:
        print("没有读取到数据!")
        return
    
    print(f"\n总记录数: {len(all_records)}")
    print(f"列名: {list(all_records[0].keys())}")
    
    # 分析统计
    tag_stats = defaultdict(int)
    problem_types = defaultdict(list)
    
    print("\n" + "=" * 70)
    print("  数据分析")
    print("=" * 70)
    
    # 标签分布
    for record in all_records:
        tag = record.get('其它标签', '未知')
        tag_stats[tag] += 1
    
    print("\n标签分布:")
    for tag, count in sorted(tag_stats.items(), key=lambda x: -x[1]):
        pct = count / len(all_records) * 100
        print(f"  {tag}: {count} ({pct:.1f}%)")
    
    # 问题分类
    print("\n" + "=" * 70)
    print("  问题案例分析 (前10条)")
    print("=" * 70)
    
    # 筛选有问题倾向的案例
    problem_keywords = ['套机套现', '违规商品', '营销缺失', '未沟通']
    
    for i, record in enumerate(all_records[:30]):
        info = analyze_record(record)
        tag = info['original_tag']
        
        # 只显示重点关注的标签
        if tag in problem_keywords or '套机' in tag or '违规' in tag:
            dialogue = info['dialogue'][:150] if info['dialogue'] else '(无)'
            llm_reason = info['llm_reason'][:100] if info['llm_reason'] else '(无)'
            
            print(f"\n{'='*60}")
            print(f"案例 {i+1}")
            print(f"{'='*60}")
            print(f"【标签】: {tag}")
            print(f"【挂机】: {info['hangup']}")
            print(f"【LLM理由】: {llm_reason}")
            print(f"【对话】: {dialogue}...")
            
            # 分析问题
            print(f"\n【问题分析】:")
            
            # 检查关键词
            dialogue_text = info['dialogue'] or ''
            
            has_phone = '手机' in dialogue_text
            has_know = any(k in dialogue_text for k in ['知道', '清楚', '明白', '晓得'])
            has_dont_know = any(k in dialogue_text for k in ['不知道', '不晓得', '啥是', '啥玩意儿'])
            has_recycled = any(k in dialogue_text for k in ['回收', '样板'])
            has_cash = any(k in dialogue_text for k in ['钱', '折现', '现金'])
            has_no_goods = any(k in dialogue_text for k in ['没拿到', '没收到', '没有', '什么都没'])
            
            print(f"  - 手机提及: {has_phone}")
            print(f"  - 知晓合约: {has_know}")
            print(f"  - 不知晓合约: {has_dont_know}")
            print(f"  - 被回收: {has_recycled}")
            print(f"  - 现金折现: {has_cash}")
            print(f"  - 未收到商品: {has_no_goods}")
            
            # 根因分析
            if tag == '套机套现':
                if has_phone and not has_no_goods:
                    print(f"\n⚠️ 【根因】: 提到手机却判套机套现，可能误判")
                if has_recycled:
                    print(f"\n✓ 【合理】: 手机被回收，判套机套现正确")
            elif tag == '营销缺失':
                if has_know and not has_dont_know:
                    print(f"\n⚠️ 【根因】: 用户表示知晓，却被判营销缺失")
            elif tag == '正常':
                if has_dont_know:
                    print(f"\n⚠️ 【根因】: 用户表示不知晓，却判正常")
    
    # 生成优化建议
    print("\n" + "=" * 70)
    print("  Prompt优化建议")
    print("=" * 70)
    
    suggestions = """
【一、个性标签Prompt优化】

1. 【套机套现判定规则】
   问题：用户提到手机但实际被回收，仍判为套机套现
   优化：
   - 增加"被回收/做样板机"关键词 → 应判定为套机套现
   - 增加"手机被门店收走" → 视为未持有商品
   
2. 【知晓合约判定规则】
   问题：用户回复"嗯"被判为不知晓
   优化：
   - "嗯/嗯嗯"在商品确认环节 → 应视为中性，不触发营销缺失
   - 只有明确说"不知道/不晓得/啥是" → 才触发营销缺失
   
3. 【流程完整性】
   问题：用户说没拿到手机，没继续问宽带/家电
   优化：
   - 在话术prompt中明确：没拿到手机 → 继续问宽带
   - 没拿到宽带 → 继续问家电
   - 所有品类都问完才能结束

【二、话术Prompt优化】

1. 【节点流转】
   - L节点(手机)用户说"没有" → 应跳转到M节点(宽带)
   - M节点(宽带)用户说"没有" → 应跳转到O节点(家电)
   - O节点(家电)用户说"没有" → 应跳转到P节点(折现)
   
2. 【二次确认】
   - 用户说"嗯" → 应二次确认："请问您清楚橙分期业务吗？"
   - 不能直接判定为不知道

3. 【特殊场景】
   - 用户说"手机被回收" → 直接记录套机套现
   - 用户说"什么也没收到" → 继续问是否收到现金
"""
    print(suggestions)
    
    # 保存完整报告
    report_path = r'D:\pi-coding-agent\promptflow\reports\ANALYSIS_REPORT.txt'
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("电信橙分期问题分析与Prompt优化报告\n")
        f.write("=" * 60 + "\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"总记录数: {len(all_records)}\n\n")
        
        f.write("标签分布:\n")
        for tag, count in sorted(tag_stats.items(), key=lambda x: -x[1]):
            pct = count / len(all_records) * 100
            f.write(f"  {tag}: {count} ({pct:.1f}%)\n")
        
        f.write("\n" + suggestions)
    
    print(f"\n\n报告已保存: {report_path}")

if __name__ == '__main__':
    main()
