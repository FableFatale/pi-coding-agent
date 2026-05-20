---
name: pi-debugger
description: 断点调试。支持 node 和 python。
---

# pi-debugger

断点调试扩展，通过 `/debug` 命令。

## 命令

```
/debug --launch <文件> [语言]  # 启动调试
/debug --break [文件:]行号     # 设置断点
/debug --list                  # 列出断点
/debug --kill                  # 终止调试
/debug --status                # 查看状态
```

## 支持语言

| 语言 | 调试器 |
|------|--------|
| node | Node Inspector |
| python | debugpy |

## 示例

```
/debug --launch app.js
/debug --break app.js:10
/debug --break 10 --condition i > 5
/debug --list
/debug --kill
```

## 条件断点

```
/debug --break main.ts:20 --condition userId == 123
```
