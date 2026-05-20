# 测试用例生成报告

## 概述

本项目包含完整的测试套件，覆盖 PromptFlow 框架的所有核心模块。

## 测试文件结构

```
tests/
├── __init__.py           # 测试包初始化
├── conftest.py           # Pytest 配置和共享 fixtures
├── test_parser.py        # PromptParser 测试
├── test_flow_builder.py  # FlowBuilder 测试
├── test_path_analyzer.py # PathAnalyzer 测试
├── test_test_generator.py # TestGenerator 测试
├── test_scenario_runner.py # ScenarioRunner 测试
├── test_result_analyzer.py # ResultAnalyzer 测试
├── test_tags.py          # TagEngine 测试
└── test_integration.py    # 集成测试
```

## 模块测试覆盖

### 1. PromptParser (parser.py)

| 测试类 | 测试方法 | 描述 |
|--------|----------|------|
| TestPromptParser | test_parser_initialization | 测试解析器初始化 |
| TestPromptParser | test_parse_basic_structure | 测试基本结构解析 |
| TestPromptParser | test_parse_nodes | 测试节点解析 |
| TestPromptParser | test_parse_ending_node | 测试结束节点识别 |
| TestPromptParser | test_parse_dialogue_examples | 测试对话示例提取 |
| TestPromptParser | test_parse_empty_prompt | 测试空 Prompt |
| TestPromptParser | test_parse_variables | 测试变量提取 |
| TestPromptParser | test_parse_node_headers | 测试节点标题解析 |
| TestPromptParser | test_parse_global_rules | 测试全局规则提取 |
| TestPromptParser | test_parse_libraries | 测试关键词库提取 |
| TestPromptParser | test_parse_multi_word_node_name | 测试多字节点名称 |
| TestPromptParserEdgeCases | test_parse_only_role | 测试只有角色的 Prompt |
| TestPromptParserEdgeCases | test_parse_no_role | 测试没有角色的 Prompt |
| TestPromptParserEdgeCases | test_parse_special_characters_in_node | 测试特殊字符 |

### 2. FlowBuilder (flow_builder.py)

| 测试类 | 测试方法 | 描述 |
|--------|----------|------|
| TestFlowBuilder | test_builder_initialization | 测试构建器初始化 |
| TestFlowBuilder | test_build_basic_flow | 测试基本流程构建 |
| TestFlowBuilder | test_build_with_explicit_edges | 测试显式边构建 |
| TestFlowBuilder | test_build_infers_implicit_edges | 测试隐式边推断 |
| TestFlowBuilder | test_identify_start_node | 测试起始节点识别 |
| TestFlowGraph | test_flow_graph_initialization | 测试流程图初始化 |
| TestFlowGraph | test_flow_graph_with_networkx | 测试 NetworkX 图构建 |
| TestFlowGraph | test_flow_graph_path_analysis | 测试路径分析 |
| TestEdgeTypes | test_normal_edge | 测试普通边 |
| TestEdgeTypes | test_conditional_edge | 测试条件边 |
| TestEdgeTypes | test_ending_edge | 测试结束边 |
| TestFlowBuilderEdgeCases | test_build_empty_nodes | 测试空节点 |
| TestFlowBuilderEdgeCases | test_build_single_node | 测试单节点 |
| TestFlowBuilderEdgeCases | test_build_circular_reference | 测试循环引用 |

### 3. PathAnalyzer (path_analyzer.py)

| 测试类 | 测试方法 | 描述 |
|--------|----------|------|
| TestPathAnalyzer | test_analyzer_initialization | 测试分析器初始化 |
| TestPathAnalyzer | test_analyze_simple_flow | 测试简单流程分析 |
| TestPathAnalyzer | test_collect_all_paths_simple | 测试收集简单路径 |
| TestPathAnalyzer | test_collect_all_paths_branch | 测试收集分支路径 |
| TestPathAnalyzer | test_identify_branch_points | 测试识别分支点 |
| TestPathAnalyzer | test_get_critical_paths | 测试获取关键路径 |
| TestPathAnalyzer | test_suggest_next_test | 测试建议下一个测试 |
| TestPathCoverage | test_coverage_calculation | 测试覆盖率计算 |
| TestPathCoverage | test_coverage_with_all_paths_tested | 测试全路径测试后覆盖率 |
| TestBranchPoint | test_branch_point_creation | 测试分支点创建 |
| TestBranchPoint | test_branch_count_property | 测试分支数量属性 |
| TestPath | test_path_creation | 测试路径创建 |
| TestPath | test_path_string_representation | 测试路径字符串表示 |
| TestPathAnalyzerEdgeCases | test_analyze_empty_flow | 测试空流程分析 |
| TestPathAnalyzerEdgeCases | test_analyze_single_node_flow | 测试单节点流程分析 |
| TestPathAnalyzerEdgeCases | test_analyze_long_chain | 测试长链分析 |

### 4. TestGenerator (test_generator.py)

| 测试类 | 测试方法 | 描述 |
|--------|----------|------|
| TestTestGenerator | test_generator_initialization | 测试生成器初始化 |
| TestTestGenerator | test_generate_returns_test_suite | 测试生成返回测试套件 |
| TestTestGenerator | test_generate_creates_test_cases | 测试生成创建测试用例 |
| TestTestGenerator | test_generate_includes_metadata | 测试生成包含元数据 |
| TestGeneratePathTests | test_generate_path_tests_exists | 测试路径测试生成方法存在 |
| TestGeneratePathTests | test_path_tests_have_normal_type | 测试路径测试用例类型 |
| TestGenerateEdgeTests | test_generate_edge_tests_exists | 测试边界测试生成方法存在 |
| TestGenerateEdgeTests | test_edge_tests_have_edge_type | 测试边界测试用例类型 |
| TestGenerateCriticalTests | test_generate_critical_tests_exists | 测试关键场景测试生成方法存在 |
| TestCreateTest | test_create_test_increments_id | 测试创建测试用例递增ID |
| TestCreateTest | test_create_test_with_user_inputs | 测试创建带用户输入的测试用例 |
| TestCreateTest | test_create_test_with_expected_ending | 测试创建带期望结束节点的测试用例 |
| TestTestCase | test_test_case_to_dict | 测试测试用例转换为字典 |
| TestTestSuite | test_test_suite_to_dict | 测试测试套件转换为字典 |
| TestTestInput | test_test_input_creation | 测试测试输入创建 |
| TestTestInput | test_test_input_default_type | 测试测试输入默认类型 |
| TestTestTypes | test_all_test_types_exist | 测试所有测试类型存在 |
| TestTestTypes | test_test_types_are_unique | 测试测试类型唯一性 |
| TestTestGeneratorEdgeCases | test_generate_with_empty_flow | 测试空流程图 |
| TestTestGeneratorEdgeCases | test_generate_with_single_node | 测试单节点流程 |

### 5. ScenarioRunner (scenario_runner.py)

| 测试类 | 测试方法 | 描述 |
|--------|----------|------|
| TestScenarioRunner | test_runner_initialization | 测试运行器初始化 |
| TestScenarioRunner | test_set_llm_client | 测试设置 LLM 客户端 |
| TestScenarioRunner | test_set_flow_handler | 测试设置流程处理器 |
| TestScenarioRunner | test_run_requires_handler_or_client | 测试运行需要处理器或客户端 |
| TestScenarioRunner | test_run_with_flow_handler | 测试使用流程处理器运行 |
| TestScenarioRunner | test_run_respects_max_turns | 测试运行遵守最大轮数限制 |
| TestRunSingleTest | test_run_single_test_creates_result | 测试运行单个测试创建结果 |
| TestRunSingleTest | test_run_single_test_with_error | 测试运行单个测试处理错误 |
| TestExecuteTurn | test_execute_turn_with_handler | 测试使用处理器执行单轮 |
| TestExecuteTurn | test_execute_turn_with_llm_client | 测试使用 LLM 客户端执行单轮 |
| TestExecuteTurn | test_execute_turn_handles_exception | 测试执行单轮处理异常 |
| TestTestRunResult | test_passed_property | 测试 passed 属性 |
| TestTestRunResult | test_to_dict | 测试转换为字典 |
| TestTestRunSummary | test_pass_rate_calculation | 测试通过率计算 |
| TestTestRunSummary | test_pass_rate_with_zero_tests | 测试零测试的通过率 |
| TestTestRunSummary | test_to_dict | 测试转换为字典 |
| TestTurnResult | test_turn_result_creation | 测试单轮结果创建 |
| TestTurnResult | test_turn_result_with_error | 测试带错误的单轮结果 |
| TestScenarioRunnerEdgeCases | test_run_empty_suite | 测试运行空测试套件 |
| TestScenarioRunnerEdgeCases | test_run_with_timeout | 测试超时设置 |
| TestScenarioRunnerEdgeCases | test_export_results_json | 测试导出 JSON 结果 |
| TestTestResults | test_all_result_types | 测试所有结果类型 |

### 6. ResultAnalyzer (result_analyzer.py)

| 测试类 | 测试方法 | 描述 |
|--------|----------|------|
| TestResultAnalyzer | test_analyzer_initialization | 测试分析器初始化 |
| TestResultAnalyzer | test_analyze_returns_report | 测试分析返回报告 |
| TestResultAnalyzer | test_analyze_generates_issues | 测试分析生成问题 |
| TestResultAnalyzer | test_analyze_generates_recommendations | 测试分析生成建议 |
| TestAnalyzeFailures | test_analyze_failures_detects_failures | 测试分析检测失败 |
| TestAnalyzeFailures | test_analyze_failures_high_severity | 测试分析失败高严重性 |
| TestAnalyzeErrors | test_analyze_errors_detects_errors | 测试分析检测错误 |
| TestAnalyzeErrors | test_analyze_errors_groups_same_errors | 测试分析分组相同错误 |
| TestGenerateRecommendations | test_recommendations_for_critical_issues | 测试关键问题建议 |
| TestGenerateRecommendations | test_recommendations_for_low_pass_rate | 测试低通过率建议 |
| TestGenerateRecommendations | test_recommendations_for_good_results | 测试良好结果建议 |
| TestAnalysisReport | test_report_to_dict | 测试报告转换为字典 |
| TestIssue | test_issue_creation | 测试问题创建 |
| TestIssue | test_issue_to_dict | 测试问题转换为字典 |
| TestResultAnalyzerEdgeCases | test_analyze_empty_summary | 测试分析空摘要 |
| TestResultAnalyzerEdgeCases | test_analyze_all_pass | 测试分析全通过 |

### 7. TagEngine (tags.py)

| 测试类 | 测试方法 | 描述 |
|--------|----------|------|
| TestLabelDefinition | test_label_definition_creation | 测试标签定义创建 |
| TestLabelDefinition | test_label_definition_defaults | 测试标签定义默认值 |
| TestTagResult | test_tag_result_creation | 测试标签结果创建 |
| TestTagResult | test_tag_result_to_dict | 测试标签结果转换为字典 |
| TestKeywordMatcher | test_keyword_matcher_basic | 测试关键词匹配器基本功能 |
| TestKeywordMatcher | test_keyword_matcher_case_insensitive | 测试关键词匹配器大小写不敏感 |
| TestKeywordMatcher | test_keyword_matcher_no_match | 测试关键词匹配器无匹配 |
| TestRegexMatcher | test_regex_matcher_basic | 测试正则匹配器基本功能 |
| TestRegexMatcher | test_regex_matcher_no_match | 测试正则匹配器无匹配 |
| TestCompositeMatcher | test_composite_matcher_any_mode | 测试组合匹配器任意模式 |
| TestCompositeMatcher | test_composite_matcher_all_mode | 测试组合匹配器全部模式 |
| TestCompositeMatcher | test_composite_matcher_all_mode_no_match | 测试组合匹配器全部模式无匹配 |
| TestConditionMatcher | test_condition_matcher_min_count | 测试条件匹配器最小计数 |
| TestConditionMatcher | test_condition_matcher_min_count_not_met | 测试条件匹配器计数不满足 |
| TestTagEngine | test_engine_initialization | 测试引擎初始化 |
| TestTagEngine | test_register_label | 测试注册标签 |
| TestTagEngine | test_register_personal_label | 测试注册个性标签 |
| TestTagEngine | test_register_labels_from_dict | 测试批量注册标签 |
| TestTagEngine | test_process_turn | 测试处理对话轮次 |
| TestTagEngine | test_process_turn_accumulate | 测试累积计数 |
| TestTagEngine | test_determine_intent_with_conditions | 测试条件判定意向 |
| TestTagEngine | test_determine_intent_default | 测试默认意向 |
| TestTagEngine | test_get_result | 测试获取结果 |
| TestTagEngine | test_reset | 测试重置 |
| TestTagParser | test_parse_from_markdown | 测试从 Markdown 解析 |
| TestTagParser | test_parse_intent_labels | 测试解析意向标签 |
| TestTagParser | test_parse_personal_labels | 测试解析个性标签 |
| TestCreateTagEngineFromPrompt | test_create_tag_engine_from_prompt | 测试从 Prompt 创建标签引擎 |
| TestTagEngineEdgeCases | test_engine_no_labels | 测试无标签引擎 |
| TestTagEngineEdgeCases | test_process_empty_input | 测试处理空输入 |
| TestTagEngineEdgeCases | test_regex_in_label | 测试正则表达式标签 |

### 8. 集成测试 (test_integration.py)

| 测试类 | 测试方法 | 描述 |
|--------|----------|------|
| TestEndToEndPipeline | test_complete_pipeline | 测试完整流程 |
| TestPromptFlowClass | test_prompt_flow_workflow | 测试 PromptFlow 工作流类 |
| TestComponentIntegration | test_parser_to_flow_builder | 测试解析器到流程构建器的集成 |
| TestComponentIntegration | test_flow_to_path_analyzer | 测试流程到路径分析器的集成 |
| TestComponentIntegration | test_analyzer_to_generator | 测试分析器到生成器的集成 |
| TestComponentIntegration | test_generator_to_runner | 测试生成器到运行器的集成 |
| TestComponentIntegration | test_runner_to_analyzer | 测试运行器到分析器的集成 |
| TestEdgeCasesIntegration | test_minimal_prompt | 测试最小 Prompt |
| TestEdgeCasesIntegration | test_complex_branching_flow | 测试复杂分支流程 |

## 运行测试

### 运行所有测试

```bash
cd promptflow
python run_tests.py
```

### 运行特定测试文件

```bash
pytest tests/test_parser.py -v
```

### 运行特定测试类

```bash
pytest tests/test_parser.py::TestPromptParser -v
```

### 生成覆盖率报告

```bash
pytest tests/ --cov=promptflow --cov-report=html
```

## 测试统计

- **总测试类**: 约 50 个
- **总测试方法**: 约 200+ 个
- **覆盖模块**: 7 个核心模块
- **集成测试**: 9 个端到端测试

## 测试质量指标

| 指标 | 目标 | 说明 |
|------|------|------|
| 代码覆盖率 | >80% | 核心模块高覆盖 |
| 边界测试 | ✓ | 包含空输入、单节点、循环等 |
| 错误处理 | ✓ | 测试异常情况 |
| 集成测试 | ✓ | 完整流程端到端测试 |
