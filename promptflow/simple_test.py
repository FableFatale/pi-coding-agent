# -*- coding: utf-8 -*-
"""检查Excel文件"""
import zipfile, re

filepath = r'D:\pi-coding-agent\promptflow\data\真实对话\301564-94-公众话术（新系统）-已完成外呼记录_2026-04-15_09-47-38.csv'

with zipfile.ZipFile(filepath) as z:
    # 共享字符串
    with z.open('xl/sharedStrings.xml') as f:
        content = f.read().decode('utf-8')
    strings = re.findall(r'<t[^>]*>([^<]*)</t>', content)
    print(f"字符串数: {len(strings)}")
    print(f"列名: {strings[:15]}")
    
    # 工作表
    with z.open('xl/worksheets/sheet1.xml') as f:
        content = f.read().decode('utf-8')
    
    # 找到前几行
    rows = re.findall(r'<row[^>]*>(.*?)</row>', content, re.DOTALL)
    print(f"\n总行数: {len(rows)}")
    
    for i, row in enumerate(rows[:3]):
        cells = re.findall(r'<c r="([^"]+)"[^>]*><v>(\d+)</v>', row)
        values = [strings[int(idx)] if int(idx) < len(strings) else f"idx:{idx}" for col, idx in cells]
        print(f"\n行{i+1}: {values}")
