# 电信橙分期话术与标签优化系统

## 项目概述

基于 PromptFlow 框架的电信橙分期外呼话术与个性标签判定系统，包含完整的测试、优化、分析功能。

---

## 一键运行

```bash
cd D:\pi-coding-agent\promptflow
python run_all.py
```

或双击运行：
```
一键测试.bat
```

---

## 目录结构

```
promptflow/
│
├── 📁 src/                      # 源代码
│   └── promptflow/              # PromptFlow 框架
│
├── 📁 examples/                 # 示例数据
│   ├── customer_service.md       # 客服场景示例
│   ├── telecom_tags.md          # 原始标签规范
│   ├── telecom_tags_optimized.md # 优化后标签规范
│   └── telecom_flow_optimized.md # 优化后话术+标签
│
├── 📁 tests/                     # 测试用例
│   └── test_*.py                 # 各种测试用例
│
├── 📁 data/                     # 📂 您的数据目录
│   └── README.md                 # 数据格式说明
│
├── 📁 reports/                   # 📄 生成的报告
│   └── README.md                 # 报告说明
│
├── 📁 scripts/                   # 辅助脚本
│   └── README.md
│
├── 📁 docs/                     # 文档
│   ├── QUICK_START.md           # 快速开始 ⭐
│   ├── TEST_CASES_README.md     # 测试用例说明
│   └── TEST_GUIDE.md            # 测试指南
│
├── run_all.py                    # ⭐ 一键测试 (推荐)
├── run_optimize.py               # 优化分析
├── test_telecom_dialogue.py     # 对话测试
├── 一键测试.bat                   # Windows快捷方式
├── pyproject.toml               # 项目配置
└── README.md                   # 本文件
```

---

## 快速开始

### 一键测试 (推荐)

```bash
python run_all.py
```

### 或双击

```
一键测试.bat
```

---

## 核心文件

| 文件 | 说明 |
|------|------|
| `run_all.py` | ⭐ **一键测试** - 包含所有测试 |
| `examples/telecom_flow_optimized.md` | **完整优化版** - 话术+标签 |
| `examples/telecom_tags_optimized.md` | **标签优化版** - 判定规则 |
| `data/` | 📂 **数据目录** - 上传您的数据 |

---

## 测试覆盖

### 话术流程 (13个场景)
- ✅ 标准流程 / 等待 / 语气词
- ✅ 投诉 / 询问业务
- ✅ 方言 (粤语/四川/东北)
- ✅ 未收到商品 / 违规商品

### 标签判定 (5个标签)
- ✅ 正常 / 套机套现
- ✅ 违规商品 / 营销缺失 / 未沟通

---

## 下一步

### 1. 运行测试
```bash
python run_all.py
```

### 2. 上传数据
将真实对话数据放到 `data/` 目录

### 3. 查看报告
报告会自动生成到 `reports/` 目录

---

**准备好后，查看 `QUICK_START.md` 获取更多详情！**
