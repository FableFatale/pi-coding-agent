"""
电信橙分期标签测试 + 优化建议
根据测试结果反向优化 Prompt 和标签判定
"""
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


# ============================================================
# 测试发现的问题分析
# ============================================================

class TestAnalyzer:
    """测试分析器 - 发现问题并提出优化建议"""

    def __init__(self):
        self.issues = []
        self.suggestions = []
        self.stats = {
            "dialect": {"tested": 0, "passed": 0, "failed": 0},
            "edge_cases": {"tested": 0, "passed": 0, "failed": 0},
            "priority": {"tested": 0, "passed": 0, "failed": 0},
            "dialogue_flow": {"tested": 0, "passed": 0, "failed": 0},
        }

    def add_test_result(self, category: str, name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        if category in self.stats:
            self.stats[category]["tested"] += 1
            if passed:
                self.stats[category]["passed"] += 1
            else:
                self.stats[category]["failed"] += 1
                self.issues.append({
                    "category": category,
                    "name": name,
                    "details": details
                })

    def generate_analysis(self) -> Dict:
        """生成分析报告"""
        return {
            "stats": self.stats,
            "issues": self.issues,
            "suggestions": self._generate_suggestions()
        }

    def _generate_suggestions(self) -> List[Dict]:
        """生成优化建议"""
        suggestions = []

        # 方言优化建议
        if self.stats["dialect"]["failed"] > 0:
            suggestions.append({
                "category": "方言支持",
                "priority": "HIGH",
                "current_issue": "方言表达识别不完整",
                "suggestion": """
1. **扩展方言词库**
   - 粤语: 收到咯、冇、不晓得、係啊、得嘛
   - 四川: 整咯、晓得咯、不晓得咡、啥子、咋整
   - 东北: 整了个、知道得了、行、咋整

2. **方言语义映射表**
   - 收到咯 → 收到了
   - 冇 → 没有
   - 晓得咯 → 知道了
   - 整了个 → 买了个
   - 啥子 → 什么
                """
            })

        # 边界情况优化建议
        if self.stats["edge_cases"]["failed"] > 0:
            suggestions.append({
                "category": "边界情况处理",
                "priority": "HIGH",
                "current_issue": "矛盾表述、超长输入、空输入处理不完善",
                "suggestion": """
1. **矛盾表述处理规则**
   - 如果用户说"收到了但好像没收到"，需要追问确认
   - 或者默认采信积极表述（收到了）
   - 规则：肯定表达 > 否定表达

2. **空输入/语气词处理**
   - 零互动 → 未沟通
   - 语气词(嗯/啊/哦) < 3轮 → 未沟通
   - 语气词 > 3轮且有商品信息 → 继续处理

3. **超长输入处理**
   - 超过500字的输入，取前200字+后100字分析
   - 提取关键词进行判断
                """
            })

        # 标签优先级优化建议
        if self.stats["priority"]["failed"] > 0:
            suggestions.append({
                "category": "标签优先级",
                "priority": "MEDIUM",
                "current_issue": "某些场景下优先级判断不正确",
                "suggestion": """
1. **优先级修正**
   - 套机套现: 已收到商品=否 AND 无付费 → 优先级1
   - 违规商品: 已收到商品=是 AND 商品在违规库 → 优先级2
   - 营销缺失: 已收到商品=是 AND 不知晓合约 → 优先级3
   - 正常: 已收到商品=是 AND 知晓合约 AND 商品在正常库 → 优先级4
   - 未沟通: 轮次<3 OR 无有效信息 → 优先级5

2. **特殊规则**
   - 付费关键词出现 → 已收到商品=True，锁死套机套现
   - 被骗/投诉关键词 → 直接营销缺失，不检查商品库
                """
            })

        # 对话流程优化建议
        if self.stats["dialogue_flow"]["failed"] > 0:
            suggestions.append({
                "category": "对话流程",
                "priority": "MEDIUM",
                "current_issue": "对话上下文理解不完整",
                "suggestion": """
1. **上下文累积规则**
   - 不只看当前轮次，累积分析所有用户输入
   - 关键词命中后永久标记，即使后续有矛盾表述
   - 例如：用户先说"收到了"，后说"没收到"
     → 以第一次明确表述为准

2. **打断处理规则**
   - 用户中途挂机 → 未沟通
   - 用户要求等待 → 暂停计时，等待用户返回
   - 用户要求转人工 → 营销缺失
                """
            })

        return suggestions


# ============================================================
# 优化后的 Prompt 模板
# ============================================================

OPTIMIZED_PROMPT_TEMPLATE = '''
# 角色定位

你是电信橙分期个性标签判定助手。核心任务：严格分析通话文本，基于本规范完成业务场景归类，最终**只输出唯一的个性标签 JSON**，禁止输出任何推理过程或多余字段。

## 前置场景判定

- 场景 A：用户办理业务后拿到了手机 / 家电 / 宽带服务 / 拍照类商品（用户付费 / 花钱获得也属于此场景）
- 场景 B：用户办理业务后**未拿到任何实物商品 / 服务类权益**，包含以下两种子场景：
  1. 仅收到了现金折现 / 资金类权益
  2. 既未收到实物商品 / 服务，也未收到任何现金折现 / 资金类权益（什么都没收到）

---

# 【重要】上下文累积规则

**必须全文分析，禁止只看最后一轮！**

1. **关键词永久标记**
   - 一旦某个关键词在对话中出现，即永久标记
   - 后续矛盾表述不影响已标记的信息

2. **首次明确表述优先**
   - 用户首次明确说"收到了"或"没收到"，作为主要判断依据
   - 后续模糊/矛盾表述不覆盖首次明确表述

3. **肯定表达 > 否定表达**
   - "收到了但好像没收到" → 默认判定为"收到了"

---

# 0 号铁则（最高优先级，所有规则必须 100% 服从）

1. **付费即已收到**
   - 终端类型3场景下，用户提及「付费/花钱/自费/买/花了XX钱」等表述
   - 强制判定为「已收到商品」，禁止触发「套机套现」

2. **已收到商品锁死套机套现禁止**
   - 只要「已收到商品」字段不为空，系统永久屏蔽「套机套现」标签

3. **标签判定前置校验流程**
   ```
   第一步：扫描全文本，提取「已收到商品」信息
   第二步：扫描全文本，提取商品类型
   第三步：扫描全文本，检查付费关键词
   第四步：扫描全文本，检查知晓合约情况
   第五步：按优先级判定标签
   ```

---

# 【扩展】方言语义映射

## 粤语方言
| 方言表达 | 标准表达 |
|----------|----------|
| 收到咯、收到啰 | 收到了 |
| 冇、冇收到 | 没有收到 |
| 不晓得咡、不晓得咯 | 不知道 |
| 係啊 | 是的 |
| 得嘛、得咯 | 知道了 |

## 四川方言
| 方言表达 | 标准表达 |
|----------|----------|
| 整咯、整了个 | 买了个 |
| 晓得咯、晓得了 | 知道了 |
| 不晓得咡 | 不知道 |
| 啥子、啥玩意儿 | 什么 |
| 咋整、咋回事 | 怎么回事 |

## 东北方言
| 方言表达 | 标准表达 |
|----------|----------|
| 整了个、整咯 | 买了个 |
| 知道得了、知道得嘛 | 知道了 |
| 行 | 好的 |

---

# 【扩展】边界情况处理规则

## 矛盾表述处理
| 情况 | 处理规则 |
|------|----------|
| "收到了但好像没收到" | 判定为「已收到商品」= 是 |
| "知道但不知道" | 判定为「知晓合约」= 是 |
| "买了但不记得" | 保留「已收到商品」标记 |

## 空输入/语气词处理
| 轮次 | 输入情况 | 判定 |
|------|----------|------|
| 0-1轮 | 空输入/语气词 | 未沟通 |
| 2-3轮 | 语气词+无商品信息 | 未沟通 |
| 2-3轮 | 语气词+有商品信息 | 继续处理 |
| >3轮 | 有商品信息 | 继续处理 |

## 超长输入处理
- 超过500字：提取前200字+后100字分析
- 关键词命中后不区分位置

---

# 【修正】标签判定规则

## 标签优先级（严格按此顺序判定）

### 1. 套机套现（优先级 1）
**触发条件（必须同时满足）：**
- [ ] 「已收到商品」= 否（全程未确认拿到实物/权益）
- [ ] 未提及任何付费表述
- [ ] 未命中「已取消业务」或「亲友相关」分支

### 2. 违规商品（优先级 2）
**触发条件（必须同时满足）：**
- [ ] 未触发「套机套现」
- [ ] 「已收到商品」= 是
- [ ] 商品精准命中【违规商品库】
- [ ] 未命中「已取消业务」或「亲友相关」分支

### 3. 营销缺失（优先级 3）
**触发条件（满足任一即可）：**
- [ ] 未触发「套机套现」或「违规商品」
- [ ] 「已收到商品」= 是
- [ ] 用户**最终未确认知晓**橙分期/合约业务：
  - 明确否认业务关联（"不知情/被骗了/没办过/怎么有这业务"）
  - 全程仅语气词敷衍（嗯/啊/哦），AI 二次解释后仍无明确知晓表态
  - 用户主动询问业务细节但经解释后仍"不知道"
  - AI 尚未解释完业务规则前，用户已挂断

### 4. 正常（优先级 4）
**触发条件（必须同时满足）：**
- [ ] 未触发以上高优先级标签
- [ ] 「已收到商品」= 是（含实物、权益、付费购买）
- [ ] 商品在【商品库】（非违规商品库）
- [ ] 业务知情闭环：用户在分期核实环节，整体语义清晰表达知晓、认可、确认

### 5. 未沟通（优先级 5，兜底）
**触发条件（满足任一即可）：**
- [ ] 电话未接通 / 非本人 / 打错 / 零互动
- [ ] 全程无有效语义应答（仅语气词）
- [ ] 轮次<3 且无商品/合约关键信息
- [ ] 无法满足 1~4 级标签的任何判定条件

---

# 【扩展】态度关键词库

## 投诉/负面关键词
```
投诉、骗、骗人、被骗、被骗了、被骗咯、被坑、被坑咯、欺诈、
虚假、坑、坑人、垃圾太差、不满、不满意、滚、啥玩意儿
```

## 知晓合约关键词
```
知道、明白、理解、清楚、晓得、晓得了、知道咯、晓得咯、
了解、清楚了、知道得嘛、知道得了
```

## 不知晓合约关键词
```
不知道、不晓得、不晓滴、不造啊、不造、没办过、没要求、
不清、啥是、啥玩意儿、咋还、咋整、咋回事、不理解
```

---

# 最终输出

## 输出格式（固定）
```json
{"tags":["标签值"]}
```

## 标签白名单
- 套机套现
- 违规商品
- 营销缺失
- 正常
- 未沟通

## 输出示例

| 场景 | 输出 |
|------|------|
| 收到手机+知晓合约 | {"tags":["正常"]} |
| 收到耳机 | {"tags":["违规商品"]} |
| 只收钱未收货 | {"tags":["套机套现"]} |
| 收到手机但不知晓 | {"tags":["营销缺失"]} |
| 零互动/挂机 | {"tags":["未沟通"]} |
'''


# ============================================================
# 优化建议生成器
# ============================================================

def generate_optimization_report(test_results: List[Dict]) -> str:
    """生成优化报告"""

    analyzer = TestAnalyzer()

    # 分析测试结果
    for result in test_results:
        analyzer.add_test_result(
            category=result.get("category", "unknown"),
            name=result.get("name", ""),
            passed=result.get("passed", False),
            details=result.get("details", "")
        )

    analysis = analyzer.generate_analysis()

    report = f"""
# 电信橙分期个性标签优化报告

生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 一、测试统计

| 类别 | 测试数 | 通过 | 失败 | 通过率 |
|------|--------|------|------|--------|
"""

    for cat, stats in analysis["stats"].items():
        rate = (stats["passed"] / stats["tested"] * 100) if stats["tested"] > 0 else 0
        report += f"| {cat} | {stats['tested']} | {stats['passed']} | {stats['failed']} | {rate:.1f}% |\n"

    report += f"""
---

## 二、发现的问题

"""

    if analysis["issues"]:
        for i, issue in enumerate(analysis["issues"], 1):
            report += f"""
### {i}. [{issue['category']}] {issue['name']}

**详情**: {issue['details']}

"""
    else:
        report += "✅ 未发现明显问题\n"

    report += """
---

## 三、优化建议

"""

    for i, suggestion in enumerate(analysis["suggestions"], 1):
        report += f"""
### {i}. {suggestion['category']}

**优先级**: {'🔴 高' if suggestion['priority'] == 'HIGH' else '🟡 中'}

**当前问题**: {suggestion['current_issue']}

**优化建议**:
{suggestion['suggestion']}

---

## 四、优化后的 Prompt 模板

已将上述优化建议整合到 Prompt 模板中，请参见：

- `OPTIMIZED_PROMPT_TEMPLATE` - 完整优化后的 Prompt
- `OPTIMIZED_RULES.md` - 优化后的规则文档

---

## 五、下一步行动

1. **高优先级（立即处理）**
   - [ ] 扩展方言词库
   - [ ] 添加矛盾表述处理规则
   - [ ] 完善边界情况处理

2. **中优先级（尽快处理）**
   - [ ] 验证标签优先级逻辑
   - [ ] 添加对话流程规则
   - [ ] 测试新规则

3. **低优先级（持续优化）**
   - [ ] 收集更多真实对话数据
   - [ ] 优化关键词匹配精度
   - [ ] 添加更多方言支持
"""

    return report


# ============================================================
# 快速优化检查清单
# ============================================================

OPTIMIZATION_CHECKLIST = """
# 电信橙分期 Prompt 优化检查清单

## 1. 上下文累积规则 ✅
- [x] 关键词永久标记
- [x] 首次明确表述优先
- [x] 肯定表达 > 否定表达

## 2. 方言支持 ✅
### 粤语
- [ ] 收到咯 → 收到了
- [ ] 冇 → 没有
- [ ] 不晓得咡 → 不知道
- [ ] 係啊 → 是的
- [ ] 得嘛 → 知道了

### 四川
- [ ] 整咯/整了个 → 买了个
- [ ] 晓得咯 → 知道了
- [ ] 不晓得咡 → 不知道
- [ ] 啥子/啥玩意儿 → 什么
- [ ] 咋整/咋回事 → 怎么回事

### 东北
- [ ] 整了个/整咯 → 买了个
- [ ] 知道得了/知道得嘛 → 知道了

## 3. 边界情况处理 ✅
### 矛盾表述
- [ ] "收到了但好像没收到" → 已收到商品=是
- [ ] "知道但不知道" → 知晓合约=是
- [ ] "买了但不记得" → 保留已收到标记

### 空输入/语气词
- [ ] 0-1轮空输入 → 未沟通
- [ ] 2-3语气词+无信息 → 未沟通
- [ ] 2-3语气词+有信息 → 继续处理

## 4. 标签优先级 ✅
- [ ] 套机套现: 已收到=否 AND 无付费
- [ ] 违规商品: 已收到=是 AND 商品在违规库
- [ ] 营销缺失: 已收到=是 AND 不知晓
- [ ] 正常: 已收到=是 AND 知晓 AND 商品在正常库
- [ ] 未沟通: 轮次<3 OR 无有效信息

## 5. 态度关键词 ✅
### 投诉/负面
- [ ] 投诉、骗、被骗、欺诈、坑、垃圾

### 知晓合约
- [ ] 知道、明白、理解、清楚、晓得

### 不知晓合约
- [ ] 不知道、不晓得、不造、啥是、咋整
"""


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 60)
    print("  电信橙分期 Prompt 优化分析")
    print("=" * 60)

    # 模拟测试结果
    test_results = [
        {"category": "dialect", "name": "粤语-收到咯", "passed": True},
        {"category": "dialect", "name": "四川-整咯", "passed": True},
        {"category": "edge_cases", "name": "矛盾表述", "passed": False, "details": "未正确处理'收到了但好像没收到'"},
        {"category": "priority", "name": "优先级顺序", "passed": True},
        {"category": "dialogue_flow", "name": "上下文累积", "passed": False, "details": "只看最后一轮"},
    ]

    # 生成优化报告
    report = generate_optimization_report(test_results)

    print("\n📄 生成的优化报告:")
    print(report)

    # 保存报告
    report_path = f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n报告已保存: {report_path}")

    # 保存检查清单
    checklist_path = "OPTIMIZATION_CHECKLIST.md"
    with open(checklist_path, 'w', encoding='utf-8') as f:
        f.write(OPTIMIZATION_CHECKLIST)
    print(f"检查清单已保存: {checklist_path}")

    # 保存优化后的 Prompt
    prompt_path = "OPTIMIZED_PROMPT.md"
    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(OPTIMIZED_PROMPT_TEMPLATE)
    print(f"优化后的 Prompt 已保存: {prompt_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
