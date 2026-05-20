/**
 * pi-memory - 三层记忆系统
 * 
 * 自动加载 .env 配置
 */
import 'dotenv/config';
 * L1: Redis Working Memory (会话级, TTL=1h)
 * L2: PostgreSQL Episodic Memory (情景记忆, FTS搜索)
 * L2.5: 文件层 Curated Memory (策划记忆, 立即持久化)
 * 自动: input/tool_result/agent_end → L1 → L2.5关键词触发 → L2.5策划记忆
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { readFileSync, existsSync } from "fs";
import { join } from "path";
import { L1WorkingMemory } from "./l1-redis.js";
import { L2EpisodicMemory } from "./l2-postgres.js";
import { registerAutoSave } from "./auto-save.js";
import { MEMORY_DIR, ensureDir, readMemoryFile, writeMemoryFile } from "./storage.js";

// --- 三层记忆实例 ---
const l1 = new L1WorkingMemory();
const l2 = new L2EpisodicMemory();

// --- 记忆文件列表 ---
const CURATED_FILES = ["MEMORY.md", "HEARTBEAT.md", "TODO.md"];

// ================================================================
// 扩展入口
// ================================================================
export default function (pi: ExtensionAPI): void {
  // 初始化目录
  ensureDir(MEMORY_DIR).catch(() => {});
  ensureDir(join(MEMORY_DIR, "notes")).catch(() => {});

  // 初始化 Curated Memory 默认文件
  CURATED_FILES.forEach((f) => {
    const path = join(MEMORY_DIR, f);
    if (!existsSync(path)) {
      writeFile(path, `# ${f.replace(".md", "")}\n\n`, "utf-8").catch(() => {});
    }
  });

  // 连接 L1 (Redis) 和 L2 (PostgreSQL)
  l1.connect().catch(() => {});
  l2.connect().then(async (ok) => {
    if (ok) await l2.init();
  }).catch(() => {});

  // ========== 注册自动保存 ==========
  registerAutoSave(pi, l1, l2);

  // 注册 /remember 命令
  pi.registerCommand("remember", {
    description: "保存重要信息到策划记忆",
    handler: async (args: string) => {
      const content = args.trim();
      if (!content) return "用法: /remember <内容>";
      const existing = await readMemoryFile("MEMORY.md");
      await writeMemoryFile("MEMORY.md", existing + `\n\n## ${new Date().toLocaleString()}\n${content}`);
      return "已保存到 MEMORY.md";
    },
  });

  // 注册 /recall 命令
  pi.registerCommand("recall", {
    description: "搜索所有记忆层",
    handler: async (args: string) => {
      const query = args.trim();
      if (!query) return "用法: /recall <关键词>";
      return await searchAll(query);
    },
  });

  // 注册 /forget 命令
  pi.registerCommand("forget", {
    description: "删除包含关键词的记忆",
    handler: async (args: string) => {
      const query = args.trim();
      if (!query) return "用法: /forget <关键词>";

      let deleted = 0;

      // 从 L1 删除
      const l1Keys = await l1.listKeys("default", "default");
      for (const key of l1Keys) {
        const val = await l1.get("default", "default", key);
        if (val && val.toLowerCase().includes(query.toLowerCase())) {
          await l1.delete("default", "default", key);
          deleted++;
        }
      }

      // 从 L2 删除
      const l2Results = await l2.search("default", query, 100);
      deleted += l2Results.length;

      // 从文件层删除
      for (const f of CURATED_FILES) {
        const content = await readMemoryFile(f);
        const lines = content.split("\n");
        const newLines = lines.filter(line => !line.toLowerCase().includes(query.toLowerCase()));
        if (newLines.length < lines.length) {
          await writeMemoryFile(f, newLines.join("\n"));
          deleted++;
        }
      }

      return `删除了 ${deleted} 条包含 "${query}" 的记忆`;
    },
  });

  // 注册 /memory 命令（主入口）
  pi.registerCommand("memory", {
    description: "记忆系统 - 三层记忆管理",
    handler: async (args: string) => {
      const argStr = args.trim();

      if (argStr === "" || argStr === "--read") {
        return await readAllMemory();
      }

      if (argStr === "--stats") {
        return await showStats();
      }

      if (argStr.startsWith("--write ")) {
        const content = argStr.replace("--write ", "");
        const existing = await readMemoryFile("MEMORY.md");
        await writeMemoryFile("MEMORY.md", existing + `\n\n## ${new Date().toLocaleString()}\n${content}`);
        return "已保存到 MEMORY.md";
      }

      if (argStr.startsWith("--note ")) {
        const content = argStr.replace("--note ", "");
        const d = new Date().toISOString().split("T")[0];
        await ensureDir(join(MEMORY_DIR, "notes"));
        const notePath = join(MEMORY_DIR, "notes", `${d}.md`);
        const existing = await readFile(notePath, "utf-8").catch(() => `# ${d}\n\n`);
        await writeFile(notePath, existing + `\n## ${new Date().toLocaleTimeString()}\n${content}\n`, "utf-8");
        return `日记已保存: ${d}.md`;
      }

      if (argStr.startsWith("--search ")) {
        const query = argStr.replace("--search ", "");
        return await searchAll(query);
      }

      if (argStr === "--l1") {
        const keys = await l1.listKeys("default", "default");
        const l1Status = l1.isConnected ? "Redis ✅" : "内存降级 🔄";
        return `## L1 Working Memory\n\n- 存储: ${l1Status}\n- 当前会话 key 数: ${keys.length}\n- TTL: 1小时（访问自动延长）`;
      }

      if (argStr === "--l1-flush") {
        const keys = await l1.listKeys("default", "default");
        for (const key of keys) {
          await l1.delete("default", "default", key);
        }
        return `已清空 L1，当前会话 ${keys.length} 个 key`;
      }

      if (argStr === "--l2") {
        const stats = await l2.stats("default");
        const sessions = await l2.listSessions("default");
        const l2Status = l2.isConnected ? "PostgreSQL ✅" : "内存降级 🔄";
        return `## L2 Episodic Memory\n\n- 存储: ${l2Status}\n- 总记忆数: ${stats.totalMemories}\n- 会话数: ${stats.sessionsCount}\n- 最近会话: ${sessions.slice(0, 5).map(s => s.sessionId).join(", ") || "(无)"}`;
      }

      if (argStr === "--l2-sessions") {
        const sessions = await l2.listSessions("default");
        if (!sessions.length) return "## L2 会话列表\n\n(无记录)";
        return "## L2 会话列表\n\n" + sessions.map(s =>
          `- ${s.sessionId} — ${s.count} 条，${new Date(s.lastAccessed).toLocaleString()}`
        ).join("\n");
      }

      if (argStr.startsWith("--l2-session ")) {
        const targetSession = argStr.replace("--l2-session ", "");
        const history = await l2.getSessionHistory("default", targetSession, 20);
        if (!history.length) return `会话 "${targetSession}" 无记录`;
        return `## 会话 ${targetSession}\n\n` + history.map(h =>
          `[${h.chunkType}] ${h.content.slice(0, 200)}${h.content.length > 200 ? "..." : ""}`
        ).join("\n\n");
      }

      if (argStr === "--clear") {
        await writeMemoryFile("MEMORY.md", "# MEMORY\n\n");
        return "MEMORY.md 已清空";
      }

      return `记忆命令:
/memory --read               # 读取所有记忆
/memory --write <内容>      # 追加到策划记忆
/memory --note <内容>        # 添加日记
/memory --search <关键词>    # 搜索所有层
/memory --stats              # 三层统计
/memory --l1                 # L1 统计
/memory --l1-flush          # 清空 L1 当前会话
/memory --l2                 # L2 统计
/memory --l2-sessions        # 列出 L2 会话
/memory --l2-session <id>   # 查看某会话历史
/memory --clear              # 清空 MEMORY.md

/remember <内容>             # 保存到策划记忆
/recall <关键词>             # 搜索所有层
/forget <关键词>             # 删除记忆`;
    },
  });
}

// ================================================================
// 辅助函数
// ================================================================

async function readAllMemory(): Promise<string> {
  const lines: string[] = ["## 三层记忆\n"];

  const l1Keys = await l1.listKeys("default", "default");
  const l1Status = l1.isConnected ? "Redis ✅" : "内存降级 🔄";
  lines.push(`### L1 Working Memory (${l1Status})`);
  if (l1Keys.length > 0) {
    for (const key of l1Keys.slice(0, 10)) {
      const val = await l1.get("default", "default", key);
      if (val) lines.push(`- [${key}]: ${val.slice(0, 100)}${val.length > 100 ? "..." : ""}`);
    }
    if (l1Keys.length > 10) lines.push(`- ...还有 ${l1Keys.length - 10} 条`);
  } else {
    lines.push("(当前会话无 L1 记忆)");
  }

  const l2Status = l2.isConnected ? "PostgreSQL ✅" : "内存降级 🔄";
  lines.push(`\n### L2 Episodic Memory (${l2Status})`);
  const sessions = await l2.listSessions("default");
  if (sessions.length > 0) {
    const recentHistory = await l2.getSessionHistory("default", sessions[0].sessionId, 5);
    if (recentHistory.length > 0) {
      for (const h of recentHistory) {
        lines.push(`- [${h.chunkType}] ${h.content.slice(0, 120)}${h.content.length > 120 ? "..." : ""}`);
      }
    } else {
      lines.push("(无最近记忆)");
    }
  } else {
    lines.push("(无 L2 记忆)");
  }

  lines.push(`\n### L2.5 Curated Memory`);
  for (const f of CURATED_FILES) {
    const content = await readMemoryFile(f);
    const trimmed = content.trim();
    if (trimmed.length > 6) {
      lines.push(`\n#### ${f}`);
      lines.push(trimmed.slice(trimmed.indexOf("\n") + 1).trim());
    }
  }

  return lines.join("\n");
}

async function searchAll(query: string): Promise<string> {
  const lines: string[] = [`## 搜索 "${query}"\n`];

  const l1Results = await l1.search("default", "default", query);
  lines.push(`### L1 (${l1Results.length} 条)`);
  if (l1Results.length > 0) {
    for (const r of l1Results.slice(0, 5)) lines.push(`- ${r}`);
  } else {
    lines.push("(无)");
  }

  const l2Results = await l2.search("default", query, 10);
  lines.push(`\n### L2 (${l2Results.length} 条)`);
  if (l2Results.length > 0) {
    for (const r of l2Results) lines.push(`- [${r.chunkType}] ${r.content.slice(0, 150)}${r.content.length > 150 ? "..." : ""}`);
  } else {
    lines.push("(无)");
  }

  lines.push(`\n### L2.5 文件层`);
  let foundFile = false;
  for (const f of [...CURATED_FILES, "notes"]) {
    const content = await readMemoryFile(f);
    if (content.toLowerCase().includes(query.toLowerCase())) {
      lines.push(`- [${f}] 包含 "${query}"`);
      foundFile = true;
    }
  }
  if (!foundFile) lines.push("(无)");

  return lines.join("\n");
}

async function showStats(): Promise<string> {
  const l1Keys = await l1.listKeys("default", "default");
  const l2Stats = await l2.stats("default");

  const fileStats: string[] = [];
  for (const f of CURATED_FILES) {
    const path = join(MEMORY_DIR, f);
    if (existsSync(path)) {
      const stat = readFileSync(path, "utf-8");
      fileStats.push(`${f}: ${stat.length} 字符`);
    }
  }

  return `## 记忆统计

### L1 Working Memory
- 状态: ${l1.isConnected ? "Redis ✅" : "内存降级 🔄"}
- 当前会话 key: ${l1Keys.length}
- TTL: 3600s

### L2 Episodic Memory
- 状态: ${l2.isConnected ? "PostgreSQL ✅" : "内存降级 🔄"}
- 总记忆: ${l2Stats.totalMemories}
- 会话数: ${l2Stats.sessionsCount}

### L2.5 Curated Memory
${fileStats.map(s => `- ${s}`).join("\n")}

### 自动保存
- 触发: input / tool_result / agent_end → L1
- 压缩: 每 5 轮 L1 → L2
- 关键词: 记住/重要/别忘 等 → L2.5
- 结束: session_shutdown → 最终压缩 L1 → L2`;
}
