#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pi Memory - 使用示例
"""

import sys


def main():
    print("=" * 50)
    print("  Pi Memory - 升级版三层记忆系统")
    print("=" * 50)

    # 交互式输入密码
    password = input("\n请输入 PostgreSQL 密码 (直接回车用postgres): ").strip()
    if not password:
        password = "postgres"

    try:
        from pi_memory import MemorySystem
    except ImportError:
        print("❌ 请先安装: pip install -e .")
        return 1

    # 初始化记忆系统
    memory = MemorySystem(
        # L1 Redis
        redis_host="localhost",
        redis_port=6379,
        
        # L2 PostgreSQL
        pg_host="localhost",
        pg_port=5432,
        pg_database="pimemory",
        pg_user="postgres",
        pg_password=password
    )

    # ============================================================
    # L1: 工作记忆 (Redis)
    # ============================================================
    print("\n[L1] Working Memory (Redis)")
    print("-" * 40)

    # 检查连接
    if not memory.l1.ping():
        print("⚠️  Redis 未连接")
    else:
        print("✅ Redis 已连接")
        
        # 创建会话
        memory.session_create("user:123", {"user": "张三"})
        print("✅ 创建会话: user:123")
        
        # 添加消息
        memory.session_add_message("user:123", "user", "你好，我想学习Python")
        memory.session_add_message("user:123", "assistant", "好的，Python是一门很好的编程语言")
        memory.session_add_message("user:123", "user", "有什么推荐的学习方法吗？")
        print("✅ 添加消息: 3条")
        
        # 获取消息
        messages = memory.session_get_messages("user:123")
        print(f"✅ 获取消息: {len(messages)}条")
        for msg in messages[-2:]:
            print(f"   [{msg.role}] {msg.content[:30]}...")
        
        # 获取会话信息
        info = memory.l1.get_session_info("user:123")
        print(f"   会话信息: {info}")

    # ============================================================
    # L2: 情景记忆 (PostgreSQL)
    # ============================================================
    print("\n[L2] Episodic Memory (PostgreSQL)")
    print("-" * 40)

    if not memory.l2.ping():
        print("⚠️  PostgreSQL 未连接")
    else:
        print("✅ PostgreSQL 已连接")
        
        # 保存会话到历史
        session_id = memory.save_session(
            "user:123",
            [
                {"role": "user", "content": "你好，我想学习Python"},
                {"role": "assistant", "content": "好的，Python是一门很好的编程语言"},
                {"role": "user", "content": "有什么推荐的学习方法吗？"}
            ],
            title="Python学习咨询",
            tags=["学习", "Python"],
            auto_summarize=True
        )
        print(f"✅ 保存会话: id={session_id}")
        
        # 搜索会话
        results = memory.search_sessions("Python")
        print(f"✅ 搜索会话 'Python': 找到 {len(results)} 条")
        for session, score in results:
            print(f"   - {session.title} (得分: {score:.2f})")
            print(f"     摘要: {session.summary[:50]}...")

    # ============================================================
    # L2.5: 策划记忆 (文件)
    # ============================================================
    print("\n[L2.5] Curated Memory (文件)")
    print("-" * 40)

    print(f"✅ 记忆目录: {memory.l2_5.get_path()}")
    
    # 添加共享记忆
    memory.memory_add(
        "用户张三对Python编程感兴趣",
        author="agent",
        tags=["用户偏好", "Python"]
    )
    print("✅ 添加共享记忆")
    
    # 添加用户信息
    memory.memory_add_user("name", "张三")
    memory.memory_add_user("interest", "Python编程")
    print("✅ 更新用户信息")
    
    # 读取记忆
    memory_content = memory.memory_read()
    print(f"   共享记忆长度: {len(memory_content)} 字符")
    
    # 搜索记忆
    entries = memory.memory_search("Python")
    print(f"✅ 搜索记忆 'Python': 找到 {len(entries)} 条")

    # ============================================================
    # L3: 语义记忆 (技能)
    # ============================================================
    print("\n[L3] Semantic Memory (skills)")
    print("-" * 40)

    print(f"✅ Skills目录: {memory.l3.get_path()}")
    
    # 添加技能
    memory.skill_add(
        "python-basics",
        name="Python基础",
        content="""# Python基础

## 变量
```python
x = 10
name = "张三"
```

## 条件
```python
if x > 5:
    print("大于5")
```

## 循环
```python
for i in range(10):
    print(i)
```
""",
        description="Python编程语言基础知识",
        category="编程",
        level="beginner",
        tags=["Python", "编程", "入门"]
    )
    print("✅ 添加技能: Python基础")
    
    # 添加另一个技能
    memory.skill_add(
        "web-development",
        name="Web开发",
        content="""# Web开发

## 前端
- HTML/CSS/JavaScript
- React/Vue

## 后端
- Python Flask/Django
- Node.js Express
""",
        description="Web全栈开发知识",
        category="编程",
        level="intermediate",
        tags=["Web", "全栈"]
    )
    print("✅ 添加技能: Web开发")
    
    # 搜索技能
    skills = memory.skill_search("Python")
    print(f"✅ 搜索技能 'Python': 找到 {len(skills)} 个")
    for skill in skills:
        print(f"   - {skill.name} [{skill.level}]")
    
    # 检测冲突
    result = memory.skill_detect_conflict("Python Web开发框架 Django", "Python Django")
    if result.has_conflicts:
        print(f"⚠️  检测到 {len(result.conflicts)} 个冲突")
        for c in result.conflicts:
            print(f"   - {c.skill_a} vs {c.skill_b}: {c.type}")
    else:
        print("✅ 无冲突")
    
    # 列出所有分类
    categories = memory.l3.get_categories()
    print(f"✅ 技能分类: {categories}")

    # ============================================================
    # 预取相关记忆
    # ============================================================
    print("\n[Prefetch] 预取相关记忆")
    print("-" * 40)

    context = memory.prefetch("Python编程学习")
    print(f"✅ 预取结果:")
    print(f"   相关会话: {len(context['relevant_sessions'])} 个")
    print(f"   共享记忆: {len(context['curated_memory'])} 条")
    print(f"   相关技能: {len(context['relevant_skills'])} 个")

    # ============================================================
    # 健康检查
    # ============================================================
    print("\n[Health Check]")
    print("-" * 40)
    
    health = memory.health_check()
    print(f"L1 (Redis): {health['l1']['status']}")
    print(f"L2 (PostgreSQL): {health['l2']['status']}, 会话数={health['l2']['count']}")
    print(f"L2.5 (文件): {health['l2_5']['status']}")
    print(f"L3 (Skills): {health['l3']['status']}, 技能数={health['l3']['stats']['total']}")
    print(f"Pinecone: {'已启用' if health['l3']['pinecone'] else '未启用(本地模式)'}")

    print("\n" + "=" * 50)
    print("  ✅ 示例完成！")
    print("=" * 50)

    memory.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
