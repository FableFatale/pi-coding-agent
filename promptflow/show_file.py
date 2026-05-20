# -*- coding: utf-8 -*-
with open(r'D:\pi-coding-agent\promptflow\data\真实对话\问题.txt', 'r', encoding='utf-8') as f:
    content = f.read()
    print("文件内容:")
    print(repr(content[:500]))
    print("\n\n显示:")
    print(content[:500])
