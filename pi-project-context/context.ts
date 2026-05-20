/**
 * pi-project-context - 项目上下文系统
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { readFile, writeFile, existsSync } from "fs/promises";
import { join, resolve, dirname } from "path";
import { createHash } from "crypto";

const CACHE_DIR = join(process.env.HOME || process.env.USERPROFILE || "", ".pi", "agent", "project-cache");

interface ProjectInfo {
  name: string;
  path: string;
  packageManager?: string;
  framework?: string;
  typescript: boolean;
  detected: string;
}

async function exists(path: string): Promise<boolean> {
  try {
    return existsSync(path);
  } catch {
    return false;
  }
}

async function detectProject(cwd: string): Promise<ProjectInfo> {
  let dir = resolve(cwd);
  const root = dirname(dir);
  
  while (dir !== root) {
    const pkgPath = join(dir, "package.json");
    if (await exists(pkgPath)) {
      const pkg = JSON.parse(await readFile(pkgPath, "utf-8"));
      const tsconfig = await exists(join(dir, "tsconfig.json"));
      const pm = await exists(join(dir, "pnpm-lock.yaml")) ? "pnpm"
        : await exists(join(dir, "yarn.lock")) ? "yarn"
        : await exists(join(dir, "package-lock.json")) ? "npm" : undefined;
      
      return {
        name: pkg.name || "unnamed",
        path: dir,
        packageManager: pm,
        framework: pkg.framework || detectFramework(pkg),
        typescript: tsconfig,
        detected: new Date().toISOString()
      };
    }
    dir = dirname(dir);
  }
  
  return {
    name: "unknown",
    path: cwd,
    typescript: false,
    detected: new Date().toISOString()
  };
}

function detectFramework(pkg: any): string | undefined {
  const deps = { ...pkg.dependencies, ...pkg.devDependencies };
  if (deps.next) return "next";
  if (deps.nuxt) return "nuxt";
  if (deps.express) return "express";
  if (deps.fastify) return "fastify";
  if (deps.react) return "react";
  if (deps.vue) return "vue";
  if (deps.angular) return "angular";
  return undefined;
}

export default function (pi: ExtensionAPI): void {
  pi.registerCommand("context", {
    description: "项目上下文管理",
    handler: async (args: string) => {
      const argStr = args.trim();
      const cwd = process.cwd();
      
      if (argStr === "" || argStr === "--detect") {
        const info = await detectProject(cwd);
        return `## 项目上下文\n\n- **名称**: ${info.name}\n- **路径**: ${info.path}\n- **包管理器**: ${info.packageManager || "(未检测到)"}\n- **框架**: ${info.framework || "(未检测到)"}\n- **TypeScript**: ${info.typescript ? "是" : "否"}`;
      }
      
      if (argStr === "--cache") {
        const hash = createHash("sha256").update(cwd).digest("hex").slice(0, 8);
        const cachePath = join(CACHE_DIR, `${hash}.json`);
        const info = await detectProject(cwd);
        await writeFile(cachePath, JSON.stringify(info, null, 2), "utf-8").catch(() => {});
        return `上下文已缓存: ${hash}`;
      }
      
      if (argStr.startsWith("--load ")) {
        const hash = argStr.replace("--load ", "").trim();
        const cachePath = join(CACHE_DIR, `${hash}.json`);
        if (await exists(cachePath)) {
          const info = JSON.parse(await readFile(cachePath, "utf-8"));
          return `## 加载的项目\n\n${JSON.stringify(info, null, 2)}`;
        }
        return `未找到缓存: ${hash}`;
      }
      
      return `上下文命令:\n/context --detect   # 检测当前项目\n/context --cache    # 缓存当前项目\n/context --load <hash> # 加载缓存项目`;
    }
  });
}
