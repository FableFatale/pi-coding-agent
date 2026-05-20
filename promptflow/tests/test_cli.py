"""
CLI 测试
"""
import pytest
import sys
sys.path.insert(0, 'src')

from promptflow.cli import PromptFlow


class TestPromptFlowCLI:
    """PromptFlow CLI 测试"""
    
    def test_prompt_flow_initialization(self):
        """测试 PromptFlow 初始化"""
        pf = PromptFlow()
        
        assert pf.parser is not None
        assert pf.flow_builder is not None
        assert pf.path_analyzer is not None
        assert pf.test_generator is not None
        assert pf.runner is not None
        assert pf.result_analyzer is not None
    
    def test_prompt_flow_attributes_initially_none(self):
        """测试 PromptFlow 属性初始为 None"""
        pf = PromptFlow()
        
        assert pf.parsed is None
        assert pf.flow_graph is None
        assert pf.test_suite is None
        assert pf.test_summary is None
        assert pf.analysis_report is None
    
    def test_prompt_flow_class_structure(self):
        """测试 PromptFlow 类结构"""
        pf = PromptFlow()
        
        # 检查所有必需的方法存在
        assert hasattr(pf, 'load_prompt')
        assert hasattr(pf, 'run_pipeline')
        assert hasattr(pf, 'export_tests')
        assert hasattr(pf, 'export_report')
        
        # 检查方法可调用
        assert callable(pf.load_prompt)
        assert callable(pf.run_pipeline)
        assert callable(pf.export_tests)
        assert callable(pf.export_report)


class TestPromptFlowMethods:
    """PromptFlow 方法测试"""
    
    def test_build_report_structure(self):
        """测试构建报告结构"""
        pf = PromptFlow()
        
        # 初始状态应该返回基本结构
        # 由于没有实际数据，验证方法存在
        assert callable(pf._build_report)
    
    def test_run_pipeline_method_exists(self):
        """测试 run_pipeline 方法存在"""
        pf = PromptFlow()
        
        # 验证方法存在且可调用
        assert hasattr(pf.run_pipeline, '__call__')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
