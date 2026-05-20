---
name: pi-test-runner
description: 测试生成和运行。支持 jest、vitest、pytest、gotest。
---

# pi-test-runner

自动化测试生成和运行，通过 `/test` 命令。

## 命令

```
/test --detect     # 检测测试框架
/test --run [框架] # 运行测试
/test --coverage   # 运行并生成覆盖率
```

## 支持框架

| 框架 | 文件 | 命令 |
|------|------|------|
| Jest | `*.test.ts` | npx jest |
| Vitest | `*.test.ts` | npx vitest |
| Pytest | `test_*.py` | pytest |
| Go test | `*_test.go` | go test |

## 自动检测

```
/test --detect
```
自动检测项目使用的测试框架。

## 运行测试

```
/test --run jest
/test --run --coverage
```

## 示例

```
/test --detect
/test --run vitest
/test --coverage
```
