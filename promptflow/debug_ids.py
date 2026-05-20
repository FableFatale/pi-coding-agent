#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试 - 查看实际外呼编号
"""
import zipfile
import re

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
        
        rows = re.findall(r'<row[^>]*>(.*?)</row>', content, re.DOTALL)
        
        first_row = rows[0]
        cells = re.findall(r'<c r="([^"]+)"[^>]*><v>(\d+)</v>', first_row)
        headers = []
        for col, idx in cells:
            idx = int(idx)
            if idx < len(strings):
                headers.append(strings[idx])
        
        for row in rows[1:]:
            cells = re.findall(r'<c r="([^"]+)"[^>]*><v>(\d+)</v>', row)
            record = {}
            for col, idx in cells:
                idx = int(idx)
                col_letter = re.match(r'([A-Z]+)', col)
                if col_letter:
                    col_num = 0
                    for c in col_letter.group(1):
                        col_num = col_num * 26 + (ord(c) - ord('A') + 1)
                    col_num -= 1
                    if col_num < len(headers):
                        record[headers[col_num]] = strings[idx] if idx < len(strings) else ""
            if record:
                records.append(record)
    return records

def parse_problem_file():
    problems = {}
    with open(PROBLEM_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if parts and parts[0].strip().isdigit():
                problems[parts[0].strip()] = parts[0].strip()
    return problems

records = read_xlsx(EXCEL_FILE)
print("Excel中的外呼编号:")
for i, r in enumerate(records):
    print("  " + str(i+1) + ": [" + str(r.get('外呼编号', '')) + "]")

print("\n问题文件中的ID:")
for pid in parse_problem_file().keys():
    print("  [" + pid + "]")
