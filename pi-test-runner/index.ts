/**
 * pi-test-runner - 测试生成和运行
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { spawn } from "child_process";
import { join } from "path";
import { existsSync } from "fs";
import { readFile } from "fs/promises";

const FRAMEWORKS: Record<string, string[]> = {
  jest: ["npx", "jest"],
  vitest: ["npx", "vitest"],
  pytest: ["pytest"],
  gotest: ["go", "test"]
};

async function detectFramework(projectPath: string): Promise<string> {
  const pkgPath = join(projectPath, "package.json");
  
  if (existsSync(pkgPath)) {
    const pkg = JSON.parse(await readFile(pkgPath, "utf-8"));
    const deps = { ...pkg.dependencies, ...pkg.devDependencies };
    if (deps.vitest) return "vitest";
    if (deps.jest) return "jest";
  }
  
  if (existsSync(join(projectPath, "go.mod"))) return "gotest";
  if (existsSync(join(projectPath, "pytest.ini"))) return "pytest";
  
  return "jest";
}

async function runTests(projectPath: string, framework: string, coverage = false): Promise<string> {
  const cmd = FRAMEWORKS[framework];
  if (!cmd) {
    return `不支持的框架: ${framework}。支持: ${Object.keys(FRAMEWORKS).join(", ")}`;
  }

  const args = [...cmd];
  if (coverage) {
    if (framework === "jest" || framework === "vitest") args.push("--coverage");
    if (framework === "pytest") args.push("--cov");
  }

  return new Promise((resolve) => {
    const proc = spawn(args[0], args.slice(1), { cwd: projectPath, shell: true });
    
    let stdout = "";
    let stderr = "";
    
    proc.stdout?.on("data", (d) => { stdout += d.toString(); });
    proc.stderr?.on("data", (d) => { stderr += d.toString(); });
    
    proc.on("close", (code) => {
      resolve(`测试完成 (${framework})\n\nstdout:\n${stdout}\n\nstderr:\n${stderr}\n\nexit code: ${code}`);
    });
    
    proc.on("error", (err) => {
      resolve(`测试失败: ${err.message}`);
    });
  });
}

export default function (pi: ExtensionAPI): void {
  pi.registerCommand("test", {
    description: "运行测试 (jest, vitest, pytest, gotest)",
    handler: async (args: string) => {
      const argStr = args.trim();
      
      if (argStr.includes("--detect") || argStr === "") {
        const fw = await detectFramework(process.cwd());
        return `检测到测试框架: ${fw}\n\n运行: /test --run ${fw}`;
      }
      
      if (argStr.includes("--run")) {
        const fw = argStr.replace("--run", "").trim() || await detectFramework(process.cwd());
        const coverage = argStr.includes("--coverage");
        return await runTests(process.cwd(), fw, coverage);
      }
      
      return `测试命令:\n/test --detect     # 检测框架\n/test --run [框架] # 运行测试\n/test --coverage   # 覆盖率`;
    }
  });
}
