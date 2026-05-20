# -*- coding: utf-8 -*-
"""
Agent Extension for pi-code-runner

智能体扩展，提供:
- 任务规划
- 工具调用
- 记忆集成
- 反思机制
"""

import json
import logging
import re
from typing import Any, Optional, List, Dict, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent 状态"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_TOOL = "waiting_tool"
    REFLECTING = "reflecting"
    DONE = "done"
    ERROR = "error"


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, str] = field(default_factory=dict)  # param_name -> type
    handler: Optional[Callable] = None
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


@dataclass
class ToolCall:
    """工具调用"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Any = None
    error: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "tool": self.tool_name,
            "args": self.arguments,
            "result": str(self.result)[:500] if self.result else None,
            "error": self.error
        }


@dataclass
class Step:
    """执行步骤"""
    step_number: int
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict] = None
    observation: str = ""
    is_error: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "step": self.step_number,
            "thought": self.thought,
            "action": self.action,
            "input": self.action_input,
            "observation": self.observation[:500] if self.observation else "",
            "error": self.is_error
        }


@dataclass
class AgentResponse:
    """Agent 响应"""
    final_answer: str
    steps: List[Step]
    tool_calls: List[ToolCall]
    memory_context: str = ""
    state: AgentState = AgentState.DONE
    error: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "answer": self.final_answer,
            "steps": [s.to_dict() for s in self.steps],
            "tool_calls": [t.to_dict() for t in self.tool_calls],
            "memory_used": bool(self.memory_context),
            "state": self.state.value,
            "error": self.error
        }


class AgentExtension:
    """
    Agent 扩展
    
    功能:
    - 任务规划 (ReAct)
    - 工具调用
    - 记忆集成
    - 反思机制
    - 多轮对话
    """
    
    name = "agent"
    version = "1.0.0"
    
    def __init__(
        self,
        llm_provider: Optional[Callable] = None,
        memory_manager=None,
        max_steps: int = 10,
        max_retries: int = 2
    ):
        """
        Args:
            llm_provider: LLM 提供函数 (prompt) -> str
            memory_manager: MemoryManagerExtension 实例
            max_steps: 最大步数
            max_retries: 最大重试次数
        """
        self.llm_provider = llm_provider
        self.memory = memory_manager
        self.max_steps = max_steps
        self.max_retries = max_retries
        
        self.tools: Dict[str, Tool] = {}
        self.conversation_history: List[Dict] = []
        self.current_state = AgentState.IDLE
        
        # 注册默认工具
        self._register_default_tools()
        
        logger.info(f"AgentExtension initialized with {len(self.tools)} tools")
    
    def _register_default_tools(self):
        """注册默认工具"""
        # 搜索记忆
        self.register_tool(Tool(
            name="search_memory",
            description="搜索相关记忆和历史会话",
            parameters={"query": "string"},
            handler=self._tool_search_memory
        ))
        
        # 获取用户信息
        self.register_tool(Tool(
            name="get_user_info",
            description="获取用户信息",
            parameters={},
            handler=self._tool_get_user_info
        ))
        
        # 搜索技能
        self.register_tool(Tool(
            name="search_skill",
            description="搜索相关技能文档",
            parameters={"query": "string"},
            handler=self._tool_search_skill
        ))
        
        # 保存记忆
        self.register_tool(Tool(
            name="save_memory",
            description="保存重要信息到记忆",
            parameters={"content": "string", "author": "string"},
            handler=self._tool_save_memory
        ))
    
    def register_tool(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def unregister_tool(self, name: str):
        """注销工具"""
        if name in self.tools:
            del self.tools[name]
    
    # ============================================================
    # 工具实现
    # ============================================================
    
    def _tool_search_memory(self, query: str) -> str:
        """搜索记忆工具"""
        if not self.memory:
            return "记忆管理器未初始化"
        
        sessions = self.memory.search_sessions(query, limit=3)
        if not sessions:
            return "未找到相关历史会话"
        
        results = []
        for s in sessions:
            results.append(f"- {s['title']}: {s.get('summary', '')[:100]}")
        
        return "\n".join(results)
    
    def _tool_get_user_info(self) -> str:
        """获取用户信息工具"""
        if not self.memory:
            return "记忆管理器未初始化"
        
        info = self.memory.user_info_get()
        if not info:
            return "未找到用户信息"
        
        return "\n".join([f"- {k}: {v}" for k, v in info.items()])
    
    def _tool_search_skill(self, query: str) -> str:
        """搜索技能工具"""
        if not self.memory:
            return "记忆管理器未初始化"
        
        skills = self.memory.skill_search(query, limit=3)
        if not skills:
            return "未找到相关技能"
        
        results = []
        for s in skills:
            results.append(f"- {s['name']}: {s.get('description', '')}")
        
        return "\n".join(results)
    
    def _tool_save_memory(self, content: str, author: str = "agent") -> str:
        """保存记忆工具"""
        if not self.memory:
            return "记忆管理器未初始化"
        
        success = self.memory.memory_add(content, author)
        return "记忆已保存" if success else "保存失败"
    
    # ============================================================
    # LLM 调用
    # ============================================================
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        if self.llm_provider:
            return self.llm_provider(prompt)
        
        # 默认实现
        return "请配置 LLM provider"
    
    def _build_system_prompt(self) -> str:
        """构建 System Prompt"""
        tools_desc = []
        for tool in self.tools.values():
            params = ", ".join([f"{k}: {v}" for k, v in tool.parameters.items()])
            tools_desc.append(f"- {tool.name}({params}): {tool.description}")
        
        tools_str = "\n".join(tools_desc) if tools_desc else "无"
        
        return f"""你是一个智能助手，可以调用工具来完成任务。

## 可用工具
{tools_str}

## 规则
1. 每次只调用一个工具
2. 思考清楚后再行动
3. 观察工具返回结果
4. 如果完成回答，说"最终答案: ..."

## 格式
Thought: 思考
Action: 工具名
Action Input: {{"参数": "值"}}
"""
    
    def _build_memory_context(self, query: str) -> str:
        """构建记忆上下文"""
        if not self.memory:
            return ""
        
        context = self.memory.build_context(query)
        return f"\n\n## 相关记忆\n{context}\n" if context else ""
    
    # ============================================================
    # 执行
    # ============================================================
    
    def run(
        self,
        query: str,
        session_id: Optional[str] = None,
        context: Optional[str] = None
    ) -> AgentResponse:
        """
        运行 Agent
        
        Args:
            query: 用户问题
            session_id: 会话ID
            context: 额外上下文
            
        Returns:
            AgentResponse
        """
        self.current_state = AgentState.PLANNING
        self.conversation_history = []
        
        steps = []
        tool_calls = []
        
        system_prompt = self._build_system_prompt()
        memory_context = self._build_memory_context(query) if session_id else ""
        
        # 第一轮 Prompt
        prompt = f"""{system_prompt}
{memory_context}
{context or ""}

## 当前问题
{query}

开始执行:
"""
        
        retries = 0
        step_num = 0
        
        while step_num < self.max_steps:
            step_num += 1
            self.current_state = AgentState.EXECUTING
            
            # 调用 LLM
            response = self._call_llm(prompt)
            
            # 解析响应
            thought, action, action_input = self._parse_response(response)
            
            step = Step(
                step_number=step_num,
                thought=thought,
                action=action,
                action_input=action_input
            )
            
            # 执行动作
            if action and action in self.tools:
                self.current_state = AgentState.WAITING_TOOL
                
                tool = self.tools[action]
                result = ""
                
                try:
                    if tool.handler:
                        result = tool.handler(**(action_input or {}))
                    else:
                        result = f"工具 {action} 未实现"
                except Exception as e:
                    result = f"错误: {str(e)}"
                    step.is_error = True
                
                tool_calls.append(ToolCall(
                    tool_name=action,
                    arguments=action_input or {},
                    result=result
                ))
                
                step.observation = str(result)[:200]
                prompt += f"\n{response}\n观察: {result}\n"
                
            elif action == "最终答案":
                # 完成
                self.current_state = AgentState.DONE
                steps.append(step)
                
                return AgentResponse(
                    final_answer=action_input.get("answer", response),
                    steps=steps,
                    tool_calls=tool_calls,
                    memory_context=memory_context,
                    state=self.current_state
                )
            else:
                step.observation = "无法解析动作"
            
            steps.append(step)
            
            # 检查是否需要反思
            if step_num >= 3 and step_num % 3 == 0:
                prompt = self._add_reflection(prompt, steps[-3:])
        
        # 超时
        self.current_state = AgentState.DONE
        return AgentResponse(
            final_answer="抱歉，任务执行超时",
            steps=steps,
            tool_calls=tool_calls,
            memory_context=memory_context,
            state=self.current_state,
            error="max_steps_exceeded"
        )
    
    def _parse_response(self, response: str) -> Tuple[str, Optional[str], Optional[Dict]]:
        """解析 LLM 响应"""
        thought = ""
        action = None
        action_input = {}
        
        lines = response.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("Thought:"):
                thought = line[8:].strip()
            elif line.startswith("Action:"):
                action = line[8:].strip()
            elif line.startswith("Action Input:"):
                try:
                    # 提取 JSON
                    json_str = line[13:].strip()
                    if json_str.startswith("{") and json_str.endswith("}"):
                        action_input = json.loads(json_str)
                    elif json_str.startswith("{{") and json_str.endswith("}}"):
                        action_input = json.loads(json_str[1:-1])
                except json.JSONDecodeError:
                    # 尝试整个响应中找 JSON
                    matches = re.findall(r'\{[^{}]*\}', response)
                    for m in matches:
                        try:
                            action_input = json.loads(m)
                            break
                        except:
                            pass
            elif "最终答案" in line or "Final Answer" in line:
                action = "最终答案"
                # 提取答案
                if ":" in line:
                    answer = line.split(":", 1)[1].strip()
                    action_input = {"answer": answer}
        
        return thought, action, action_input
    
    def _add_reflection(self, prompt: str, recent_steps: List[Step]) -> str:
        """添加反思"""
        steps_summary = "\n".join([
            f"步骤 {s.step_number}: {s.thought[:50]} -> {s.observation[:50]}"
            for s in recent_steps
        ])
        
        reflection = f"""
## 反思
最近步骤:
{steps_summary}

思考:
1. 已有哪些关键信息?
2. 需要什么新信息?
3. 下一步应该怎么做?

继续:
"""
        return prompt + reflection
    
    # ============================================================
    # 聊天模式
    # ============================================================
    
    def chat(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> AgentResponse:
        """
        聊天模式
        
        Args:
            message: 用户消息
            session_id: 会话ID
            
        Returns:
            AgentResponse
        """
        # 保存用户消息
        if session_id and self.memory:
            self.memory.session_add_message(session_id, "user", message)
        
        # 运行 Agent
        response = self.run(message, session_id)
        
        # 保存助手消息
        if session_id and self.memory:
            self.memory.session_add_message(session_id, "assistant", response.final_answer)
        
        return response
    
    # ============================================================
    # 工具
    # ============================================================
    
    def list_tools(self) -> List[Dict]:
        """列出所有工具"""
        return [t.to_dict() for t in self.tools.values()]
    
    def get_state(self) -> AgentState:
        """获取当前状态"""
        return self.current_state
    
    def reset(self):
        """重置 Agent"""
        self.conversation_history = []
        self.current_state = AgentState.IDLE
