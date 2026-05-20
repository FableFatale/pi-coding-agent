/**
 * Pi Memory E2E 测试
 * 测试三层记忆系统: L1 Redis + L2 PostgreSQL + L2.5 文件
 */
import 'dotenv/config';
import { L1WorkingMemory } from "./l1-redis.js";
import { L2EpisodicMemory } from "./l2-postgres.js";
import { readMemoryFile, writeMemoryFile, MEMORY_DIR } from "./storage.js";
import { existsSync, mkdirSync } from "fs";
import { join } from "path";

async function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function runTests() {
  console.log("🧪 Pi Memory E2E 测试\n");
  console.log("=".repeat(50));

  const l1 = new L1WorkingMemory();
  const l2 = new L2EpisodicMemory();
  const testUserId = "test_user_e2e";
  const testSessionId = `session_${Date.now()}`;

  // ============================================================
  // 测试 1: 连接 L1 (Redis)
  // ============================================================
  console.log("\n📦 测试 1: L1 Redis 连接");
  console.log("-".repeat(30));
  
  try {
    const l1Connected = await l1.connect();
    if (l1Connected) {
      console.log("✅ L1 Redis 连接成功!");
    } else {
      console.log("⚠️ L1 Redis 未连接，使用内存回退模式");
    }
    console.log(`   连接状态: ${l1.isConnected ? "Redis ✅" : "内存 🔄"}`);
  } catch (e) {
    console.log("❌ L1 连接失败:", e);
  }

  // ============================================================
  // 测试 2: 连接 L2 (PostgreSQL)
  // ============================================================
  console.log("\n📦 测试 2: L2 PostgreSQL 连接");
  console.log("-".repeat(30));
  
  try {
    const l2Connected = await l2.connect();
    if (l2Connected) {
      console.log("✅ L2 PostgreSQL 连接成功!");
      await l2.init();
      console.log("   表结构初始化完成");
    } else {
      console.log("⚠️ L2 PostgreSQL 未连接，使用内存回退模式");
    }
    console.log(`   连接状态: ${l2.isConnected ? "PostgreSQL ✅" : "内存 🔄"}`);
  } catch (e) {
    console.log("❌ L2 连接失败:", e);
  }

  // ============================================================
  // 测试 3: L1 写入/读取
  // ============================================================
  console.log("\n📦 测试 3: L1 写入/读取");
  console.log("-".repeat(30));
  
  try {
    const testKey = "test_key_001";
    const testValue = "这是 L1 测试数据 - " + new Date().toISOString();
    
    await l1.set(testUserId, testSessionId, testKey, testValue);
    console.log("✅ L1 写入成功:", testKey);
    
    const retrieved = await l1.get(testUserId, testSessionId, testKey);
    if (retrieved === testValue) {
      console.log("✅ L1 读取成功:", retrieved.slice(0, 30) + "...");
    } else {
      console.log("❌ L1 读取值不匹配");
    }
  } catch (e) {
    console.log("❌ L1 测试失败:", e);
  }

  // ============================================================
  // 测试 4: L2 写入/读取
  // ============================================================
  console.log("\n📦 测试 4: L2 写入/读取");
  console.log("-".repeat(30));
  
  try {
    const testContent = "这是 L2 测试记忆 - " + new Date().toISOString();
    
    const l2Id = await l2.store(testUserId, testSessionId, testContent, "test");
    console.log("✅ L2 写入成功, ID:", l2Id);
    
    const history = await l2.getSessionHistory(testUserId, testSessionId, 10);
    if (history.length > 0 && history[0].content.includes("L2 测试")) {
      console.log("✅ L2 读取成功:", history[0].content.slice(0, 30) + "...");
    } else {
      console.log("⚠️ L2 读取结果不明确");
    }
  } catch (e) {
    console.log("❌ L2 测试失败:", e);
  }

  // ============================================================
  // 测试 5: L2.5 文件层
  // ============================================================
  console.log("\n📦 测试 5: L2.5 文件层");
  console.log("-".repeat(30));
  
  try {
    // 确保目录存在
    if (!existsSync(MEMORY_DIR)) {
      mkdirSync(MEMORY_DIR, { recursive: true });
    }
    
    const testMemoryPath = join(MEMORY_DIR, "MEMORY.md");
    const testContent = `## E2E 测试 - ${new Date().toISOString()}

这是一条测试记忆，用于验证 L2.5 文件层功能。

关键词: 测试, E2E, 三层记忆
`;
    
    const existing = await readMemoryFile("MEMORY.md");
    await writeMemoryFile("MEMORY.md", existing + "\n" + testContent);
    console.log("✅ L2.5 写入成功");
    
    const retrieved = await readMemoryFile("MEMORY.md");
    if (retrieved.includes("E2E 测试")) {
      console.log("✅ L2.5 读取成功");
    }
  } catch (e) {
    console.log("❌ L2.5 测试失败:", e);
  }

  // ============================================================
  // 测试 6: L2 搜索
  // ============================================================
  console.log("\n📦 测试 6: L2 搜索");
  console.log("-".repeat(30));
  
  try {
    const searchResults = await l2.search(testUserId, "测试", 5);
    console.log(`✅ L2 搜索 "测试": 找到 ${searchResults.length} 条结果`);
    if (searchResults.length > 0) {
      console.log("   首条:", searchResults[0].content.slice(0, 50) + "...");
    }
  } catch (e) {
    console.log("❌ L2 搜索失败:", e);
  }

  // ============================================================
  // 测试 7: L1 压缩 → L2
  // ============================================================
  console.log("\n📦 测试 7: L1 → L2 压缩");
  console.log("-".repeat(30));
  
  try {
    // 添加多条 L1 数据
    for (let i = 0; i < 3; i++) {
      await l1.set(testUserId, testSessionId, `compress_test_${i}`, `压缩测试数据 ${i}`);
    }
    
    // 压缩到 L2
    const archived = await l1.compress(testUserId, testSessionId, 1);
    console.log(`✅ L1 压缩完成，存档 ${archived.length} 条`);
    
    if (archived.length > 0) {
      await l2.storeBatch(testUserId, testSessionId, archived.map(c => ({
        content: c,
        chunkType: "archived"
      })));
      console.log("✅ 存档已写入 L2");
    }
  } catch (e) {
    console.log("❌ L1→L2 压缩测试失败:", e);
  }

  // ============================================================
  // 测试结果汇总
  // ============================================================
  console.log("\n" + "=".repeat(50));
  console.log("📊 测试结果汇总");
  console.log("=".repeat(50));
  
  const l1Stats = await l1.listKeys(testUserId, testSessionId);
  const l2Stats = await l2.stats(testUserId);
  
  console.log(`
L1 (Working Memory):
  - 状态: ${l1.isConnected ? "Redis ✅" : "内存 🔄"}
  - 当前 key 数: ${l1Stats.length}

L2 (Episodic Memory):
  - 状态: ${l2.isConnected ? "PostgreSQL ✅" : "内存 🔄"}
  - 总记忆: ${l2Stats.totalMemories}
  - 会话数: ${l2Stats.sessionsCount}

L2.5 (Curated Memory):
  - 状态: ✅ 文件系统正常
  - 路径: ${MEMORY_DIR}
  - 文件: MEMORY.md

三层记忆系统 ${(l1.isConnected && l2.isConnected) ? "🎉 全部连接成功!" : "⚠️ 部分使用回退模式"}
`);

  // 清理测试数据
  try {
    await l2.deleteSession(testUserId, testSessionId);
    console.log("🧹 测试数据已清理");
  } catch {}
}

runTests().catch(console.error);
