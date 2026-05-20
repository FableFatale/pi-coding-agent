---
name: pi-code-runner
description: 本地代码执行沙箱。支持 python、javascript、typescript、bash、go。
---

# pi-code-runner

本地代码执行沙箱，通过 `/run` 命令运行代码。

## 命令

```
/run <语言> <代码>
```

## 支持语言

| 语言 | 示例 |
|------|------|
| python | `/run python print('hello')` |
| javascript | `/run javascript console.log('hello')` |
| typescript | `/run typescript console.log('hello')` |
| bash | `/run bash ls -la` |
| go | `/run go fmt.Println("hello")` |

## 特性

- 超时控制（默认 30 秒）
- 自动清理临时文件
- 捕获 stdout/stderr

## 示例

```
/run python print('hello world')
/run javascript const x = 1; console.log(x)
/run bash echo "hello"
```
