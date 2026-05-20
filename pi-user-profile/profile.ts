/**
 * pi-user-profile - 用户档案系统
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { readFile, writeFile, existsSync } from "fs/promises";
import { join } from "path";
import { homedir } from "os";

const PROFILE_DIR = join(homedir(), ".pi", "agent", "profile");

interface UserProfile {
  name?: string;
  email?: string;
  timezone?: string;
  language?: string;
  platform?: string;
}

async function initProfileDir(): Promise<void> {
  const { mkdir } = await import("fs/promises");
  await mkdir(PROFILE_DIR, { recursive: true });
  
  const files = ["USER.md", "PREFERENCES.md", "HABITS.md"];
  for (const file of files) {
    const path = join(PROFILE_DIR, file);
    if (!existsSync(path)) {
      await writeFile(path, `---
name: 
timezone: Asia/Shanghai
language: zh-CN
platform: windows
---
# ${file.replace(".md", "")}\n\n`, "utf-8");
    }
  }
}

async function getProfile(): Promise<UserProfile | null> {
  const file = join(PROFILE_DIR, "USER.md");
  if (!existsSync(file)) return null;
  const content = await readFile(file, "utf-8");
  return parseYamlFrontmatter(content) as UserProfile;
}

function parseYamlFrontmatter(content: string): Record<string, string> {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return {};
  const result: Record<string, string> = {};
  for (const line of match[1].split("\n")) {
    const [key, ...valueParts] = line.split(":");
    if (key && valueParts.length) {
      result[key.trim()] = valueParts.join(":").trim();
    }
  }
  return result;
}

export default function (pi: ExtensionAPI): void {
  initProfileDir().catch(() => {});

  pi.registerCommand("profile", {
    description: "用户档案管理",
    handler: async (args: string) => {
      const argStr = args.trim();
      
      if (argStr === "" || argStr === "--read") {
        const profile = await getProfile();
        if (!profile) return "用户档案未找到";
        return `## 用户档案\n\n${Object.entries(profile).map(([k, v]) => `- **${k}**: ${v || "(未设置)"}`).join("\n")}`;
      }
      
      if (argStr.startsWith("--set ")) {
        const parts = argStr.replace("--set ", "").split(" ");
        if (parts.length < 2) return "用法: /profile --set <key> <value>";
        const [key, ...valueParts] = parts;
        const value = valueParts.join(" ");
        const file = join(PROFILE_DIR, "USER.md");
        let content = await readFile(file, "utf-8").catch(() => "");
        const regex = new RegExp(`^${key}:.*$`, "m");
        if (regex.test(content)) {
          content = content.replace(regex, `${key}: ${value}`);
        } else {
          content += `\n${key}: ${value}`;
        }
        await writeFile(file, content, "utf-8");
        return `已更新: ${key} = ${value}`;
      }
      
      if (argStr.startsWith("--learn ")) {
        const content = argStr.replace("--learn ", "");
        const file = join(PROFILE_DIR, "HABITS.md");
        const existing = await readFile(file, "utf-8").catch(() => "# HABITS\n\n");
        await writeFile(file, existing + `\n## ${new Date().toISOString()}\n${content}\n`, "utf-8");
        return "习惯已记录";
      }
      
      return `档案命令:\n/profile --read           # 读取档案\n/profile --set <键> <值>   # 更新字段\n/profile --learn <内容>    # 记录习惯`;
    }
  });
}
