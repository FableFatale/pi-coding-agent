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

## pgvector 处理记录

- 本机 PostgreSQL 17.9 已通过 `CREATE EXTENSION IF NOT EXISTS vector;` 启用 pgvector。
- 已验证扩展版本：`vector 0.8.2`。
- pgvector 属于 PostgreSQL 扩展，不是独立数据库；在三层记忆里只负责 L2 的 `embedding vector(1536)`、余弦距离检索和向量索引。
- L2 初始化策略：优先创建 `embedding VECTOR(1536)` 和 HNSW 索引；如果当前 PostgreSQL 没有 pgvector，则保留 PostgreSQL FTS 全文检索模式。

### Windows 安装记录

当前 Windows 环境使用 Visual Studio Build Tools 的 VC++ x64 工具链编译 pgvector：

```cmd
call D:\VS\BuildTools\VC\Auxiliary\Build\vcvars64.bat
set "PATH=D:\VS\BuildTools\VC\Tools\MSVC\14.51.36231\bin\Hostx64\x64;C:\Program Files\PostgreSQL\17\bin;%PATH%"
set "PGROOT=C:\Program Files\PostgreSQL\17"
cd /d D:\pi-coding-agent\pi-memory\pgvector
nmake /F Makefile.win
nmake /F Makefile.win install
```

`install` 需要管理员权限，因为会复制 `vector.dll`、SQL 控制文件等到 `C:\Program Files\PostgreSQL\17`。安装后对每个数据库执行一次：

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d 你的数据库名 -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### macOS 计划

macOS 不默认走 Windows 的 VC++ 编译流程。官方 pgvector 文档给了两条路径：

- Homebrew/Postgres.app：通常不需要手动编译；Homebrew 可直接 `brew install pgvector`，Postgres.app 新版本包含 pgvector。
- 源码安装：如果 PostgreSQL 不是 Homebrew/Postgres.app 管理，或需要固定源码版本，可以用 `make && make install`。

推荐优先使用 Homebrew：

```bash
brew install postgresql@17 pgvector
psql -d postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -d postgres -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
```

注意 Homebrew 的 pgvector 需要和实际运行的 PostgreSQL 主版本匹配；如果 `CREATE EXTENSION vector` 找不到控制文件，通常说明扩展安装到了另一个 PostgreSQL 目录。
