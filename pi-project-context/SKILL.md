---
name: pi-project-context
description: 项目上下文系统。为每个项目保存特殊配置、架构说明、成员信息。进入项目目录时自动加载。
---

# Pi Project Context

每个项目的专属上下文。

## 文件结构

```
项目根目录/
├── .pi/               # 项目级配置（提交到 git）
│   ├── config.json    # 项目配置
│   ├── ARCHITECTURE.md # 架构说明
│   ├── RULES.md       # 代码规范
│   └── CONTEXT.md     # 项目背景
│
~/.pi/agent/
└── project-cache/    # 项目缓存（本地）
    ├── <project-hash>/
    │   ├── state.json  # 项目状态
    │   ├── history.md  # 修改历史
    │   └── notes/      # 项目笔记
```

## 项目配置 (config.json)

```json
{
  "name": "my-project",
  "packageManager": "pnpm",
  "framework": "next.js",
  "typescript": true,
  "linter": "eslint",
  "testFramework": "jest",
  "envFiles": [".env.local", ".env.production"],
  "importantPaths": {
    "src": "./src",
    "tests": "./tests",
    "docs": "./docs"
  }
}
```

## 架构说明 (ARCHITECTURE.md)

```markdown
# 项目架构

## 目录结构
- `/src` - 源代码
- `/tests` - 测试文件
- `/docs` - 文档

## 核心技术栈
- React 18
- TypeScript 5
- Tailwind CSS

## 关键模块
- `auth/` - 认证模块
- `api/` - API 层
- `db/` - 数据库模型

## 数据流
用户请求 → API → Service → Repository → DB
```

## 项目规则 (RULES.md)

```markdown
# 代码规范

## 命名
- 组件：大驼峰 MyComponent.tsx
- 函数：小驼峰 handleClick
- 常量：全大写下划线分隔

## 提交规范
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试
```

## 使用方法

### 进入项目
```
cd my-project
# 自动检测并加载项目上下文
```

### 手动操作
```
/project --init      # 初始化项目配置
/project --update    # 更新项目信息
/project --status    # 查看项目状态
/project --history   # 查看修改历史
```

### 跨项目查询
```
> 这个项目用的什么数据库？
> 上次在这个项目改了什么？
```

## 自动行为

1. **进入项目目录** → 加载 `.pi/config.json`
2. **运行测试** → 记录测试结果
3. **提交代码** → 记录提交内容
4. **发现依赖** → 更新 package 列表

## 项目缓存

每个项目会缓存：
- 上次会话状态
- 打开的文件
- git 分支信息
- 未完成的修改
