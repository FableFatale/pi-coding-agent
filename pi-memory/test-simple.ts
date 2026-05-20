/**
 * Pi Memory E2E 测试 - 简化版（无 pgvector）
 */
import 'dotenv/config';
import { L1WorkingMemory } from "./l1-redis.js";
import { L2EpisodicMemory } from "./l2-postgres.js";
import { readMemoryFile, writeMemoryFile, MEMORY_DIR } from "./storage.js";
import { existsSync, mkdirSync } from "fs";
import { join } from "path";

async function runTests() {
  console.log("========================================");
  console.log("   Pi Memory E2E Test (Simple Mode)");
  console.log("========================================\n");

  const l1 = new L1WorkingMemory();
  const l2 = new L2EpisodicMemory();
  const testUserId = "test_e2e";
  const testSessionId = `session_${Date.now()}`;

  // 1. Connect L1
  console.log("[1] L1 (Redis)...");
  const l1Ok = await l1.connect();
  console.log(`    Status: ${l1.isConnected ? "Redis OK" : "Memory fallback"}`);

  // 2. Connect L2
  console.log("\n[2] L2 (PostgreSQL)...");
  const l2Ok = await l2.connect();
  if (l2Ok) {
    console.log("    PostgreSQL connected, initializing table...");
    await l2.init();
    console.log(`    Status: PostgreSQL OK`);
  } else {
    console.log(`    Status: Memory fallback`);
  }

  // 3. Test L1 write/read
  console.log("\n[3] L1 Write/Read...");
  await l1.set(testUserId, testSessionId, "test_key", "Hello from L1!");
  const val = await l1.get(testUserId, testSessionId, "test_key");
  console.log(`    Write/Read: ${val ? "OK" : "FAILED"}`);

  // 4. Test L2 write/read
  console.log("\n[4] L2 Write/Read...");
  const id = await l2.store(testUserId, testSessionId, "Hello from L2!", "test");
  console.log(`    Store ID: ${id}`);
  const history = await l2.getSessionHistory(testUserId, testSessionId, 5);
  console.log(`    Read: ${history.length > 0 ? "OK" : "FAILED"}`);

  // 5. Test L2.5 (File)
  console.log("\n[5] L2.5 (File)...");
  if (!existsSync(MEMORY_DIR)) mkdirSync(MEMORY_DIR, { recursive: true });
  await writeMemoryFile("MEMORY.md", "# Test\n\nHello from L2.5!");
  const content = await readMemoryFile("MEMORY.md");
  console.log(`    Write/Read: ${content.includes("L2.5") ? "OK" : "FAILED"}`);

  // Summary
  console.log("\n========================================");
  console.log("   SUMMARY");
  console.log("========================================");
  console.log(`
L1: ${l1.isConnected ? "Redis" : "Memory"} 
L2: ${l2.isConnected ? "PostgreSQL" : "Memory"}
L2.5: File System OK

All tests completed!
`);

  // Cleanup
  try { await l2.deleteSession(testUserId, testSessionId); } catch {}
}

runTests().catch(console.error);
