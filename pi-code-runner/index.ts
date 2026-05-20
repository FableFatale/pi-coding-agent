/**
 * pi-code-runner - 本地代码执行沙箱
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { spawn } from "child_process";
import { join } from "path";
import { tmpdir } from "os";
import { writeFile, unlink } from "fs/promises";

interface RunResult {
  stdout: string;
  stderr: string;
  exitCode: number;
  duration: number;
}

const LANGUAGES: Record<string, { extension: string; command: string[] }> = {
  python: { extension: ".py", command: ["python"] },
  javascript: { extension: ".js", command: ["node"] },
  typescript: { extension: ".ts", command: ["npx", "tsx"] },
  bash: { extension: ".sh", command: ["bash"] },
  go: { extension: ".go", command: ["go", "run"] }
};

async function runCode(language: string, code: string, timeout = 30000): Promise<string> {
  const lang = LANGUAGES[language.toLowerCase()];
  
  if (!lang) {
    return `不支持的语言: ${language}。支持: ${Object.keys(LANGUAGES).join(", ")}`;
  }

  const file = join(tmpdir(), `temp_${Date.now()}${lang.extension}`);
  
  try {
    await writeFile(file, code, "utf-8");
    
    const startTime = Date.now();
    const result = await executeProcess(lang.command[0], [...lang.command.slice(1), file], timeout);
    const duration = Date.now() - startTime;
    
    return `执行完成 (${duration}ms)\n\nstdout:\n${result.stdout}\n\nstderr:\n${result.stderr}\n\nexit code: ${result.exitCode}`;
  } finally {
    try {
      await unlink(file);
    } catch {
      // ignore
    }
  }
}

function executeProcess(
  command: string,
  args: string[],
  timeout: number
): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  return new Promise((resolve) => {
    let stdout = "";
    let stderr = "";
    let killed = false;

    const proc = spawn(command, args, { shell: true, env: { ...process.env } });

    proc.stdout?.on("data", (data) => { stdout += data.toString(); });
    proc.stderr?.on("data", (data) => { stderr += data.toString(); });

    const timer = setTimeout(() => {
      killed = true;
      proc.kill("SIGTERM");
    }, timeout);

    proc.on("close", (code) => {
      clearTimeout(timer);
      resolve({ stdout, stderr, exitCode: killed ? -1 : (code || 0) });
    });

    proc.on("error", (err) => {
      clearTimeout(timer);
      resolve({ stdout, stderr, exitCode: -1 });
    });
  });
}

export default function (pi: ExtensionAPI): void {
  pi.registerCommand("run", {
    description: "运行代码 (python, javascript, bash, go)",
    handler: async (args: string) => {
      const parts = args.trim().split(/\s+/);
      if (parts.length < 2) {
        return "用法: /run <语言> <代码>\n例如: /run python print('hello')";
      }
      const language = parts[0];
      const code = parts.slice(1).join(" ");
      return await runCode(language, code);
    }
  });
}
