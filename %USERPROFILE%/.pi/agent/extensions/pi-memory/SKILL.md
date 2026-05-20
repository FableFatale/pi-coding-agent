---
name: pi-memory
description: 三层记忆系统。L1 Redis + L2 PostgreSQL/pgvector + L2.5 文件层，自动保存对话到记忆。使用 /memory /remember /recall /forget 命令。
---

# Pi Memory - 三层记忆系统

## 自动保存 ✅

每轮对话自动保存，无需手动输入：

| 事件 | 保存位置 |
|------|---------|
| 用户输入 | L1 Redis |
| 工具输出 (bash/read/grep等) | L1 Redis |
| Agent 响应 | L1 Redis |
| 关键词触发 (记住/重要/别忘) | L2.5 MEMORY.md |
| 每5轮 / session结束 | L1 → L2 PostgreSQL |

## 命令

| 命令 | 功能 |
|------|------|
| `/memory --read` | 读取所有记忆 |
| `/memory --stats` | 三层统计 |
| `/memory --l1` | L1 Redis 状态 |
| `/memory --l1-flush` | 清空 L1 |
| `/memory --l2` | L2 PostgreSQL 状态 |
| `/memory --l2-sessions` | 列出 L2 会话 |
| `/memory --search <关键词>` | 混合搜索 L1+L2+L2.5 |
| `/remember <内容>` | 手动保存策划记忆 |
| `/recall <关键词>` | 搜索所有层 |
| `/forget <关键词>` | 删除记忆 |

## 文件层

```
~/.pi/agent/memory/
├── MEMORY.md      # 核心记忆
├── USER.md        # 用户档案
├── SYSTEM.md      # 系统配置
├── EXPERIENCE.md  # 踩坑经验
├── HEARTBEAT.md   # 定时任务
├── TODO.md        # 待办
└── notes/         # 每日随手记
```
