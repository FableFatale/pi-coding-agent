/**
 * pi-debugger - 断点调试
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { spawn, type ChildProcess } from "child_process";

interface Breakpoint {
  file: string;
  line: number;
  condition?: string;
}

class CodeDebugger {
  private proc: ChildProcess | null = null;
  private breakpoints: Map<string, Breakpoint[]> = new Map();

  async launch(file: string, language: "node" | "python" = "node"): Promise<string> {
    const args = language === "node" 
      ? ["node", "--inspect", file]
      : ["python", "-m", "debugpy", "--listen", "localhost:5678", file];

    this.proc = spawn(args[0], args.slice(1), { stdio: "inherit" });

    this.proc.on("close", () => { this.proc = null; });
    
    return `调试会话已启动: ${file}\n等待 debugger 连接...`;
  }

  async setBreak(file: string, line: number, condition?: string): Promise<string> {
    if (!this.breakpoints.has(file)) {
      this.breakpoints.set(file, []);
    }
    this.breakpoints.get(file)!.push({ file, line, condition });
    return `断点已设置: ${file}:${line}${condition ? ` (条件: ${condition})` : ""}`;
  }

  async listBreaks(): Promise<string> {
    if (this.breakpoints.size === 0) return "暂无断点";
    
    let result = "当前断点:\n";
    for (const [file, bps] of this.breakpoints) {
      for (const bp of bps) {
        result += `  ${file}:${bp.line}${bp.condition ? ` (条件: ${bp.condition})` : ""}\n`;
      }
    }
    return result;
  }

  kill(): void {
    if (this.proc) {
      this.proc.kill();
      this.proc = null;
    }
  }

  isRunning(): boolean {
    return this.proc !== null;
  }
}

const dbg = new CodeDebugger();

export default function (pi: ExtensionAPI): void {
  pi.registerCommand("debug", {
    description: "断点调试 (node, python)",
    handler: async (args: string) => {
      const argStr = args.trim();
      
      if (argStr.includes("--launch")) {
        const parts = argStr.replace("--launch", "").trim().split(/\s+/);
        const file = parts[0];
        const lang = (parts[1] as "node" | "python") || "node";
        
        if (!file) {
          return "用法: /debug --launch <文件> [语言]\n例如: /debug --launch app.js node";
        }
        
        try {
          return await dbg.launch(file, lang);
        } catch (err: any) {
          return `启动失败: ${err.message}`;
        }
      }
      
      if (argStr.includes("--break")) {
        const match = argStr.match(/--break\s+(?:(\S+):)?(\d+)(?:\s+--condition\s+(.+))?/);
        if (!match) {
          return "用法: /debug --break [文件:]行号 [--condition 条件]";
        }
        
        const [, file, line, condition] = match;
        return await dbg.setBreak(file || "当前文件", parseInt(line), condition);
      }
      
      if (argStr.includes("--list")) return await dbg.listBreaks();
      if (argStr.includes("--kill")) { dbg.kill(); return "调试会话已终止"; }
      if (argStr.includes("--status")) return dbg.isRunning() ? "调试会话运行中" : "无活动调试会话";
      
      return `调试命令:\n/debug --launch <文件> [语言]  # 启动\n/debug --break [文件:]行号      # 断点\n/debug --break --condition 条件  # 条件断点\n/debug --list                  # 列表\n/debug --kill                  # 终止\n/debug --status                # 状态`;
    }
  });
}
