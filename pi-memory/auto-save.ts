/**
 * 自动保存三层记忆
 *
 * L1 (Redis): 每个 tool_result / input / agent_response 自动存入
 * L1 → L2: 每 N 轮自动 compress 并持久化到 PG
 * L2.5: 关键词触发自动写入策划记忆
 */

import { L1WorkingMemory } from "./l1-redis.js";
import { L2EpisodicMemory } from "./l2-postgres.js";
import { readMemoryFile, writeMemoryFile, ensureDir } from "./storage.js";
import { homedir } from "os";
import { join } from "path";
import { existsSync } from "fs";
import type { ExtensionAPI, ExtensionContext } from "@mariozechner/pi-coding-agent";
import type { InputEvent, ToolExecutionEndEvent, AgentEndEvent } from "@mariozechner/pi-coding-agent";

const MEMORY_DIR = join(homedir(), ".pi", "agent", "memory");
const USER_ID = "default";
const COMPRESS_EVERY_N_TURNS = 5;  // 每 N 轮压缩一次 L1 → L2
const L1_KEEP_RECENT = 20;           // 压缩时保留最近 N 条

// 触发写入 L2.5 的关键词
const CURATED_TRIGGERS = [
  "记住", "重要", "别忘", "要记住", "必须记住", "一定要",
  "记下来", "帮我记", "don't forget", "remember to", "important",
  "别忘了", "notebook", "mark it", "save this", "收藏",
  "后续要用", "以后需要", "长期有效",
];

// 记录当前会话状态
let currentSessionId = "";
let turnCount = 0;
let pendingUserMsg = "";

// L1/L2 实例（从 memory.ts 共享）
let l1: L1WorkingMemory;
let l2: L2EpisodicMemory;

/**
 * 从文本中提取关键词作为 tags
 */
function extractTags(text: string): string[] {
  const tags: string[] = [];
  // 提取 #标签
  const hashMatches = text.match(/#(\w+)/g);
  if (hashMatches) tags.push(...hashMatches.map(t => t.slice(1)));
  // 提取 @mentions
  const atMatches = text.match(/@(\w+)/g);
  if (atMatches) tags.push(...atMatches.map(t => t.slice(1)));
  return tags;
}

/**
 * 检查文本是否包含策划记忆触发词
 */
function hasCuratedTrigger(text: string): boolean {
  return CURATED_TRIGGERS.some(trigger =>
    text.toLowerCase().includes(trigger.toLowerCase())
  );
}

/**
 * 保存到 L1 (Redis)
 */
async function saveToL1(key: string, content: string): Promise<void> {
  if (!currentSessionId) currentSessionId = `session-${Date.now()}`;
  try {
    await l1.set(USER_ID, currentSessionId, key, content);
  } catch (e) {
    console.warn("[AutoSave] L1 save failed:", e);
  }
}

/**
 * L1 → L2 压缩持久化
 */
async function compressL1ToL2(): Promise<void> {
  if (!currentSessionId) return;
  try {
    const archived = await l1.compress(USER_ID, currentSessionId, L1_KEEP_RECENT);
    if (archived.length > 0) {
      await l2.storeBatch(USER_ID, currentSessionId, archived.map(c => ({
        content: c,
        chunkType: "archived",
        tags: [],
      })));
      console.log(`[AutoSave] Compressed ${archived.length} entries to L2`);
    }
  } catch (e) {
    console.warn("[AutoSave] L1→L2 compress failed:", e);
  }
}

/**
 * 关键词触发 → 自动写 L2.5
 */
async function autoWriteCurated(text: string): Promise<void> {
  if (!hasCuratedTrigger(text)) return;
  try {
    const existing = await readMemoryFile("MEMORY.md");
    const timestamp = new Date().toLocaleString();
    await writeMemoryFile("MEMORY.md", existing + `\n\n## ${timestamp} [自动]\n${text}`);
    console.log("[AutoSave] Auto-saved to L2.5 (Curated Memory)");
  } catch (e) {
    console.warn("[AutoSave] L2.5 auto-write failed:", e);
  }
}

/**
 * 注册自动保存事件
 */
export function registerAutoSave(pi: ExtensionAPI, l1Instance: L1WorkingMemory, l2Instance: L2EpisodicMemory): void {
  l1 = l1Instance;
  l2 = l2Instance;

  // session 开始 → 生成新 sessionId
  pi.on("session_start", async () => {
    currentSessionId = `session-${Date.now()}`;
    turnCount = 0;
    pendingUserMsg = "";
    console.log(`[AutoSave] Session started: ${currentSessionId}`);
  });

  // session 结束 → 压缩 L1 → L2
  pi.on("session_shutdown", async () => {
    console.log("[AutoSave] Session shutdown, flushing L1→L2...");
    await compressL1ToL2();
  });

  // 用户输入 → 保存到 L1，检查是否触发 L2.5
  pi.on("input", async (event: InputEvent) => {
    if (!event.text?.trim()) return;
    pendingUserMsg = event.text.trim().slice(0, 500);  // 截断防超长
    turnCount++;

    // 保存到 L1
    await saveToL1(`input_${Date.now()}`, `USER: ${pendingUserMsg}`);

    // 触发词 → L2.5
    await autoWriteCurated(pendingUserMsg);

    // 每 N 轮自动压缩
    if (turnCount % COMPRESS_EVERY_N_TURNS === 0) {
      await compressL1ToL2();
    }
  });

  // 工具执行结束 → 工具输出保存到 L1
  pi.on("tool_execution_end", async (event: ToolExecutionEndEvent) => {
    if (!currentSessionId) return;

    // 只保存关键工具的输出
    const importantTools = ["bash", "read", "grep", "find", "edit", "write"];
    if (!importantTools.includes(event.toolName)) return;

    // 截断大输出
    let result = "";
    try {
      result = typeof event.result === "string"
        ? event.result
        : JSON.stringify(event.result);
    } catch {
      result = String(event.result);
    }
    result = result.slice(0, 2000);  // 截断到 2KB

    if (!result.trim()) return;

    const key = `${event.toolName}_${event.toolCallId}`;
    await saveToL1(key, `[TOOL: ${event.toolName}]\n${result}`);

    // 如果是重要工具的输出，检查触发词
    await autoWriteCurated(result);
  });

  // agent 响应结束 → 保存到 L1
  pi.on("agent_end", async (event: AgentEndEvent) => {
    if (!currentSessionId) return;

    // 提取 assistant 消息内容
    const assistantMessages = event.messages.filter(m => m.role === "assistant");
    if (assistantMessages.length === 0) return;

    const lastAssistant = assistantMessages[assistantMessages.length - 1];
    const parts: string[] = [];

    for (const content of lastAssistant.content) {
      if (content.type === "text") {
        parts.push(content.text);
      }
    }

    const responseText = parts.join("\n").slice(0, 2000);
    if (!responseText.trim()) return;

    await saveToL1(`agent_${Date.now()}`, `AGENT:\n${responseText}`);

    // 结合用户输入检查触发词（用户说了 + agent 回答了）
    if (pendingUserMsg) {
      const combined = `${pendingUserMsg}\n${responseText}`;
      await autoWriteCurated(combined);
      pendingUserMsg = "";
    }
  });

  console.log("[AutoSave] Auto-save registered");
}
