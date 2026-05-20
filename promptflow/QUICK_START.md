# 快速开始指南

## 一键运行

```bash
cd D:\pi-coding-agent\promptflow

# 运行完整测试
python run_all.py
```

---

## 目录结构

```
promptflow/
│
├── 📁 examples/           # 规范文档
│   ├── telecom_tags.md     # 原始标签规范
│   ├── telecom_tags_optimized.md   # 优化后标签
│   └── telecom_flow_optimized.md   # 优化后话术
│
├── 📁 tests/              # 测试用例
│   └── test_*.py         # 各种测试
│
├── 📁 data/               # 您的数据目录
│   └── README.md          # 数据格式说明
│
├── 📁 reports/           # 生成的报告
│   └── README.md         # 报告说明
│
├── 📁 scripts/           # 辅助脚本
│   └── README.md
│
├── run_all.py             # ⭐ 一键测试
├── run_optimize.py        # 优化分析
├── test_telecom_dialogue.py  # 对话测试
└── README.md              # 本文件
```

---

## 运行测试

### 方式1: 一键测试 (推荐)

```bash
python run_all.py
```

输出：
- 测试结果统计
- 话术评分
- 生成报告到 `reports/`

### 方式2: 对话测试

```bash
python test_telecom_dialogue.py
```

输出：
- HTML 报告
- JSON 数据

### 方式3: 优化分析

```bash
python run_optimize.py
```

输出：
- 优化建议
- 话术问题分析

---

## 下一步

### 1. 上传您的数据

将真实对话数据放到 `data/` 目录：
- 话术文本
- 对话日志
- 标签案例
- 方言样本

### 2. 自定义测试用例

编辑 `run_all.py` 中的 `TEST_CASES` 列表：
```python
TEST_CASES = [
    {"name": "您的场景", "dialogue": [...], "expected": "正常"},
    ...
]
```

### 3. 查看报告

打开 `reports/` 目录中的报告文件：
- `TEST_REPORT_*.md` - Markdown 报告
- `test_report.html` - HTML 报告

---

## 文件说明

| 文件 | 用途 |
|------|------|
| `run_all.py` | 主测试脚本 |
| `run_optimize.py` | 优化分析 |
| `test_telecom_dialogue.py` | 对话测试 |
| `examples/telecom_flow_optimized.md` | 完整优化规范 |

---

## 帮助

```bash
# 查看帮助
python run_all.py --help

# 查看测试用例
cat run_all.py | grep "TEST_CASES"
```

---

**准备好后，上传您的数据到 `data/` 目录！**
