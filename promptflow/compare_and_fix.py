#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
电信橙分期 - 对比分析报告
"""
import zipfile
import re
import os
from datetime import datetime

PROBLEM_FILE = r'D:\pi-coding-agent\promptflow\data\真实对话\问题.txt'
EXCEL_FILE = r'D:\pi-coding-agent\promptflow\data\真实对话\对话记录.xlsx'

def read_xlsx(filepath):
    records = []
    with zipfile.ZipFile(filepath, 'r') as z:
        with z.open('xl/sharedStrings.xml') as f:
            content = f.read().decode('utf-8')
        strings = re.findall(r'<t[^>]*>([^<]*)</t>', content)
        
        with z.open('xl/worksheets/sheet1.xml') as f:
            content = f.read().decode('utf-8')
        
        all_cells = re.findall(r'<c r="([^"]+)"([^>]*)>(.*?)</c>', content, re.DOTALL)
        
        rows_data = {}
        for cell_ref, attrs, cell_content in all_cells:
            row_num = int(re.search(r'\d+', cell_ref).group())
            if row_num not in rows_data:
                rows_data[row_num] = {}
            
            col_letter = re.match(r'([A-Z]+)', cell_ref).group(1)
            col_num = 0
            for c in col_letter:
                col_num = col_num * 26 + (ord(c) - ord('A') + 1)
            
            v_match = re.search(r'<v>(\d+)</v>', cell_content)
            if v_match:
                val = v_match.group(1)
                if 't="s"' in attrs:
                    idx = int(val)
                    if idx < len(strings):
                        rows_data[row_num][col_num] = strings[idx]
                    else:
                        rows_data[row_num][col_num] = val
                else:
                    rows_data[row_num][col_num] = val
        
        if 1 in rows_data:
            headers = rows_data[1]
            header_list = [headers.get(i, f"col{i}") for i in range(1, max(headers.keys())+1)]
        else:
            header_list = ["col1", "col2", "col3", "col4"]
        
        for row_num in sorted(rows_data.keys()):
            if row_num == 1:
                continue
            row_data = rows_data[row_num]
            record = {}
            for col_num, value in row_data.items():
                if col_num <= len(header_list):
                    record[header_list[col_num-1]] = value
                else:
                    record[f"col{col_num}"] = value
            if record:
                records.append(record)
    
    return records

def parse_problem_file():
    problems = {}
    with open(PROBLEM_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if i < 2:
            continue
        
        line = line.strip()
        if not line:
            continue
        
        line = line.lstrip('|')
        parts = line.split('|')
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) >= 2:
            first_part = parts[0]
            correct_tag = parts[1]
            
            id_parts = first_part.split('\t')
            id_parts = [p.strip() for p in id_parts if p.strip()]
            
            record_id = ''
            description = ''
            for p in id_parts:
                if p.isdigit():
                    record_id = p
                else:
                    description = p
                    break
            
            if record_id and correct_tag:
                problems[record_id] = {
                    'correct_tag': correct_tag,
                    'description': description
                }
    
    return problems

def analyze_dialogue(dialogue):
    """分析对话中的关键信息"""
    text = dialogue or ''
    
    analysis = {
        'has_phone': '手机' in text,
        'has_broadband': any(k in text for k in ['宽带', '光猫', '路由器']),
        'has_know': any(k in text for k in ['知道', '清楚', '明白', '晓得']),
        'has_dont_know': any(k in text for k in ['不知道', '不晓得', '啥是', '没办过']),
        'has_recycled': any(k in text for k in ['回收', '样板', '回收入']),
        'has_cash': any(k in text for k in ['钱', '折现', '现金']),
        'has_no_goods': any(k in text for k in ['没有', '没拿到', '没收到', '什么都没']),
        'has_complaint': any(k in text for k in ['投诉', '骗', '被骗']),
        'has_filler': any(k in text for k in ['嗯', '啊', '哦', '嗯嗯']),
    }
    
    return analysis

def main():
    print("=" * 80)
    print("  电信橙分期 - 问题对比分析报告")
    print("=" * 80)
    
    problems = parse_problem_file()
    records = read_xlsx(EXCEL_FILE)
    
    print(f"\n问题数量: {len(problems)}")
    print(f"Excel记录数: {len(records)}\n")
    
    error_records = []
    matched = 0
    
    print("=" * 80)
    print("  一、对比分析结果")
    print("=" * 80)
    
    for pid, info in problems.items():
        record = None
        for r in records:
            if str(r.get('外呼编号', '')).strip() == pid.strip():
                record = r
                break
        
        if record:
            matched += 1
            system_tag = str(record.get('个性标签', '')).strip()
            correct_tag = info['correct_tag']
            dialogue = str(record.get('聊天记录', '')).strip()
            hangup = str(record.get('挂机方式', '')).strip()
            
            is_correct = system_tag == correct_tag
            
            status = "[正确]" if is_correct else "[错误]"
            
            print(f"\n{status} ID={pid}")
            print(f"  系统判定: {system_tag}")
            print(f"  正确答案: {correct_tag}")
            print(f"  挂机方式: {hangup}")
            print(f"  问题: {info['description'][:50]}...")
            
            # 对话关键词分析
            analysis = analyze_dialogue(dialogue)
            print(f"  对话分析:")
            if analysis['has_phone']: print(f"    + 提到手机")
            if analysis['has_broadband']: print(f"    + 提到宽带/光猫/路由器")
            if analysis['has_know']: print(f"    + 表示知晓(知道/清楚)")
            if analysis['has_dont_know']: print(f"    + 表示不知晓(不知道/不晓得)")
            if analysis['has_recycled']: print(f"    + 被回收/做样板")
            if analysis['has_cash']: print(f"    + 提到钱/折现")
            if analysis['has_no_goods']: print(f"    + 表示没有商品")
            if analysis['has_complaint']: print(f"    + 投诉/被骗")
            if analysis['has_filler']: print(f"    + 语气词(嗯/啊/哦)")
            
            if not is_correct:
                error_records.append({
                    'id': pid,
                    'system': system_tag,
                    'correct': correct_tag,
                    'dialogue': dialogue,
                    'desc': info['description'],
                    'analysis': analysis
                })
    
    # 统计
    print("\n" + "=" * 80)
    print("  二、统计汇总")
    print("=" * 80)
    print(f"  问题总数: {len(problems)}")
    print(f"  匹配数: {matched}")
    print(f"  正确判定: {matched - len(error_records)}")
    print(f"  错误判定: {len(error_records)}")
    
    # 错误分类
    if error_records:
        print("\n" + "=" * 80)
        print("  三、错误分类统计")
        print("=" * 80)
        
        error_by_correct = {}
        for err in error_records:
            correct = err['correct']
            if correct not in error_by_correct:
                error_by_correct[correct] = []
            error_by_correct[correct].append(err)
        
        for tag, cases in error_by_correct.items():
            print(f"\n  【{tag}】类型错误: {len(cases)}个")
            for case in cases:
                print(f"    - ID={case['id']}: 系统判{case['system']}")
    
    # 根因分析
    print("\n" + "=" * 80)
    print("  四、根因分析")
    print("=" * 80)
    
    reasons = {
        'should_be_normal': [],      # 应该判正常但判错了
        'should_be_taoji': [],       # 应该判套机套现但判错了
        'should_be_yingxiao': [],    # 应该判营销缺失但判错了
        'flow_error': []             # 流程错误
    }
    
    for err in error_records:
        correct = err['correct']
        system = err['system']
        analysis = err['analysis']
        
        if correct == '正常':
            if 'has_no_goods' in analysis and analysis['has_no_goods'] and 'has_know' in analysis and analysis['has_know']:
                reasons['should_be_normal'].append(err)
            else:
                reasons['should_be_normal'].append(err)
        elif correct == '套机套现':
            reasons['should_be_taoji'].append(err)
        elif correct == '营销缺失':
            reasons['should_be_yingxiao'].append(err)
        
        if '无' in correct or '流程' in err['desc']:
            reasons['flow_error'].append(err)
    
    if reasons['should_be_normal']:
        print("\n  1. 应判【正常】但判错的案例:")
        for err in reasons['should_be_normal']:
            print(f"     ID={err['id']}: 系统判{err['system']}")
            if err['analysis']['has_know']:
                print(f"       → 原因: 用户表示知晓，但被判其他标签")
    
    if reasons['should_be_taoji']:
        print("\n  2. 应判【套机套现】但判错的案例:")
        for err in reasons['should_be_taoji']:
            print(f"     ID={err['id']}: 系统判{err['system']}")
            if err['analysis']['has_recycled']:
                print(f"       → 原因: 用户手机被回收/做样板，应判套机套现")
            if err['analysis']['has_no_goods']:
                print(f"       → 原因: 用户表示未收到商品")
    
    if reasons['should_be_yingxiao']:
        print("\n  3. 应判【营销缺失】但判错的案例:")
        for err in reasons['should_be_yingxiao']:
            print(f"     ID={err['id']}: 系统判{err['system']}")
            if err['analysis']['has_dont_know']:
                print(f"       → 原因: 用户表示不知晓合约")
    
    if reasons['flow_error']:
        print("\n  4. 【流程错误】:")
        for err in reasons['flow_error']:
            print(f"     ID={err['id']}: {err['desc'][:50]}")
    
    # 优化建议
    print("\n" + "=" * 80)
    print("  五、Prompt优化建议")
    print("=" * 80)
    
    suggestions = """
【一、个性标签Prompt优化】

1. 【修复"回收/样板"检测】
   问题: 用户说"手机被回收做样板"，应判套机套现
   修改: 增加关键词"回收"、"样板"、"回收入"
   示例: "手机被门店回收"、"要做样板机"
   
2. 【修复"不知道"检测】
   问题: 用户说"不知道/不晓得"，但系统判了正常
   修改: 明确"不知道/不晓得/啥是/没办过"必须触发营销缺失
   关键词库:
   - 不知晓: ["不知道", "不晓得", "不晓滴", "啥是", "啥玩意儿", "没办过"]
   
3. 【修复"语气词"处理】
   问题: 用户只回复"嗯/啊/哦"，被误判
   修改: "嗯/啊/哦"在分期确认环节应视为中性
   区分: 
   - 商品确认环节: "嗯"=中性
   - 明确问是否知道: "嗯"=确认
   
4. 【修复"没有"检测】
   问题: 用户说"没有"但没说具体什么没有
   修改: 需要根据上下文判断
   - 说"没有"后又补充具体商品 -> 以补充为准
   - 说"什么都没有" -> 直接套机套现
   
5. 【修复"知道"的判断】
   问题: 用户说"知道"但被判了其他标签
   修改: "知道/清楚/明白/晓得"视为知晓合约
   注意: 需要区分"知道分期"和"知道办理过业务"

【二、话术Prompt优化】

1. 【流程完整性】
   问题: 用户说"没有拿到手机"，流程直接结束
   修改: 没拿到手机 -> 继续问宽带 -> 继续问家电 -> 继续问折现
   
2. 【分期确认二次确认】
   问题: 用户说"不知道"直接结束
   修改: 必须解释橙分期后再次确认
   
3. 【回收场景识别】
   问题: 用户说"手机被回收"，未识别
   修改: "被回收"、"做样板"、"回收入" -> 记录套机套现

【三、规则调整】

1. 标签判定优先级:
   (1) 套机套现: 未收到商品 + 无付费
   (2) 违规商品: 收到违规商品库商品
   (3) 营销缺失: 收到商品 + 不知晓合约
   (4) 正常: 收到商品 + 知晓合约
   (5) 未沟通: 零互动/非本人

2. 关键修复:
   - "手机被回收" → 套机套现
   - "不知道/不晓得" → 营销缺失
   - "嗯/啊/哦" → 中性(需结合上下文)
   - "没有+商品" → 根据商品判断
"""
    print(suggestions)
    
    # 保存报告
    report_path = r'D:\pi-coding-agent\promptflow\reports\问题对比分析完整报告.md'
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 电信橙分期问题对比分析报告\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 统计\n\n")
        f.write(f"- 问题总数: {len(problems)}\n")
        f.write(f"- 匹配数: {matched}\n")
        f.write(f"- 正确: {matched - len(error_records)}\n")
        f.write(f"- 错误: {len(error_records)}\n\n")
        
        f.write("## 错误案例\n\n")
        for err in error_records:
            f.write(f"### ID={err['id']}\n\n")
            f.write(f"- 系统判定: {err['system']}\n")
            f.write(f"- 正确答案: {err['correct']}\n")
            f.write(f"- 问题描述: {err['desc']}\n\n")
            f.write(f"- 对话: {err['dialogue'][:300]}\n\n")
        
        f.write("## 优化建议\n\n")
        f.write(suggestions)
    
    print("\n" + "=" * 80)
    print(f"报告已保存: {report_path}")
    print("=" * 80)

main()
