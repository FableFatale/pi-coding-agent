# Pi Coding Agent

> 一个本地运行的 AI 编程助手，基于 Claude Code 风格设计的终端 UI

**位置：** `D:\pi-coding-agent`  
**版本：** v0.66.1

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
- **Working Memory**：会话级，自动压缩
- **Episodic Memory**：SQLite FTS5 全文搜索
- **Curated Memory**：MD 文件，立即持久化
- **Semantic Memory**：skills 目录结构化知识

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

| Provider | 环境变量 | baseUrl 示例 |
|----------|----------|-------------|
| MiniMax | `MINIMAX_API_KEY` | `https://api.minimaxi.com/anthropic` |
| Google | `GOOGLE_API_KEY` | `https://api.google.com` |
| Anthropic | `ANTHROPIC_API_KEY` | `https://api.anthropic.com` |
| OpenAI | `OPENAI_API_KEY` | `https://api.openai.com` |

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

*最后更新：2026-04-11*
