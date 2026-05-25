# Pi Coding Agent

> 一个本地运行的 AI 编程助手，基于 Claude Code 风格设计的终端 UI

**位置：** `D:\pi-coding-agent`  
**版本：** pi-coding-agent v0.66.1 + @earendil-works/pi-* 0.75.x
**Node 要求：** Node.js >= 22.19.0

---

## 快速开始

### 1. 安装扩展

双击运行 `scripts\install-extensions.bat`，自动安装所有扩展。

或手动安装：
```bash
# 复制扩展到 pi 配置目录
xcopy /E /I /Y pi-subagents %USERPROFILE%\.pi\agent\extensions\pi-subagents\
xcopy /E /I /Y pi-messenger %USERPROFILE%\.pi\agent\extensions\pi-messenger\
# ... 其他扩展同理
```

### 2. 配置 API Key

编辑 `%USERPROFILE%\.pi\agent\auth.json`：

```json
{
  "minimax": {
    "type": "api_key",
    "key": "你的API Key"
  }
}
```

或编辑 `%USERPROFILE%\.pi\agent\models.json`：

```json
{
  "providers": {
    "minimax": {
      "baseUrl": "https://api.minimaxi.com/anthropic",
      "api": "anthropic-messages",
      "apiKey": "你的API Key",
      "models": [
        {
          "id": "MiniMax-M2.7-highspeed",
          "input": ["text"],
          "contextWindow": 204800,
          "maxTokens": 32000
        }
      ]
    }
  }
}
```

### 3. 启动

```bash
D:\pi-coding-agent\pi.bat
```

### 4. 常用命令

| 命令 | 功能 |
|------|------|
| `/model` | 选择模型 |
| `/reload` | 重载扩展 |
| `/clear` | 清屏 |
| `/remember` | 保存记忆 |
| `/recall` | 搜索记忆 |

---

## Provider 测试

当前根目录已安装：

```text
@earendil-works/pi-agent-core@0.75.5
@earendil-works/pi-ai@0.75.5
@earendil-works/pi-tui@0.75.5
@earendil-works/pi-web-ui@0.75.3
```

### 1. 检查 Node 和依赖

```powershell
cd D:\pi-coding-agent
node -v
npm -v
npm install
npm audit
```

期望：

```text
node >= v22.19.0
found 0 vulnerabilities
```

### 2. 查看 OAuth Provider

```powershell
cd D:\pi-coding-agent
npx --no-install @earendil-works/pi-ai list
```

当前支持的 OAuth provider：

```text
anthropic       Anthropic (Claude Pro/Max)
github-copilot  GitHub Copilot
openai-codex    ChatGPT Plus/Pro (Codex Subscription)
```

### 3. 登录 OAuth Provider

交互式选择：

```powershell
npx --no-install @earendil-works/pi-ai login
```

指定 provider：

```powershell
npx --no-install @earendil-works/pi-ai login anthropic
npx --no-install @earendil-works/pi-ai login github-copilot
npx --no-install @earendil-works/pi-ai login openai-codex
```

登录凭据会写入当前目录的 `auth.json`。如果要给 Pi 主程序使用，建议同步到：

```text
%USERPROFILE%\.pi\agent\auth.json
```

### 4. 用 API Key Provider 快速测试

PowerShell 临时设置环境变量：

```powershell
$env:OPENAI_API_KEY="你的 OpenAI Key"
$env:ANTHROPIC_API_KEY="你的 Anthropic Key"
$env:GEMINI_API_KEY="你的 Gemini Key"
$env:MINIMAX_API_KEY="你的 MiniMax Key"
```

一次性调用 Pi，避免进入交互界面：

```powershell
npx --no-install pi -p --provider openai --model gpt-4o-mini "用一句话回复：provider 测试成功"
npx --no-install pi -p --provider anthropic --model claude-3-5-haiku-20241022 "用一句话回复：provider 测试成功"
npx --no-install pi -p --provider google --model gemini-2.5-flash "用一句话回复：provider 测试成功"
npx --no-install pi -p --provider minimax --model MiniMax-M2.7-highspeed "用一句话回复：provider 测试成功"
```

如果只想验证模型能否被发现：

```powershell
npx --no-install pi --list-models openai
npx --no-install pi --list-models anthropic
npx --no-install pi --list-models google
npx --no-install pi --list-models minimax
```

### 5. 常见 Provider 问题

**`No models available`**
> 没有可用 API Key、OAuth token 或模型配置。先检查环境变量、`auth.json`、`models.json`。

**`EBADENGINE Unsupported engine`**
> Node 版本低于包声明要求。升级到 Node.js 22.19.0 或更高。

**OAuth 登录后 Pi 仍不可用**
> `pi-ai login` 默认把 `auth.json` 写在当前目录；Pi 主程序通常读取 `%USERPROFILE%\.pi\agent\auth.json`。

---

## 目录结构

```
D:\pi-coding-agent\
├── pi.bat                      # 启动脚本
├── pi-start.bat               # 带环境变量的启动脚本
├── config.json                 # API Key 配置模板
├── README.md                   # 本文件
│
├── scripts/                   # 脚本
│   └── install-extensions.bat  # 一键安装脚本
│
├── node_modules/              # pi 主程序
│
├── # 官方扩展
├── pi-subagents/             # 子代理管理
├── pi-messenger/             # 多代理通讯
├── pi-mcp-adapter/           # MCP 适配器
├── pi-web-access/            # 网页访问
├── pi-btw/                   # 侧边对话
│
└── # 自定义扩展（记忆系统 + 工具扩展）
    ├── pi-memory/            # 三层记忆系统
    ├── pi-user-profile/     # 用户档案
    ├── pi-project-context/   # 项目上下文
    ├── pi-code-runner/       # 代码执行沙箱
    ├── pi-test-runner/       # 测试生成运行
    ├── pi-debugger/          # 断点调试
    └── pi-deploy/           # 自动化部署

C:\Users\<user>\.pi\agent\
├── auth.json                 # API Key 配置
├── models.json               # 模型配置
├── settings.json            # 用户设置
│
├── extensions/              # 所有扩展（安装后复制到这里）
│   ├── pi-subagents/
│   ├── pi-messenger/
│   ├── pi-mcp-adapter/
│   ├── pi-web-access/
│   ├── pi-btw/
│   ├── pi-memory/
│   ├── pi-user-profile/
│   ├── pi-project-context/
│   ├── pi-code-runner/
│   ├── pi-test-runner/
│   ├── pi-debugger/
│   └── pi-deploy/
│
├── memory/                  # 记忆存储
│   ├── MEMORY.md
│   ├── HEARTBEAT.md
│   ├── TODO.md
│   └── notes/
│
├── profile/                 # 用户档案
│   ├── USER.md
│   ├── PREFERENCES.md
│   └── HABITS.md
│
├── project-cache/           # 项目缓存
├── skills/                 # 结构化知识
├── state.db                # SQLite 数据库
└── bin/                    # 工具 (rg.exe, fd.exe)
```

---

## 扩展说明

### 官方扩展

| 扩展 | 功能 | 来源 |
|------|------|------|
| pi-subagents | 子代理管理，模型切换 | nicobailon |
| pi-messenger | 多代理通讯 | nicobailon |
| pi-mcp-adapter | MCP 适配器 | nicobailon |
| pi-web-access | 网页搜索、视频理解 | nicobailon |
| pi-btw | 侧边对话 | dbachelder |

### 记忆系统扩展

#### pi-memory（三层记忆）
- **L1 Working Memory**：Redis，会话级短期记忆，自动压缩
- **L2 Episodic Memory**：PostgreSQL + pgvector，历史会话、摘要、FTS 全文搜索、向量相似检索
- **L2.5 Curated Memory**：MD 文件，长期偏好、重要事实、人工沉淀记忆
- **L3 Semantic Memory**：skills 目录结构化知识，Pinecone 为可选未来钩子

当前 Windows 环境已验证：

```text
PostgreSQL 17.9
pgvector 0.8.2
Visual Studio Build Tools / VC++ nmake 编译安装
```

Windows 下 pgvector 需要和本机 PostgreSQL ABI 匹配，当前流程是用 Visual Studio Build Tools 的 x64 C++ 工具链编译 `pgvector/Makefile.win`，再安装到 `C:\Program Files\PostgreSQL\17`。安装完成后，每个需要向量能力的数据库都要执行：

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d 你的数据库名 -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

macOS 计划使用时优先走 Homebrew 或 Postgres.app：

```bash
brew install postgresql@17 pgvector
psql -d postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

官方 pgvector 文档确认 macOS/Linux 可以源码 `make && make install`，也可以用 Homebrew；Homebrew 当前提供 `brew install pgvector`，并有 macOS bottle。也就是说 macOS 通常不需要手动编译，但如果不用 Homebrew/Postgres.app，或 PostgreSQL 安装方式特殊，仍可能需要源码编译。

```
/remember <内容>  # 保存记忆
/recall <关键词>  # 搜索记忆
/forget <关键词> # 删除记忆
/memory --stats  # 显示统计
```

#### pi-user-profile（用户档案）
```
/profile         # 查看档案
/叫我小明        # 更新名字
```

#### pi-project-context（项目上下文）
```
/project --init  # 初始化项目
/project --status # 查看状态
```

### 工具扩展

#### pi-code-runner（代码执行）
```
/run python "print('hello')"
/run javascript "console.log('hello')"
/run bash "ls -la"
```

#### pi-test-runner（测试生成）
```
/test --generate src/utils.ts
/test --run
/test --coverage
```

#### pi-debugger（断点调试）
```
/debug --break main.ts:10
/debug --step
/debug --watch variableName
```

#### pi-deploy（自动化部署）
```
/deploy --docker
/deploy --k8s
/deploy --ci
/deploy --platform vercel
```

---

## 支持的 Provider

| Provider | 认证方式 | 环境变量 / 登录命令 |
|----------|----------|---------------------|
| OpenAI | API Key | `OPENAI_API_KEY` |
| Anthropic | API Key 或 OAuth | `ANTHROPIC_API_KEY` / `npx --no-install @earendil-works/pi-ai login anthropic` |
| Google Gemini | API Key | `GEMINI_API_KEY` |
| MiniMax | API Key | `MINIMAX_API_KEY` |
| GitHub Copilot | OAuth | `npx --no-install @earendil-works/pi-ai login github-copilot` |
| OpenAI Codex | OAuth | `npx --no-install @earendil-works/pi-ai login openai-codex` |

---

## 常见问题

**Q: 启动提示 "No models available"**
> 配置 API Key，见上面配置说明

**Q: 扩展加载失败**
> 执行 `/reload` 重载扩展

**Q: Windows 下找不到 node**
> 直接用 `pi.bat` 启动，已内置路径

---

## 相关链接

- [pi-mono](https://github.com/badlogic/pi-mono) - 主仓库
- [Pi 文档](https://pi.dev/) - 官方文档
- [nicobailon](https://github.com/nicobailon) - 官方扩展
- [dbachelder](https://github.com/dbachelder) - pi-btw

---

*最后更新：2026-05-25*
