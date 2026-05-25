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

本机已验证 PostgreSQL 17.9 + pgvector 0.8.2。对新数据库启用方式：

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d 你的数据库名 -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

## 安装依赖

### Windows

当前仓库已在 Windows 上验证 PostgreSQL 17.9 + pgvector 0.8.2。pgvector 是 PostgreSQL 扩展，Windows 下需要用 Visual Studio Build Tools / VC++ x64 工具链编译安装到 PostgreSQL 目录。

```cmd
call D:\VS\BuildTools\VC\Auxiliary\Build\vcvars64.bat
set "PATH=D:\VS\BuildTools\VC\Tools\MSVC\14.51.36231\bin\Hostx64\x64;C:\Program Files\PostgreSQL\17\bin;%PATH%"
set "PGROOT=C:\Program Files\PostgreSQL\17"
cd /d D:\pi-coding-agent\pi-memory\pgvector
nmake /F Makefile.win
nmake /F Makefile.win install
```

然后启用扩展：

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d 你的数据库名 -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### macOS

macOS 优先使用 Homebrew 或 Postgres.app，不需要走 Windows 的 VC++ 编译流程。Homebrew 路径：

```bash
brew install redis
brew install postgresql@17 pgvector
psql -d postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -d postgres -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
```

如果不用 Homebrew/Postgres.app，或要固定 pgvector 源码版本，则仍可按官方源码方式编译：

```bash
git clone --branch v0.8.2 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### Docker 备用

```bash
docker run -d -e POSTGRES_PASSWORD=xxx -p 5432:5432 pgvector/pgvector
```

### Pinecone

# Pinecone (可选)
pip install pinecone-client
```
