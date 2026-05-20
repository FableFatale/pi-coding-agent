# Pi Memory - 三层记忆系统

## 架构

```
L1: Redis Working Memory    ✅ 自动保存每轮对话
    ↓ (每5轮 compress)
L2: PostgreSQL + pgvector ✅ HNSW向量搜索 + GIN全文搜索
    ↓ (关键词触发)
L2.5: Curated Memory      ✅ 文件层策划记忆
    ↓
L3: Pinecone Semantic      ⏳ 未来特性
```

## 自动保存逻辑

| 事件 | 操作 |
|------|------|
| `session_start` | 初始化 L1 sessionId |
| `input` | 用户消息 → L1；关键词触发 → L2.5 |
| `tool_execution_end` | 工具输出 → L1（bash/read/grep等） |
| `agent_end` | Agent 响应 → L1 |
| 每 5 轮 | L1 compress → L2 持久化 |
| `session_shutdown` | 最终 L1 compress → L2 |

**L2.5 触发词**：记住、重要、别忘、要记住、don't forget、important 等

## 命令

| 命令 | 功能 |
|------|------|
| `/memory --read` | 读取所有记忆 |
| `/memory --stats` | 三层统计 |
| `/memory --l1` | L1 Redis 状态 |
| `/memory --l1-flush` | 清空 L1 |
| `/memory --l2` | L2 PostgreSQL 状态 |
| `/memory --l2-sessions` | 列出 L2 会话 |
| `/memory --l2-session <id>` | 查看某会话 |
| `/memory --search <关键词>` | 混合搜索 |
| `/remember <内容>` | 保存策划记忆 |
| `/recall <关键词>` | 搜索所有层 |
| `/forget <关键词>` | 删除记忆 |

## 文件结构

```
pi-memory/
├── storage.ts      # 共享工具（无依赖）
├── l1-redis.ts    # L1 Redis
├── l2-postgres.ts # L2 PostgreSQL + pgvector
├── auto-save.ts   # 自动保存
├── shared.ts      # 扩展入口 + 命令
├── memory.ts      # 重新导出 shared.ts
└── package.json
```

## 依赖

| 依赖 | 版本 | 状态 |
|------|------|------|
| ioredis | 5.x | ✅ |
| pg | 8.x | ✅ |
| pgvector | 0.8.2 | ✅ 编译安装 |
