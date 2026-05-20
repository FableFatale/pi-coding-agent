#!/usr/bin/env python
# -*- coding: utf-8 -*-
import zipfile
import re
import os

EXCEL_FILE = r'D:\pi-coding-agent\promptflow\data\真实对话\对话记录.xlsx'

with zipfile.ZipFile(EXCEL_FILE, 'r') as z:
    with z.open('xl/worksheets/sheet1.xml') as f:
        content = f.read().decode('utf-8')

print("XML内容前1000字符:")
print(content[:1000])

print("\n\n尝试匹配单元格:")
cells = re.findall(r'<c r="([^"]+)"[^>]*>(.*?)</c>', content, re.DOTALL)
print(f"找到 {len(cells)} 个单元格")
for c in cells[:10]:
    print(c)

print("\n\n尝试另一种匹配:")
cells2 = re.findall(r'<c[^>]+r="([^"]+)"[^>]*><v>(\d+)</v>', content)
print(f"找到 {len(cells2)} 个单元格")
for c in cells2[:10]:
    print(c)
