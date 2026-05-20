---
name: pi-user-profile
description: 用户档案系统。存储用户偏好、习惯、工作方式。记住用户的名字、时区、语言偏好等。
---

# Pi User Profile

用户档案和偏好设置。

## 文件结构

```
~/.pi/agent/
├── profile/           # 用户档案目录
│   ├── USER.md       # 主用户信息
│   ├── PREFERENCES.md # 偏好设置
│   ├── HABITS.md     # 使用习惯
│   └── CONTEXT.md    # 当前上下文
```

## 用户信息 (USER.md)

```markdown
---
name: 用户名
email: email@example.com
timezone: Asia/Shanghai
language: zh-CN
platform: windows
---

# 关于用户

## 基本信息
- 姓名：XXX
- 职业：XXX
- 时区：UTC+8

## 联系方式
- Telegram: @xxx
- Discord: xxx#1234
```

## 偏好设置 (PREFERENCES.md)

```markdown
# 用户偏好

## 包管理器
优先级：pnpm > npm > yarn

## 代码风格
- 使用 2 空格缩进
- 偏好单引号字符串
- 使用分号

## 输出格式
- 详细模式：开
- 确认危险操作：是

## AI 模型偏好
主要使用：Claude Sonnet 4
备用：Gemini 2.0 Pro
```

## 使用方法

```
> 叫我小明
> 我的时区是 UTC+9
> 以后都用 pnpm
```

## 自动收集

扩展会自动记录：
- 用户的命令选择
- 确认/拒绝的操作
- 常用的工作流程
- 偏好修改记录

## 触发时机

- 首次启动时询问用户信息
- 发现新偏好时自动学习
- `/profile` 查看当前档案
