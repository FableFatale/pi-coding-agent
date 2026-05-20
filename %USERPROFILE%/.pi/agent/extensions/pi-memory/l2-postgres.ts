/**
 * L2: Episodic Memory (PostgreSQL)
 *
 * 特性:
 * - 历史会话片段存储
 * - FTS 全文搜索（pgvector 装好后升级为向量搜索）
 * - 自动去重链接
 */

import pg from "pg";
const { Pool } = pg;

export interface EpisodicEntry {
  id?: number;
  userId: string;
  sessionId: string;
  chunkType: string;
  content: string;
  summary?: string;
  tags?: string[];
  createdAt?: Date;
  accessedAt?: Date;
}

export interface SessionInfo {
  sessionId: string;
  lastAccessed: string;
  count: number;
}

export class L2EpisodicMemory {
  private pool: Pool | null = null;
  private connected = false;
  // 内存降级: sessionId → entries
  private fallback = new Map<string, EpisodicEntry[]>();
  private idCounter = 1;

  /**
   * 连接 PostgreSQL
   */
  async connect(): Promise<boolean> {
    try {
      this.pool = new Pool({
        host: "127.0.0.1",
        port: 5432,
        database: "postgres",
        user: process.env.PGUSER || "postgres",
        password: process.env.PGPASSWORD || "",
        max: 5,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 5000,
      });
      await this.pool.query("SELECT 1");
      this.connected = true;
      console.log("[L2] PostgreSQL connected");
      return true;
    } catch (e) {
      this.connected = false;
      this.pool = null;
      console.log("[L2] PostgreSQL not available, using in-memory fallback");
      return false;
    }
  }

  /**
   * 初始化表结构
   */
  async init(): Promise<void> {
    if (!this.connected || !this.pool) return;
    try {
      // 启用 pgvector 扩展
      await this.pool.query("CREATE EXTENSION IF NOT EXISTS vector");
      console.log("[L2] pgvector extension enabled");

      await this.pool.query(`
        CREATE TABLE IF NOT EXISTS episodic_memories (
          id SERIAL PRIMARY KEY,
          user_id VARCHAR(64) NOT NULL,
          session_id VARCHAR(64) NOT NULL,
          chunk_type VARCHAR(32) DEFAULT 'message',
          content TEXT NOT NULL,
          summary TEXT,
          embedding VECTOR(1536),
          tags TEXT[],
          created_at TIMESTAMP DEFAULT NOW(),
          accessed_at TIMESTAMP DEFAULT NOW(),
          is_archived BOOLEAN DEFAULT FALSE
        )
      `);

      // 为向量列创建 HNSW 索引
      await this.pool.query(`
        CREATE INDEX IF NOT EXISTS idx_episodic_embedding
          ON episodic_memories USING hnsw (embedding vector_cosine_ops)
          WITH (m = 16, ef_construction = 64)
      `).catch(() => {
        // HNSW 不支持时，使用普通向量索引
        return this.pool!.query(`
          CREATE INDEX IF NOT EXISTS idx_episodic_embedding_ivfflat
            ON episodic_memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
        `);
      });

      // 全文搜索索引
      await this.pool.query(`
        CREATE INDEX IF NOT EXISTS idx_episodic_fts
          ON episodic_memories USING gin (to_tsvector('english', content))
      `);

      await this.pool.query(`
        CREATE INDEX IF NOT EXISTS idx_episodic_user_session
          ON episodic_memories(user_id, session_id)
      `);
      await this.pool.query(`
        CREATE INDEX IF NOT EXISTS idx_episodic_created
          ON episodic_memories(created_at DESC)
      `);
      console.log("[L2] Schema initialized with vector support");
    } catch (e) {
      console.error("[L2] Init error:", e);
    }
  }

  /**
   * 存储单条记忆
   */
  async store(
    userId: string,
    sessionId: string,
    content: string,
    chunkType = "message",
    tags?: string[]
  ): Promise<number> {
    if (this.connected && this.pool) {
      const result = await this.pool.query(
        `INSERT INTO episodic_memories (user_id, session_id, chunk_type, content, tags)
         VALUES ($1, $2, $3, $4, $5) RETURNING id`,
        [userId, sessionId, chunkType, content, tags || null]
      );
      return result.rows[0].id;
    } else {
      const id = this.idCounter++;
      const entry: EpisodicEntry = { id, userId, sessionId, chunkType, content, tags };
      const key = `${userId}:${sessionId}`;
      const existing = this.fallback.get(key) || [];
      existing.push(entry);
      this.fallback.set(key, existing);
      return id;
    }
  }

  /**
   * 批量存储（用于 compress 结果）
   */
  async storeBatch(
    userId: string,
    sessionId: string,
    entries: Array<{ content: string; chunkType?: string; tags?: string[] }>
  ): Promise<number[]> {
    if (!entries.length) return [];

    if (this.connected && this.pool) {
      const client = await this.pool.connect();
      try {
        await client.query("BEGIN");
        const ids: number[] = [];
        for (const e of entries) {
          const result = await client.query(
            `INSERT INTO episodic_memories (user_id, session_id, chunk_type, content, tags)
             VALUES ($1, $2, $3, $4, $5) RETURNING id`,
            [userId, sessionId, e.chunkType || "message", e.content, e.tags || null]
          );
          ids.push(result.rows[0].id);
        }
        await client.query("COMMIT");
        return ids;
      } catch (e) {
        await client.query("ROLLBACK");
        throw e;
      } finally {
        client.release();
      }
    } else {
      const ids: number[] = [];
      const key = `${userId}:${sessionId}`;
      const existing = this.fallback.get(key) || [];
      for (const e of entries) {
        const id = this.idCounter++;
        existing.push({ id, userId, sessionId, chunkType: e.chunkType || "message", content: e.content, tags: e.tags });
        ids.push(id);
      }
      this.fallback.set(key, existing);
      return ids;
    }
  }

  /**
   * 混合搜索 - FTS + 向量相似度
   *
   * 策略：
   * 1. 尝试向量搜索（如果有 embedding）
   * 2. 同时进行 FTS 全文搜索
   * 3. 合并并去重结果，按综合分数排序
   *
   * @param query 搜索文本
   * @param embedding 可选的查询向量，提供时优先使用向量搜索
   * @param hybridWeight 混合权重 0-1，1=纯向量，0=纯FTS
   */
  async search(
    userId: string,
    query: string,
    limit = 10,
    embedding?: number[],
    hybridWeight = 0.7
  ): Promise<Array<{ id: number; content: string; chunkType: string; createdAt: string; score: number; source: "vector" | "fts" | "both" }>> {
    // 降级模式：回退到简单 LIKE 搜索
    if (!this.connected || !this.pool) {
      return this.searchFallback(userId, query, limit);
    }

    const results: Map<number, { id: number; content: string; chunkType: string; createdAt: string; score: number; vectorScore?: number; ftsScore?: number }> = new Map();

    // 1. 向量搜索（如果提供了 embedding）
    if (embedding && embedding.length === 1536) {
      const embeddingString = `[${embedding.join(",")}]`;
      const vectorResults = await this.pool.query(
        `SELECT id, content, chunk_type, created_at,
                embedding <=> $2::vector as distance
         FROM episodic_memories
         WHERE user_id = $1
           AND NOT is_archived
         ORDER BY embedding <=> $2::vector
         LIMIT $3`,
        [userId, embeddingString, limit * 2]  // 多取一些用于融合
      );

      for (const r of vectorResults.rows) {
        // distance 是 cosine distance (0-2)，转为 similarity (0-1)
        const distance = r.distance as number;
        const similarity = Math.max(0, 1 - distance / 2);  // 归一化到 0-1

        results.set(r.id, {
          id: r.id,
          content: r.content,
          chunkType: r.chunk_type,
          createdAt: r.created_at.toISOString(),
          score: similarity * hybridWeight,
          vectorScore: similarity,
        });
      }
    }

    // 2. FTS 全文搜索（使用 ts_rank）
    const ftsResults = await this.pool.query(
      `SELECT id, content, chunk_type, created_at,
              ts_rank(to_tsvector('english', content), plainto_tsquery($2)) as rank
       FROM episodic_memories
       WHERE user_id = $1
         AND to_tsvector('english', content) @@ plainto_tsquery($2)
         AND NOT is_archived
       ORDER BY rank DESC
       LIMIT $3`,
      [userId, query, limit * 2]
    );

    for (const r of ftsResults.rows) {
      const rank = r.rank as number;
      const normalizedRank = Math.min(1, rank / 10);  // 归一化到 0-1

      const existing = results.get(r.id);
      if (existing) {
        // 合并分数
        existing.ftsScore = normalizedRank;
        existing.score = (existing.score || 0) + (normalizedRank * (1 - hybridWeight));
      } else {
        results.set(r.id, {
          id: r.id,
          content: r.content,
          chunkType: r.chunk_type,
          createdAt: r.created_at.toISOString(),
          score: normalizedRank * (1 - hybridWeight),
          ftsScore: normalizedRank,
        });
      }
    }

    // 3. 当没有向量且FTS失败时，回退到 ILIKE
    if (results.size === 0) {
      const fallbackResults = await this.pool.query(
        `SELECT id, content, chunk_type, created_at, 0.5 as score
         FROM episodic_memories
         WHERE user_id = $1
           AND content ILIKE $2
           AND NOT is_archived
         ORDER BY accessed_at DESC
         LIMIT $3`,
        [userId, `%${query}%`, limit]
      );

      for (const r of fallbackResults.rows) {
        results.set(r.id, {
          id: r.id,
          content: r.content,
          chunkType: r.chunk_type,
          createdAt: r.created_at.toISOString(),
          score: r.score as number,
        });
      }
    }

    // 4. 按综合分数排序并返回
    return Array.from(results.values())
      .sort((a, b) => b.score - a.score)
      .slice(0, limit)
      .map(r => ({
        id: r.id,
        content: r.content,
        chunkType: r.chunkType,
        createdAt: r.createdAt,
        score: parseFloat(r.score.toFixed(4)),
        source: r.vectorScore && r.ftsScore ? "both" : (r.vectorScore ? "vector" : "fts"),
      }));
  }

  /**
   * 降级搜索（内存模式）
   */
  private async searchFallback(
    userId: string,
    query: string,
    limit = 10
  ): Promise<Array<{ id: number; content: string; chunkType: string; createdAt: string; score: number; source: "vector" | "fts" | "both" }>> {
    const results: Array<{ id: number; content: string; chunkType: string; createdAt: string; score: number; source: "vector" | "fts" | "both" }> = [];
    const q = query.toLowerCase();

    for (const [, entries] of this.fallback) {
      for (const e of entries) {
        if (e.userId === userId && e.content.toLowerCase().includes(q)) {
          results.push({
            id: e.id!,
            content: e.content,
            chunkType: e.chunkType,
            createdAt: (e.createdAt || new Date()).toISOString(),
            score: 0.5,
            source: "fts",
          });
          if (results.length >= limit) break;
        }
      }
    }

    return results.sort((a, b) => b.id - a.id);  // 按 ID 倒序
  }

  /**
   * 获取会话历史
   */
  async getSessionHistory(
    userId: string,
    sessionId: string,
    limit = 50
  ): Promise<Array<{ id: number; content: string; chunkType: string; createdAt: string }>> {
    if (this.connected && this.pool) {
      const result = await this.pool.query(
        `SELECT id, content, chunk_type, created_at
         FROM episodic_memories
         WHERE user_id = $1 AND session_id = $2 AND NOT is_archived
         ORDER BY created_at DESC
         LIMIT $3`,
        [userId, sessionId, limit]
      );
      return result.rows.map(r => ({
        id: r.id,
        content: r.content,
        chunkType: r.chunk_type,
        createdAt: r.created_at.toISOString(),
      }));
    } else {
      const key = `${userId}:${sessionId}`;
      const entries = this.fallback.get(key) || [];
      return entries.slice(-limit).map(e => ({
        id: e.id!,
        content: e.content,
        chunkType: e.chunkType,
        createdAt: (e.createdAt || new Date()).toISOString(),
      }));
    }
  }

  /**
   * 列出用户所有会话
   */
  async listSessions(userId: string): Promise<SessionInfo[]> {
    if (this.connected && this.pool) {
      const result = await this.pool.query(
        `SELECT session_id, MAX(accessed_at) as last_accessed, COUNT(*) as count
         FROM episodic_memories
         WHERE user_id = $1 AND NOT is_archived
         GROUP BY session_id
         ORDER BY last_accessed DESC`,
        [userId]
      );
      return result.rows.map(r => ({
        sessionId: r.session_id,
        lastAccessed: r.last_accessed.toISOString(),
        count: parseInt(r.count),
      }));
    } else {
      const sessions = new Map<string, { lastAccessed: Date; count: number }>();
      for (const [, entries] of this.fallback) {
        for (const e of entries) {
          if (e.userId !== userId) continue;
          const existing = sessions.get(e.sessionId);
          const accessed = e.accessedAt || e.createdAt || new Date();
          if (existing) {
            existing.count++;
            if (accessed > existing.lastAccessed) existing.lastAccessed = accessed;
          } else {
            sessions.set(e.sessionId, { lastAccessed: accessed, count: 1 });
          }
        }
      }
      return Array.from(sessions.entries())
        .map(([sessionId, info]) => ({
          sessionId,
          lastAccessed: info.lastAccessed.toISOString(),
          count: info.count,
        }))
        .sort((a, b) => b.lastAccessed.localeCompare(a.lastAccessed));
    }
  }

  /**
   * 更新访问时间
   */
  async touch(id: number): Promise<void> {
    if (this.connected && this.pool) {
      await this.pool.query(
        "UPDATE episodic_memories SET accessed_at = NOW() WHERE id = $1",
        [id]
      );
    } else {
      for (const [, entries] of this.fallback) {
        const e = entries.find(e => e.id === id);
        if (e) { e.accessedAt = new Date(); break; }
      }
    }
  }

  /**
   * 删除会话所有记忆
   */
  async deleteSession(userId: string, sessionId: string): Promise<number> {
    if (this.connected && this.pool) {
      const result = await this.pool.query(
        "DELETE FROM episodic_memories WHERE user_id = $1 AND session_id = $2",
        [userId, sessionId]
      );
      return result.rowCount || 0;
    } else {
      const key = `${userId}:${sessionId}`;
      const entries = this.fallback.get(key) || [];
      const count = entries.length;
      this.fallback.delete(key);
      return count;
    }
  }

  /**
   * 统计
   */
  async stats(userId: string): Promise<{ totalMemories: number; sessionsCount: number }> {
    if (this.connected && this.pool) {
      const result = await this.pool.query(
        "SELECT COUNT(*) as total, COUNT(DISTINCT session_id) as sessions FROM episodic_memories WHERE user_id = $1 AND NOT is_archived",
        [userId]
      );
      return {
        totalMemories: parseInt(result.rows[0].total),
        sessionsCount: parseInt(result.rows[0].sessions),
      };
    } else {
      let total = 0;
      const sessions = new Set<string>();
      for (const [, entries] of this.fallback) {
        for (const e of entries) {
          if (e.userId === userId) {
            total++;
            sessions.add(e.sessionId);
          }
        }
      }
      return { totalMemories: total, sessionsCount: sessions.size };
    }
  }

  // ============================================================
  // pgvector 向量搜索钩子（pgvector 编译好后启用）
  // ============================================================

  /**
   * 存储带向量嵌入的记忆（pgvector核心功能）
   */
  async storeWithEmbedding(
    userId: string,
    sessionId: string,
    content: string,
    embedding: number[],
    chunkType = "message",
    tags?: string[]
  ): Promise<number> {
    if (!this.connected || !this.pool) {
      // 降级到普通存储
      console.warn("[L2] storeWithEmbedding: pgvector not connected, falling back to store()");
      return this.store(userId, sessionId, content, chunkType, tags);
    }

    // 验证向量维度并转换为 pgvector 格式
    if (!embedding || embedding.length !== 1536) {
      throw new Error(`Invalid embedding dimension: expected 1536, got ${embedding?.length}`);
    }

    const embeddingString = `[${embedding.join(",")}]`;

    const result = await this.pool.query(
      `INSERT INTO episodic_memories (user_id, session_id, chunk_type, content, embedding, tags)
       VALUES ($1, $2, $3, $4, $5::vector, $6) RETURNING id`,
      [userId, sessionId, chunkType, content, embeddingString, tags || null]
    );

    return result.rows[0].id;
  }

  /**
   * 向量相似度搜索（pgvector核心功能）
   * 使用余弦相似度找到最接近的记忆
   */
  async searchByVector(
    userId: string,
    embedding: number[],
    limit = 10,
    minDistance = 0.7  // 最小相似度阈值（越小越相似）
  ): Promise<Array<{ id: number; content: string; chunkType: string; distance: number; createdAt?: string }>> {
    if (!this.connected || !this.pool) {
      console.warn("[L2] searchByVector: pgvector not connected, returning empty");
      return [];
    }

    // 验证向量维度
    if (!embedding || embedding.length !== 1536) {
      console.warn(`[L2] Invalid embedding dimension: expected 1536, got ${embedding?.length}`);
      return [];
    }

    const embeddingString = `[${embedding.join(",")}]`;

    // 使用 cosine distance (1 - cosine similarity)
    const result = await this.pool.query(
      `SELECT id, content, chunk_type, created_at,
              embedding <=> $2::vector as distance
       FROM episodic_memories
       WHERE user_id = $1
         AND NOT is_archived
       ORDER BY embedding <=> $2::vector
       LIMIT $3`,
      [userId, embeddingString, limit]
    );

    return result.rows
      .filter(r => r.distance <= (1 - minDistance))  // 过滤低相似度结果
      .map(r => ({
        id: r.id,
        content: r.content,
        chunkType: r.chunk_type,
        distance: parseFloat(r.distance.toFixed(4)),
        createdAt: r.created_at?.toISOString(),
      }));
  }

  get isConnected(): boolean {
    return this.connected;
  }
}
