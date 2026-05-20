# Pi Memory 快速开始

## 安装

```bash
cd D:\pi-coding-agent\pi-memory
pip install -e .
```

## 配置

```bash
# 复制配置
copy .env.example .env

# 编辑 .env 填入实际值
```

## 一键运行示例

```bash
pip install python-dotenv  # 如果没有
python examples/basic_usage.py
```

---

## 架构

```
┌─────────────────────────────────────────┐
│  L1 Working Memory (Redis)              │
│  - TTL=1小时，访问自动延长              │
│  - 短期会话信息                        │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  L2 Episodic Memory (PostgreSQL+pgvector)│
│  - 对话历史片段                        │
│  - FTS + 向量混合搜索                  │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  L3 Semantic Memory (Pinecone)          │
│  - 技能向量存储                        │
│  - 冲突检测                            │
└─────────────────────────────────────────┘
```

---

## 使用示例

```python
from pi_memory import MemorySystem

# 初始化
memory = MemorySystem()

# L1: 短期会话
memory.session_set("user:123", {"name": "张三"})
data = memory.session_get("user:123")  # 自动延长TTL

# L2: 对话记忆
memory.remember("用户询问代码优化", metadata={"user": "张三"})
results = memory.recall("代码优化")

# L3: 技能知识
memory.learn_skill("python", vector=[...])
skills = memory.find_skills(vector=[...])
```

---

## 依赖

| 组件 | 用途 | 必需 |
|------|------|------|
| Redis | L1工作记忆 | ✅ |
| PostgreSQL + pgvector | L2情景记忆 | ✅ |
| Pinecone | L3语义记忆 | 可选 |

---

## 安装依赖

```bash
# Redis
# macOS: brew install redis
# Windows: https://redis.io/docs/getting-started/

# PostgreSQL + pgvector
# docker run -d -e POSTGRES_PASSWORD=xxx -p 5432:5432 pgvector/pgvector

# Pinecone (可选)
pip install pinecone-client
```
