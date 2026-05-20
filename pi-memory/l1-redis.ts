/**
 * L1: Working Memory (Redis)
 * 
 * 特性:
 * - TTL=1小时，访问自动延长
 * - 短期会话信息存储
 * - 自动压缩防止溢出
 */

import Redis from "ioredis";

const WORKING_TTL = 3600; // 1小时

export interface WorkingMemoryEntry {
  key: string;
  value: string;
  createdAt: number;
  accessedAt: number;
}

export class L1WorkingMemory {
  private redis: Redis | null = null;
  private connected = false;
  private fallback = new Map<string, { value: string; expires: number }>();

  /**
   * 连接 Redis
   */
  async connect(host?: string, port?: number): Promise<boolean> {
    // 从环境变量读取
    const redisHost = host || process.env.REDIS_HOST || "127.0.0.1";
    const redisPort = port || parseInt(process.env.REDIS_PORT || "6379");
    
    try {
      this.redis = new Redis({ host: redisHost, port: redisPort, lazyConnect: true, maxRetriesPerRequest: 1 });
      await this.redis.ping();
      this.connected = true;
      console.log("[L1] Redis connected");
      return true;
    } catch {
      this.connected = false;
      this.redis = null;
      console.log("[L1] Redis not available, using in-memory fallback");
      return false;
    }
  }

  /**
   * 保存工作记忆
   */
  async set(userId: string, sessionId: string, key: string, value: string): Promise<void> {
    const fullKey = this.buildKey(userId, sessionId, key);
    const metadata = JSON.stringify({ createdAt: Date.now(), accessedAt: Date.now() });
    
    if (this.redis && this.connected) {
      await this.redis.setex(fullKey, WORKING_TTL, metadata + "\n" + value);
      await this.redis.setex(fullKey + ":_meta", WORKING_TTL, metadata);
    } else {
      this.fallback.set(fullKey, { value: metadata + "\n" + value, expires: Date.now() + WORKING_TTL * 1000 });
    }
  }

  /**
   * 读取工作记忆（访问时自动延长 TTL）
   */
  async get(userId: string, sessionId: string, key: string): Promise<string | null> {
    const fullKey = this.buildKey(userId, sessionId, key);
    
    if (this.redis && this.connected) {
      const data = await this.redis.get(fullKey);
      if (data) {
        // 访问时自动延长 TTL
        await this.redis.expire(fullKey, WORKING_TTL);
        const lines = data.split("\n");
        lines.shift(); // 去掉 metadata 行
        return lines.join("\n");
      }
      return null;
    } else {
      const entry = this.fallback.get(fullKey);
      if (!entry) return null;
      if (Date.now() > entry.expires) {
        this.fallback.delete(fullKey);
        return null;
      }
      // 访问时自动延长
      entry.expires = Date.now() + WORKING_TTL * 1000;
      const lines = entry.value.split("\n");
      lines.shift();
      return lines.join("\n");
    }
  }

  /**
   * 搜索工作记忆（模糊匹配 key）
   */
  async search(userId: string, sessionId: string, pattern: string): Promise<string[]> {
    const prefix = `wm:${userId}:${sessionId}:`;
    const results: string[] = [];

    if (this.redis && this.connected) {
      const keys = await this.redis.keys(prefix + "*");
      for (const k of keys) {
        if (k.endsWith(":_meta")) continue;
        const key = k.replace(prefix, "");
        if (pattern === "*" || key.includes(pattern)) {
          const data = await this.redis.get(k);
          if (data) {
            const lines = data.split("\n");
            lines.shift();
            results.push(`[${key}] ${lines.join("\n").slice(0, 100)}`);
          }
        }
      }
    } else {
      for (const [k, v] of this.fallback) {
        if (!k.startsWith(prefix)) continue;
        if (k.endsWith(":_meta")) continue;
        if (Date.now() > v.expires) continue;
        const key = k.replace(prefix, "");
        if (pattern === "*" || key.includes(pattern)) {
          const lines = v.value.split("\n");
          lines.shift();
          results.push(`[${key}] ${lines.join("\n").slice(0, 100)}`);
        }
      }
    }
    return results;
  }

  /**
   * 删除指定 key
   */
  async delete(userId: string, sessionId: string, key: string): Promise<void> {
    const fullKey = this.buildKey(userId, sessionId, key);
    if (this.redis && this.connected) {
      await this.redis.del(fullKey, fullKey + ":_meta");
    } else {
      this.fallback.delete(fullKey);
      this.fallback.delete(fullKey + ":_meta");
    }
  }

  /**
   * 压缩会话上下文（防止超出 token 限制）
   * 保留最近 N 条，摘要早期记忆存入 L2
   */
  async compress(userId: string, sessionId: string, keepRecent = 10): Promise<string[]> {
    const prefix = `wm:${userId}:${sessionId}:`;
    const all: { key: string; value: string; at: number }[] = [];

    if (this.redis && this.connected) {
      const keys = await this.redis.keys(prefix + "*");
      for (const k of keys) {
        if (k.endsWith(":_meta")) continue;
        const data = await this.redis.get(k);
        if (!data) continue;
        const lines = data.split("\n");
        const meta = JSON.parse(lines[0]);
        all.push({ key: k.replace(prefix, ""), value: lines.slice(1).join("\n"), at: meta.accessedAt });
      }
    } else {
      for (const [k, v] of this.fallback) {
        if (!k.startsWith(prefix) || k.endsWith(":_meta")) continue;
        if (Date.now() > v.expires) continue;
        const lines = v.value.split("\n");
        const meta = JSON.parse(lines[0]);
        all.push({ key: k.replace(prefix, ""), value: lines.slice(1).join("\n"), at: meta.accessedAt });
      }
    }

    all.sort((a, b) => b.at - a.at);
    const toArchive = all.slice(keepRecent);
    const toKeep = all.slice(0, keepRecent);
    
    // 归档到 L2（由调用方处理）
    return toArchive.map(e => e.value);
  }

  /**
   * 列出当前会话所有 key
   */
  async listKeys(userId: string, sessionId: string): Promise<string[]> {
    const prefix = `wm:${userId}:${sessionId}:`;
    const results: string[] = [];

    if (this.redis && this.connected) {
      const keys = await this.redis.keys(prefix + "*");
      for (const k of keys) {
        if (!k.endsWith(":_meta")) {
          results.push(k.replace(prefix, ""));
        }
      }
    } else {
      for (const [k] of this.fallback) {
        if (k.startsWith(prefix) && !k.endsWith(":_meta")) {
          results.push(k.replace(prefix, ""));
        }
      }
    }
    return results;
  }

  private buildKey(userId: string, sessionId: string, key: string): string {
    return `wm:${userId}:${sessionId}:${key}`;
  }

  get isConnected(): boolean {
    return this.connected;
  }
}
