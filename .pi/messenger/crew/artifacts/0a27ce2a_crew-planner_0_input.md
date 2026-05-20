# Task for crew-planner

Create a task breakdown for implementing this request.

## Request

分析 pi agent 的 bash 命令为什么一直失败。

问题：
1. 执行任何 bash 命令都没有输出
2. 命令显示 "Command exited with code 1" 或没有输出
3. 用户环境：Windows 10, pi 从 PowerShell 启动，但 bash 工具实际使用 WSL

任务：
1. 检查 WSL 是否正确安装和配置
2. 检查 pi 的 bash 工具配置
3. 检查 PATH 环境变量
4. 找到解决方案让 bash 命令可以正常工作
5. 测试并验证修复

用户目录：C:\Users\17745
WSL 用户目录：/mnt/c/Users/17745

## Available Skills

Workers can load these skills on demand during task execution. When creating tasks, you may include a `skills` array with relevant skill names to help workers prioritize which to read.

  opencli-rs — |
  ppt-visual — Design presentation visuals and slide layouts. Create visual concepts, suggest graphics, and provide design specifications for impactful PowerPoint slides.
  slidev — Slidev - 使用 Markdown 创建幻灯片。支持 Vue、Reveal.js、MDX 组件。


You must follow this sequence strictly:
1) Understand the request
2) Review relevant code/docs/reference resources
3) Produce sequential implementation steps
4) Produce a parallel task graph

Return output in this exact section order and headings:
## 1. PRD Understanding Summary
## 2. Relevant Code/Docs/Resources Reviewed
## 3. Sequential Implementation Steps
## 4. Parallelized Task Graph

In section 4, include both:
- markdown task breakdown
- a `tasks-json` fenced block with task objects containing title, description, dependsOn, and optionally skills (array of skill names from the Available Skills list that are relevant to the task).