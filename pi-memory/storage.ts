/**
 * 共享存储工具（无依赖，纯函数）
 */
import { readFile, writeFile, mkdir } from "fs/promises";
import { join } from "path";
import { homedir } from "os";
import { existsSync, readFileSync } from "fs";

export const MEMORY_DIR = join(homedir(), ".pi", "agent", "memory");

export async function ensureDir(path: string): Promise<void> {
  if (!existsSync(path)) {
    await mkdir(path, { recursive: true });
  }
}

export async function readMemoryFile(name: string): Promise<string> {
  const filePath = join(MEMORY_DIR, name);
  if (existsSync(filePath)) {
    return await readFile(filePath, "utf-8");
  }
  return "";
}

export async function writeMemoryFile(name: string, content: string): Promise<void> {
  await ensureDir(MEMORY_DIR);
  await writeFile(join(MEMORY_DIR, name), content, "utf-8");
}

export function readMemoryFileSync(name: string): string {
  const filePath = join(MEMORY_DIR, name);
  if (existsSync(filePath)) {
    return readFileSync(filePath, "utf-8");
  }
  return "";
}
