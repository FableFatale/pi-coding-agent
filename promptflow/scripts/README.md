# 运行脚本目录

此目录包含各种测试和验证脚本。

## 脚本说明

| 脚本 | 说明 | 使用方法 |
|------|------|----------|
| `run_tests.py` | 运行所有单元测试 | `python run_tests.py` |
| `validate_tests.py` | 验证测试语法 | `python validate_tests.py` |
| `test_all.py` | 验证模块导入 | `python test_all.py` |
| `verify.py` | 快速验证核心功能 | `python verify.py` |

## 快速测试

```bash
# 进入脚本目录
cd scripts

# 运行所有测试
python run_tests.py

# 快速验证
python verify.py
```

## 测试报告

运行脚本后会生成报告到 `reports/` 目录：

- `test_report.html` - HTML 格式报告
- `test_report.md` - Markdown 格式报告
- `test_results.json` - JSON 原始数据

---
