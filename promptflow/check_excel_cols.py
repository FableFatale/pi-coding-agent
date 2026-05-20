#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查Excel列结构
"""
import zipfile
import re
import os

# 尝试找到Excel文件
data_dir = r'D:\pi-coding-agent\promptflow\data\真实对话'

print("查找Excel文件...")
print("目录: " + data_dir)

# 列出目录下所有文件
for f in os.listdir(data_dir):
    filepath = os.path.join(data_dir, f)
    if os.path.isfile(filepath):
        print("找到文件: " + f)

# 尝试读取
xlsx_file = os.path.join(data_dir, '对话记录.xlsx')
if not os.path.exists(xlsx_file):
    xlsx_file = os.path.join(data_dir, '1.xlsx')
if not os.path.exists(xlsx_file):
    # 找第一个xlsx文件
    for f in os.listdir(data_dir):
        if f.endswith('.xlsx') or f.endswith('.csv'):
            xlsx_file = os.path.join(data_dir, f)
            break

print("\n尝试读取: " + xlsx_file)

if not os.path.exists(xlsx_file):
    print("文件不存在!")
else:
    try:
        with zipfile.ZipFile(xlsx_file, 'r') as z:
            # 读取共享字符串
            with z.open('xl/sharedStrings.xml') as f:
                content = f.read().decode('utf-8')
            strings = re.findall(r'<t[^>]*>([^<]*)</t>', content)
            
            print("\n前20个字符串(可能是列名):")
            for i, s in enumerate(strings[:20]):
                print("  " + str(i) + ": " + s)
            
            # 读取工作表
            with z.open('xl/worksheets/sheet1.xml') as f:
                content = f.read().decode('utf-8')
            
            rows = re.findall(r'<row[^>]*>(.*?)</row>', content, re.DOTALL)
            if rows:
                print("\n第一行(列名):")
                first_row = rows[0]
                cells = re.findall(r'<c r="([^"]+)"[^>]*><v>(\d+)</v>', first_row)
                for col, idx in cells:
                    idx = int(idx)
                    if idx < len(strings):
                        print("  " + col + ": " + strings[idx])
                
                # 读取前3行数据
                print("\n前3行数据:")
                for row_idx, row in enumerate(rows[1:4]):
                    cells = re.findall(r'<c r="([^"]+)"[^>]*><v>(\d+)</v>', row)
                    row_data = {}
                    for col, idx in cells:
                        idx = int(idx)
                        if idx < len(strings):
                            row_data[col] = strings[idx]
                    print("\n  Row " + str(row_idx+1) + ":")
                    for k, v in row_data.items():
                        print("    " + k + ": " + str(v)[:50])
    except Exception as e:
        print("错误: " + str(e))
        import traceback
        traceback.print_exc()
