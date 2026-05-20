#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MemoryManager 使用示例 - 完整记忆流向演示
"""

import sys


def main():
    print("=" * 60)
    print("  MemoryManager - 完整记忆流向演示")
    print("=" * 60)

    # 交互式输入密码
    password = input("\n请输入 PostgreSQL 密码 (直接回车用postgres): ").strip()
    if not password:
        password = "postgres"

    try:
        from pi_memory import MemoryManager, MemorySystem
    except ImportError:
        print("❌ 请先安装: pip install -e .")
        return 1

    # 初始化
    memory = MemorySystem(
        pg_password=password,
        pinecone_api_key=""
    )
    manager = MemoryManager(memory)

    # ============================================================
    # 步骤1: 模拟对话并存储
    # ============================================================
    print("\n[步骤1] 模拟对话存储")
    print("-" * 40)

    session_id = "demo:001"
    
    # 创建会话
    memory.session_create(session_id)
    print(f"✅ 创建会话: {session_id}")

    # 添加对话
    dialogs = [
        ("user", "我想学习Python编程"),
        ("assistant", "好的，Python是一门易学易用的编程语言。你想了解哪方面？"),
        ("user", "我想做一个Web应用"),
        ("assistant", "可以用Flask或Django框架来开发Web应用。"),
        ("user", "帮我写一个简单的API"),
        ("assistant", "我来帮你写一个Flask API示例..."),
    ]

    for role, content in dialogs:
        memory.session_add_message(session_id, role, content)
    
    print(f"✅ 添加 {len(dialogs)} 条对话")

    # 保存到历史
    memory.save_session(
        session_id,
        [{"role": r, "content": c} for r, c in dialogs],
        title="Python Web开发学习",
        tags=["Python", "Web", "Flask"]
    )
    print("✅ 保存到历史会话")

    # ============================================================
    # 步骤2: 预取相关记忆 (并行查询)
    # ============================================================
    print("\n[步骤2] 预取相关记忆 (并行查询)")
    print("-" * 40)

    query = "Python Web开发"
    context = manager.prefetch_all(query, session_id)
    
    print(f"\n📋 MemoryContext:")
    print(f"   当前会话: {context.current_session}")
    print(f"   相关会话: {len(context.relevant_sessions)} 个")
    print(f"   共享记忆: {len(context.curated_memory)} 条")
    print(f"   用户信息: {len(context.user_info)} 项")
    print(f"   相关技能: {len(context.relevant_skills)} 个")

    # ============================================================
    # 步骤3: 生成 System Prompt
    # ============================================================
    print("\n[步骤3] 生成 System Prompt")
    print("-" * 40)

    base_prompt = """你是一个有帮助的AI助手。"""

    system_prompt = manager.build_system_prompt(
        base_prompt,
        query="Python Web开发",
        session_id=session_id
    )

    print("📝 完整的 System Prompt:")
    print("-" * 40)
    print(system_prompt)
    print("-" * 40)

    # ============================================================
    # 步骤4-5: 模拟 LLM 调用
    # ============================================================
    print("\n[步骤4-5] 模拟 LLM 调用")
    print("-" * 40)
    print("🤖 LLM 处理中...")
    print("   - 已注入记忆上下文")
    print("   - 上下文长度:", len(system_prompt), "字符")

    # ============================================================
    # 步骤6: 同步到各Provider
    # ============================================================
    print("\n[步骤6] 同步到各Provider")
    print("-" * 40)

    # 添加一些共享记忆
    memory.memory_add(
        "用户对Python Web开发感兴趣",
        author="agent",
        tags=["用户偏好", "Python"]
    )

    # 执行同步
    sync_result = manager.sync_all(
        session_id,
        tags=["Python", "Web"]
    )

    print(f"✅ 同步结果:")
    print(f"   L1 (Working): {'✅' if sync_result.l1_synced else '❌'}")
    print(f"   L2 (Episodic): {'✅' if sync_result.l2_synced else '❌'}")
    print(f"   L2.5 (Curated): {'✅' if sync_result.l2_5_synced else '❌'}")
    print(f"   L3 (Semantic): {'✅' if sync_result.l3_synced else '❌'}")
    
    if sync_result.errors:
        print(f"   错误: {sync_result.errors}")

    # ============================================================
    # 完整流程演示
    # ============================================================
    print("\n" + "=" * 60)
    print("  完整记忆流向")
    print("=" * 60)

    flow = """
    ┌─────────────────────────────────────────────────────────┐
    │ 1. 用户对话                                            │
    │    → memory.session_add_message()                      │
    │    → 存储到 L1 (Redis)                                │
    └─────────────────────────────────────────────────────────┘
                            ↓
    ┌─────────────────────────────────────────────────────────┐
    │ 2. 预取记忆 (并行查询)                                 │
    │    → manager.prefetch_all(query)                      │
    │    → L1: 当前会话                                     │
    │    → L2: 相关历史会话 (并行)                          │
    │    → L2.5: 共享记忆 (并行)                            │
    │    → L3: 相关技能 (并行)                              │
    └─────────────────────────────────────────────────────────┘
                            ↓
    ┌─────────────────────────────────────────────────────────┐
    │ 3. 组装 Memory Context                                 │
    │    → manager.build_system_prompt()                    │
    │    → 注入 System Prompt                                │
    └─────────────────────────────────────────────────────────┘
                            ↓
    ┌─────────────────────────────────────────────────────────┐
    │ 4. LLM API Call                                       │
    │    → AI 处理请求                                       │
    └─────────────────────────────────────────────────────────┘
                            ↓
    ┌─────────────────────────────────────────────────────────┐
    │ 5. Tool Execution                                     │
    │    → 执行工具调用                                      │
    └─────────────────────────────────────────────────────────┘
                            ↓
    ┌─────────────────────────────────────────────────────────┐
    │ 6. 同步记忆                                           │
    │    → manager.sync_all()                               │
    │    → L1 → L2 (归档)                                   │
    │    → L2.5 (提取偏好)                                  │
    │    → L3 (提取技能)                                    │
    └─────────────────────────────────────────────────────────┘
    """
    print(flow)

    # ============================================================
    # 统计
    # ============================================================
    print("\n[统计]")
    print("-" * 40)
    stats = manager.get_stats()
    print(f"   L1 会话: {stats['l1']['info'].get('sessions', 'N/A')}")
    print(f"   L2 会话数: {stats['l2']['count']}")
    print(f"   L2.5 记忆: {stats['l2_5']['stats'].get('total_entries', 0)}")
    print(f"   L3 技能数: {stats['l3']['stats'].get('total', 0)}")

    print("\n" + "=" * 60)
    print("  ✅ 演示完成！")
    print("=" * 60)

    memory.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
