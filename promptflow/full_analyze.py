#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
电信橙分期 - 完整问题分析与Prompt优化
"""
import zipfile
import re
import os
from datetime import datetime
from collections import defaultdict

EXCEL_FILES = [
    r'D:\pi-coding-agent\promptflow\data\真实对话\301564-94-公众话术（新系统）-已完成外呼记录_2026-04-15_09-47-38.csv',
    r'D:\pi-coding-agent\promptflow\data\真实对话\301564-94-公众话术（新系统）-已完成外呼记录_2026-04-15_09-50-06.csv'
]

def read_xlsx(filepath):
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
        
        first_row = rows[0]
        cells = re.findall(r'<c r="([^"]+)"[^>]*><v>(\d+)</v>', first_row)
        headers = [strings[int(idx)] if int(idx) < len(strings) else f"col{i}" for i, (col, idx) in enumerate(cells)]
        
        for row in rows[1:]:
            cells = re.findall(r'<c r="([^"]+)"[^>]*><v>(\d+)</v>', row)
            record = {}
            for i, (col, idx) in enumerate(cells):
                idx = int(idx)
                record[headers[i] if i < len(headers) else col] = strings[idx] if idx < len(strings) else ""
            
            inline_cells = re.findall(r'<c r="([^"]+)" t="inlineStr"[^>]*><is><t>([^<]*)</t></is>', row)
            for col, val in inline_cells:
                for i, cell_ref in enumerate(re.findall(r'<c r="([^"]+)"', row)):
                    if cell_ref == col and i < len(headers):
                        record[headers[i]] = val
            
            if record:
                records.append(record)
    
    return records

def main():
    print("=" * 80)
    print("  电信橙分期 - 完整问题分析与Prompt优化")
    print("=" * 80)
    
    all_records = []
    for filepath in EXCEL_FILES:
        if os.path.exists(filepath):
            print("\n读取: " + os.path.basename(filepath))
            records = read_xlsx(filepath)
            print("  记录数: " + str(len(records)))
            all_records.extend(records)
    
    if not all_records:
        print("没有数据!")
        return
    
    print("\n总记录数: " + str(len(all_records)))
    
    # 显示第一条数据的结构
    print("\n数据结构示例:")
    for k, v in all_records[0].items():
        print("  " + k + ": " + str(v)[:50])
    
    # 统计
    tag_stats = defaultdict(int)
    records_by_tag = defaultdict(list)
    
    for record in all_records:
        tag = record.get('其它标签', '未知')
        tag_stats[tag] += 1
        records_by_tag[tag].append(record)
    
    print("\n" + "=" * 80)
    print("  一、标签分布统计")
    print("=" * 80)
    for tag, count in sorted(tag_stats.items(), key=lambda x: -x[1]):
        pct = count / len(all_records) * 100
        print("  " + tag + ": " + str(count) + "条 (" + str(round(pct, 1)) + "%)")
    
    # 重点分析正常标签
    print("\n" + "=" * 80)
    print("  二、正常标签案例分析 (检查是否有误判)")
    print("=" * 80)
    
    normal_records = records_by_tag.get('正常', [])
    print("\n正常标签共 " + str(len(normal_records)) + " 条\n")
    
    problem_normal = []
    for i, record in enumerate(normal_records[:20]):
        dialogue = record.get('聊天记录', '')
        llm_reason = record.get('LLM意向采纳理由', '')
        
        text = dialogue or ''
        has_dont_know = any(k in text for k in ['不知道', '不晓得', '啥是', '没办过'])
        has_complaint = any(k in text for k in ['投诉', '骗', '被骗'])
        has_no = '没有' in text or '没' in text
        
        is_problem = has_dont_know or has_complaint
        
        if is_problem:
            problem_normal.append((i, record, dialogue, llm_reason, has_dont_know, has_complaint))
            print("【问题案例 " + str(len(problem_normal)) + "】")
            print("  对话: " + text[:100] + "...")
            print("  LLM理由: " + (llm_reason[:80] if llm_reason else '无'))
            if has_dont_know:
                print("  警告: 检测到用户表示不知晓")
            if has_complaint:
                print("  警告: 检测到用户投诉")
            print("")
    
    # 分析非正常标签
    print("\n" + "=" * 80)
    print("  三、非正常标签案例分析")
    print("=" * 80)
    
    other_tags = [t for t in tag_stats.keys() if t != '正常']
    for tag in other_tags:
        records = records_by_tag.get(tag, [])
        print("\n【" + tag + "】共 " + str(len(records)) + " 条")
        
        for i, record in enumerate(records[:5]):
            dialogue = record.get('聊天记录', '')
            llm_reason = record.get('LLM意向采纳理由', '')
            hangup = record.get('挂机方式', '')
            
            print("\n  案例" + str(i+1) + ":")
            print("    对话: " + dialogue[:80] + "...")
            print("    挂机: " + hangup)
            print("    LLM理由: " + (llm_reason[:60] if llm_reason else '无'))
    
    # 问题根因分析
    print("\n" + "=" * 80)
    print("  四、问题根因分析")
    print("=" * 80)
    
    print("""
根据数据分析，发现以下问题：

1. 【正常标签误判】
   问题：用户说"不知道/不晓得"却判为"正常"
   原因：LLM只看到用户拿到商品，忽略了"不知道"这个关键信息
   建议：明确规则"收到商品 + 不知晓合约 = 营销缺失"

2. 【套机套现判定】
   问题：需要确认用户是否真的没收到商品
   关键：区分"没拿到"和"被回收"
   
3. 【流程完整性】
   问题：话术流程应该继续追问，而不是直接结束
   建议：没拿到手机 -> 问宽带 -> 问家电 -> 问折现
""")
    
    # 优化后的Prompt
    print("\n" + "=" * 80)
    print("  五、优化后的个性标签Prompt")
    print("=" * 80)
    
    print("""
# 个性标签判定Prompt - 优化版

## 判定规则

### 1. 套机套现 (优先级最高)
触发条件：
- 未收到任何商品(手机/家电/宽带/拍照)
- 未收到现金折现
- 商品被门店回收/做样板机

### 2. 违规商品
触发条件：
- 收到耳机/充电宝/空气炸锅/电视等违规商品

### 3. 营销缺失
触发条件：
- 收到商品 + 用户表示"不知道/不晓得/啥是/没办过"
- 收到商品 + 用户投诉/被骗

### 4. 正常
触发条件：
- 收到商品 + 用户知晓合约
- 用户回复"嗯/啊/哦"在商品确认后

### 5. 未沟通
触发条件：
- 零互动/语气词回复
- 非本人/打错

## 关键修复
1. "不知道/不晓得/啥是" -> 必须触发营销缺失
2. "嗯/啊/哦" -> 视为中性，不是明确否定
3. "手机被回收" -> 套机套现
""")
    
    # 话术Prompt
    print("\n" + "=" * 80)
    print("  六、优化后的话术Prompt关键节点")
    print("=" * 80)
    
    print("""
## 关键节点修复

### L节点(手机确认)
- 用户说"没有/没拿到" -> 继续问M节点(宽带)
- 用户说"手机被回收" -> 记录套机套现

### M节点(宽带确认)  
- 用户说"没有/没装" -> 继续问O节点(家电)
- 用户说"有/装了" -> 进入N节点(分期确认)

### N节点(分期确认)
- 用户说"不知道/不晓得" -> 进入I节点(解释)
- 用户说"知道/嗯/清楚" -> 进入H节点(礼貌挂机)

### 核心原则
1. 任何环节用户说"不知道" -> 必须解释后再确认
2. 解释后用户仍模糊 -> I节点(分期解释挂机)
3. 解释后用户明确知道 -> H节点(礼貌挂机)
""")
    
    # 保存报告
    report_path = r'D:\pi-coding-agent\promptflow\reports\完整分析报告.md'
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 电信橙分期问题分析与Prompt优化报告\n\n")
        f.write("生成时间: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n")
        
        f.write("## 一、数据概况\n\n")
        f.write("- 总记录数: " + str(len(all_records)) + "\n")
        f.write("- 文件数: " + str(len(EXCEL_FILES)) + "\n\n")
        
        f.write("## 二、标签分布\n\n")
        for tag, count in sorted(tag_stats.items(), key=lambda x: -x[1]):
            pct = count / len(all_records) * 100
            f.write("- " + tag + ": " + str(count) + "条 (" + str(round(pct, 1)) + "%)\n")
        
        f.write("\n## 三、问题案例\n\n")
        for i, (idx, record, dialogue, llm_reason, has_dont_know, has_complaint) in enumerate(problem_normal):
            f.write("### 案例" + str(i+1) + "\n\n")
            f.write("- 对话: " + dialogue[:200] + "\n\n")
            f.write("- LLM理由: " + llm_reason + "\n\n")
            if has_dont_know:
                f.write("- 问题: 用户表示不知晓合约\n\n")
            if has_complaint:
                f.write("- 问题: 用户投诉\n\n")
        
        f.write("\n## 四、Prompt优化建议\n\n")
        f.write("见上方控制台输出的完整内容\n")
    
    print("\n\n报告已保存: " + report_path)

if __name__ == '__main__':
    main()
