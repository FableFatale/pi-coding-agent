# -*- coding: utf-8 -*-
"""
Pi Memory 测试
"""

import pytest


class TestL1WorkingMemory:
    """L1工作记忆测试"""

    def test_l1_init(self):
        """测试L1初始化"""
        from pi_memory.l1_working import L1WorkingMemory
        
        # Mock Redis for testing without actual Redis
        memory = L1WorkingMemory(host="localhost", port=6379)
        assert memory.redis is not None

    def test_key_prefix(self):
        """测试键前缀"""
        from pi_memory.l1_working import L1WorkingMemory
        
        memory = L1WorkingMemory(key_prefix="test:")
        assert memory.key_prefix == "test:"
        
        key = memory._make_key("mykey")
        assert key == "test:mykey:messages"


class TestL2EpisodicMemory:
    """L2情景记忆测试"""

    def test_l2_init(self):
        """测试L2初始化"""
        from pi_memory.l2_episodic import L2EpisodicMemory
        
        memory = L2EpisodicMemory(
            host="localhost",
            database="test",
            user="postgres",
            password="",
            auto_init=False
        )
        assert memory.vector_dim == 1536
        assert memory.vector_enabled is False

    def test_l2_vector_literal(self):
        """测试 pgvector 字面量格式化"""
        from pi_memory.l2_episodic import L2EpisodicMemory

        memory = L2EpisodicMemory(auto_init=False)

        assert memory._format_vector([0.1, 0.2, 0.3]) == "[0.1,0.2,0.3]"


class TestL3SemanticMemory:
    """L3语义记忆测试"""

    def test_l3_init(self):
        """测试L3初始化"""
        from pi_memory.l3_semantic import L3SemanticMemory
        
        # Mock mode (no actual Pinecone connection)
        memory = L3SemanticMemory(pinecone_api_key="")
        assert memory.is_pinecone_enabled() is False


class TestMemorySystem:
    """记忆系统集成测试"""

    def test_system_init(self, monkeypatch):
        """测试系统初始化"""
        from pi_memory.l2_episodic import L2EpisodicMemory
        from pi_memory import MemorySystem

        monkeypatch.setattr(L2EpisodicMemory, "_init_db", lambda self: None)
        
        # With minimal config (mock mode)
        memory = MemorySystem(
            redis_host="localhost",
            pg_host="localhost",
            pg_password="",
            pinecone_api_key=""
        )
        
        assert memory.l1 is not None
        assert memory.l2 is not None
        assert memory.l3 is not None

    def test_session_methods(self, monkeypatch):
        """测试会话方法"""
        from pi_memory.l2_episodic import L2EpisodicMemory
        from pi_memory import MemorySystem

        monkeypatch.setattr(L2EpisodicMemory, "_init_db", lambda self: None)
        
        memory = MemorySystem(pinecone_api_key="")
        
        # These would need actual Redis to work
        # Just test the methods exist
        assert hasattr(memory, 'session_create')
        assert hasattr(memory, 'session_get_messages')
        assert hasattr(memory, 'session_delete')

    def test_remember_recall(self, monkeypatch):
        """测试记忆和回忆"""
        from pi_memory.l2_episodic import L2EpisodicMemory
        from pi_memory import MemorySystem

        monkeypatch.setattr(L2EpisodicMemory, "_init_db", lambda self: None)
        
        memory = MemorySystem(pinecone_api_key="")
        
        assert hasattr(memory, 'memory_add')
        assert hasattr(memory, 'memory_search')
        assert hasattr(memory, 'skill_add')
        assert hasattr(memory, 'skill_search')


class TestSkill:
    """技能测试"""

    def test_skill_creation(self):
        """测试技能创建"""
        from pi_memory.l3_semantic import Skill
        
        skill = Skill(
            id="test:1",
            name="Python",
            description="编程语言",
            level="expert"
        )
        
        assert skill.name == "Python"
        assert skill.level == "expert"


class TestConflict:
    """冲突检测测试"""

    def test_conflict_creation(self):
        """测试冲突创建"""
        from pi_memory.l3_semantic import Conflict
        
        conflict = Conflict(
            skill_a="Python",
            skill_b="Java",
            type="similar",
            similarity=0.75
        )
        
        assert conflict.skill_a == "Python"
        assert conflict.similarity == 0.75


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
