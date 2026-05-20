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
        assert key == "test:mykey"


class TestL2EpisodicMemory:
    """L2情景记忆测试"""

    def test_l2_init(self):
        """测试L2初始化"""
        from pi_memory.l2_episodic import L2EpisodicMemory
        
        memory = L2EpisodicMemory(
            host="localhost",
            database="test",
            user="postgres",
            password=""
        )
        assert memory.vector_dim == 768


class TestL3SemanticMemory:
    """L3语义记忆测试"""

    def test_l3_init(self):
        """测试L3初始化"""
        from pi_memory.l3_semantic import L3SemanticMemory
        
        # Mock mode (no actual Pinecone connection)
        memory = L3SemanticMemory(api_key="")
        assert memory.connected == False


class TestMemorySystem:
    """记忆系统集成测试"""

    def test_system_init(self):
        """测试系统初始化"""
        from pi_memory import MemorySystem
        
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

    def test_session_methods(self):
        """测试会话方法"""
        from pi_memory import MemorySystem
        
        memory = MemorySystem(pinecone_api_key="")
        
        # These would need actual Redis to work
        # Just test the methods exist
        assert hasattr(memory, 'session_set')
        assert hasattr(memory, 'session_get')
        assert hasattr(memory, 'session_delete')

    def test_remember_recall(self):
        """测试记忆和回忆"""
        from pi_memory import MemorySystem
        
        memory = MemorySystem(pinecone_api_key="")
        
        assert hasattr(memory, 'remember')
        assert hasattr(memory, 'recall')
        assert hasattr(memory, 'learn_skill')
        assert hasattr(memory, 'find_skills')


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
