#!/usr/bin/env python
# -*- coding: utf-8 -*-
print("开始执行...")
print("正在读取Excel文件...")

import zipfile, re, sys

filepath = r'D:\pi-coding-agent\promptflow\data\真实对话\301564-94-公众话术（新系统）-已完成外呼记录_2026-04-15_09-47-38.csv'

try:
    with zipfile.ZipFile(filepath) as z:
        print("ZIP打开成功")
        
        with z.open('xl/sharedStrings.xml') as f:
            content = f.read().decode('utf-8')
        
        strings = re.findall(r'<t[^>]*>([^<]*)</t>', content)
        print(f"字符串数: {len(strings)}")
        print(f"列名(前15个): {strings[:15]}")
        
        with z.open('xl/worksheets/sheet1.xml') as f:
            content = f.read().decode('utf-8')
        
        rows = re.findall(r'<row[^>]*>(.*?)</row>', content, re.DOTALL)
        print(f"总行数: {len(rows)}")
        
        for i, row in enumerate(rows[:5]):
            cells = re.findall(r'<c r="([^"]+)"[^>]*><v>(\d+)</v>', row)
            values = []
            for col, idx in cells:
                idx = int(idx)
                if idx < len(strings):
                    values.append(strings[idx][:50])
                else:
                    values.append(f"ERR:{idx}")
            print(f"\n行{i+1}: {values}")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("\n执行完成!")
