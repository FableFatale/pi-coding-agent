/**
 * Pi Code Runner - 本地代码执行沙箱
 */

import { spawn } from "child_process";
import { join } from "path";
import { tmpdir } from "os";
import { writeFile, unlink } from "fs/promises";
import { existsSync } from "fs";

export interface RunOptions {
  timeout?: number;
  memoryLimit?: string;
  cwd?: string;
}

export interface RunResult {
  stdout: string;
  stderr: string;
  exitCode: number;
  duration: number;
}

const LANGUAGES: Record<string, { extension: string; command: string[]; args: (file: string) => string[] }> = {
  python: {
    extension: ".py",
    command: ["python"],
    args: (file) => [file]
  },
  javascript: {
    extension: ".js",
    command: ["node"],
    args: (file) => [file]
  },
  typescript: {
    extension: ".ts",
    command: ["npx", "tsx"],
    args: (file) => [file]
  },
  bash: {
    extension: ".sh",
    command: ["bash"],
    args: (file) => [file]
  },
  go: {
    extension: ".go",
    command: ["go", "run"],
    args: (file) => [file]
  }
};

export async function runCode(
  language: string,
  code: string,
  options: RunOptions = {}
): Promise<RunResult> {
  const lang = LANGUAGES[language.toLowerCase()];
  if (!lang) {
    throw new Error(`Unsupported language: ${language}`);
  }

  const { timeout = 30000, cwd = tmpdir() } = options;
  const file = join(cwd, `temp_${Date.now()}${lang.extension}`);
  
  try {
    await writeFile(file, code, "utf-8");
    
    const startTime = Date.now();
    const result = await executeProcess(lang.command[0], [...lang.args(file)], { timeout, cwd });
    const duration = Date.now() - startTime;
    
    return {
      stdout: result.stdout,
      stderr: result.stderr,
      exitCode: result.exitCode,
      duration
    };
  } finally {
    try {
      await unlink(file);
    } catch {
      // ignore cleanup errors
    }
  }
}

function executeProcess(
  command: string,
  args: string[],
  options: { timeout: number; cwd: string }
): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  return new Promise((resolve, reject) => {
    let stdout = "";
    let stderr = "";
    let killed = false;

    const proc = spawn(command, args, {
      cwd: options.cwd,
      shell: true,
      env: { ...process.env }
    });

    proc.stdout?.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr?.on("data", (data) => {
      stderr += data.toString();
    });

    const timeout = setTimeout(() => {
      killed = true;
      proc.kill("SIGTERM");
    }, options.timeout);

    proc.on("close", (code) => {
      clearTimeout(timeout);
      resolve({
        stdout,
        stderr,
        exitCode: killed ? -1 : (code || 0)
      });
    });

    proc.on("error", (err) => {
      clearTimeout(timeout);
      reject(err);
    });
  });
}
