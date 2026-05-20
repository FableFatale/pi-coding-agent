# Pi Memory TODO

## 已完成 ✅

- [x] L1 Working Memory - Redis 实现（l1-redis.ts）
- [x] L2 Episodic Memory - PostgreSQL + pgvector（l2-postgres.ts）
  - HNSW 索引 + cosine distance
  - GIN 全文搜索
  - `storeWithEmbedding()` / `searchByVector()`
- [x] L2.5 Curated Memory - 文件层（MEMORY.md 等）
- [x] **自动保存**（auto-save.ts）
  - `session_start` → 初始化 L1 session
  - `input` → L1 + L2.5 关键词触发
  - `tool_execution_end` → L1
  - `agent_end` → L1
  - 每 5 轮自动 compress L1 → L2
  - `session_shutdown` → 最终压缩
- [x] `/memory` 系列命令
- [x] `/remember` / `/recall` / `/forget`

## 文件结构

```
pi-memory/
├── storage.ts      # 共享工具函数（无依赖）
├── l1-redis.ts    # L1: Redis
├── l2-postgres.ts # L2: PostgreSQL + pgvector
├── auto-save.ts   # 自动保存逻辑
├── shared.ts      # 扩展入口 + 所有命令实现
├── memory.ts      # 重新导出 shared.ts
└── package.json
```

## 依赖安装记录

- ioredis: ✅ npm 安装
- pg: ✅ npm 安装
- pgvector: ✅ MSYS2 UCRT64 编译安装

## L3 Semantic Memory（未来特性）⏳

- [ ] @pinecone-database/pinecone（需配置 API key）
- [ ] 技能向量存储
