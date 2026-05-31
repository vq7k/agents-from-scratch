"""
Agent —— 本文件贯穿全部 10 节课逐步成长。

这是本仓库的核心。每节课恰好为这个 agent 增加一项能力，
循序渐进地建立理解。

课程进度：
01：基础 LLM 对话
02：system prompt（角色）
03：结构化输出（JSON）
04：决策
05：tool calling
06：agent loop
07：记忆
08：规划
09：原子动作
10：AoT（Atom of Thought，思维原子）
"""

from typing import Any

from shared.llm import LocalLLM
from shared.utils import extract_json_from_text
from agent.state import AgentState
from agent.memory import Memory
from agent.tools import get_tool_schema, execute_tool
from agent.planner import create_plan, create_atomic_action, create_aot_graph, execute_graph


class Agent:
    """
    一个能力随课程逐步成长的 AI agent。

    在整个仓库中这始终是同一个 agent —— 它只是随着课程推进
    不断获得新的方法和能力。
    """
    
    def __init__(self, model_path: str):
        """
        初始化 agent。

        Args:
            model_path: GGUF 模型文件的路径
        """
        # 第 01 课：基础 LLM 交互
        self.llm = LocalLLM(model_path)

        # 第 02 课：用 system prompt 保证行为一致
        self.system_prompt = (
            "You are a calm, precise, and helpful AI assistant. "
            "You explain concepts simply and avoid unnecessary jargon. "
            "You are honest about what you know and don't know."
        )
        
        # 第 06 课：agent 状态
        self.state = AgentState()

        # 第 07 课：记忆系统
        self.memory = Memory()
    
    # ============================================================
    # 第 01 课：基础 LLM 对话
    # ============================================================

    def simple_generate(self, user_input: str) -> str:
        """
        最简单的交互方式 —— 直接把文本传给 LLM。

        第 01 课版本。

        Args:
            user_input: 用户的问题或请求

        Returns:
            模型的回复
        """
        return self.llm.generate(user_input)
    
    # ============================================================
    # 第 02 课：system prompt（角色）
    # ============================================================

    def generate_with_role(self, user_input: str) -> str:
        """
        借助 system prompt 来塑造行为后再生成。

        第 02 课版本。

        Args:
            user_input: 用户的问题或请求

        Returns:
            带有角色化行为的模型回复
        """
        # 使用一种不会让模型混淆的格式
        prompt = f"""{self.system_prompt}

User: {user_input}
Assistant:"""
        
        response = self.llm.generate(prompt)
        # 清理可能残留的标签碎片
        response = response.replace('<SYSTEM>', '').replace('</SYSTEM>', '')
        response = response.replace('<USER>', '').replace('</USER>', '')
        return response.strip()
    
    # ============================================================
    # 第 03 课：结构化输出
    # ============================================================

    def generate_structured(self, user_input: str, schema: str) -> dict | None:
        """
        生成带校验和重试的结构化 JSON 输出。

        第 03 课版本。

        Args:
            user_input: 用户的问题或请求
            schema: JSON schema 描述

        Returns:
            解析后的 JSON 字典；若所有重试都失败则返回 None
        """
        prompt = f"""{self.system_prompt}

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no extra text before or after the JSON
3. Start your response with {{ and end with }}

Schema you must follow:
{schema}

User request: {user_input}

Response (JSON only):"""
        
        # 最多重试 3 次
        for attempt in range(3):
            response = self.llm.generate(prompt, temperature=0.0)
            parsed = extract_json_from_text(response)

            if parsed is not None:
                return parsed
        
        return None
    
    # ============================================================
    # 第 04 课：决策
    # ============================================================

    def decide(self, user_input: str, choices: list[str]) -> str | None:
        """
        让模型从有限的选项集合中做出选择。

        第 04 课版本。

        Args:
            user_input: 需要据此做决策的输入
            choices: 可选动作/决策的列表

        Returns:
            选中的动作；若决策失败则返回 None
        """
        options = "\n".join(f"- {choice}" for choice in choices)
        
        prompt = f"""{self.system_prompt}

You must choose ONE of the following options. Respond with ONLY valid JSON.

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Available choices:
{options}

Required JSON format:
{{"decision": "one_of_the_choices_above"}}

User request: {user_input}

Response (JSON only):"""
        
        for attempt in range(3):
            response = self.llm.generate(prompt, temperature=0.0)
            parsed = extract_json_from_text(response)
            
            if parsed and "decision" in parsed:
                decision = parsed["decision"]
                if decision in choices:
                    return decision
        
        return None
    
    # ============================================================
    # 第 05 课：工具
    # ============================================================

    def request_tool(self, user_input: str) -> dict | None:
        """
        让模型发起一次 tool call。

        第 05 课版本。

        Args:
            user_input: 用户的请求

        Returns:
            tool call 的规格说明；若请求失败则返回 None
        """
        prompt = f"""{self.system_prompt}

You are a tool-calling assistant. When asked a math question, you must respond with ONLY valid JSON.

Available tool: calculator
- Parameters: a (number), b (number), operation ("add", "subtract", "multiply", or "divide")

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Example format:
{{"tool": "calculator", "arguments": {{"a": 42, "b": 7, "operation": "multiply"}}}}

User request: {user_input}

Response (JSON only):"""
        
        for attempt in range(3):
            response = self.llm.generate(prompt, temperature=0.0)
            parsed = extract_json_from_text(response)
            
            if parsed and "tool" in parsed and "arguments" in parsed:
                return parsed
        
        return None
    
    def execute_tool_call(self, tool_call: dict) -> Any:
        """
        执行模型发起的一次 tool call。

        Args:
            tool_call: 包含 "tool" 和 "arguments" 的字典

        Returns:
            工具执行的结果
        """
        return execute_tool(tool_call["tool"], tool_call["arguments"])
    
    # ============================================================
    # 第 06 课：agent loop
    # ============================================================

    def agent_step(self, user_input: str) -> dict | None:
        """
        执行 agent loop 的一步：观察 → 决策 → 行动。

        第 06 课版本。

        Args:
            user_input: 用户输入或系统观察结果

        Returns:
            行动决策；若该步失败则返回 None
        """
        state_dict = self.state.to_dict()
        
        prompt = f"""{self.system_prompt}

You are an agent. You must decide the next action and respond with ONLY valid JSON.

Current state: steps={state_dict.get('steps', 0)}, done={state_dict.get('done', False)}

Available actions: analyze, research, summarize, answer, done

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Required JSON format:
{{"action": "action_name", "reason": "explanation"}}

User input: {user_input}

Response (JSON only):"""
        
        for attempt in range(3):
            response = self.llm.generate(prompt, temperature=0.0)
            parsed = extract_json_from_text(response)
            
            if parsed and "action" in parsed:
                if "reason" not in parsed:
                    parsed["reason"] = f"Taking action: {parsed['action']}"
                self.state.increment_step()
                return parsed
        
        return None
    
    def run_loop(self, user_input: str, max_steps: int = 5):
        """
        运行 agent loop 多步。

        Args:
            user_input: 初始用户输入
            max_steps: 最多执行的步数

        Returns:
            行动结果的列表
        """
        self.state.reset()
        results = []
        
        while not self.state.done and self.state.steps < max_steps:
            action = self.agent_step(user_input)
            
            if action:
                results.append(action)
                
                # 简单的终止条件
                if action.get("action") == "done":
                    self.state.mark_done()
            else:
                break
        
        return results
    
    # ============================================================
    # 第 07 课：记忆
    # ============================================================

    def run_with_memory(self, user_input: str) -> dict | None:
        """
        带记忆上下文运行 agent。

        第 07 课版本。

        Args:
            user_input: 用户输入

        Returns:
            回复，可能附带一次记忆更新
        """
        memory_context = self.memory.get_all()

        # 构造记忆上下文字符串
        if memory_context:
            memory_str = "You remember the following:\n" + "\n".join(f"- {item}" for item in memory_context)
        else:
            memory_str = "You have no memories yet."
        
        prompt = f"""{self.system_prompt}

You are an agent with memory. You must respond with ONLY valid JSON.

{memory_str}

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}
4. If the user tells you information (like their name), save it to memory
5. If the user asks about something you remember, USE YOUR MEMORY to answer

Required JSON format:
{{"reply": "your response text", "save_to_memory": "fact to remember" or null}}

Examples:
- User says "My name is Alice" → {{"reply": "Nice to meet you, Alice!", "save_to_memory": "User's name is Alice"}}
- User asks "What's my name?" and you remember "User's name is Alice" → {{"reply": "Your name is Alice", "save_to_memory": null}}

User input: {user_input}

Response (JSON only):"""
        
        for attempt in range(3):
            response = self.llm.generate(prompt, temperature=0.0)
            parsed = extract_json_from_text(response)
            
            if parsed and "reply" in parsed:
                # 如有要求则存入记忆
                if parsed.get("save_to_memory"):
                    self.memory.add(parsed["save_to_memory"])
                
                self.state.increment_step()
                return parsed
        
        return None
    
    # ============================================================
    # 第 08 课：规划
    # ============================================================

    def create_plan(self, goal: str) -> dict | None:
        """
        生成一个用于达成目标的规划。

        第 08 课版本。

        Args:
            goal: 要达成的目标

        Returns:
            包含若干步骤的规划
        """
        plan = create_plan(self.llm, goal)
        
        if plan:
            self.state.current_plan = plan
        
        return plan
    
    def execute_plan(self, plan: dict) -> list:
        """
        逐步执行一个规划。

        Args:
            plan: 包含 "steps" 列表的规划字典

        Returns:
            执行结果的列表
        """
        if not plan or "steps" not in plan:
            return []
        
        results = []
        
        for step in plan["steps"]:
            # 简化的执行 —— 实际中你会在这里调用工具等等
            result = {
                "step": step,
                "executed": True
            }
            results.append(result)
            self.state.increment_step()
        
        return results
    
    # ============================================================
    # 第 09 课：原子动作
    # ============================================================

    def create_atomic_action(self, step: str) -> dict | None:
        """
        把规划中的一个步骤转换成一个原子动作。

        第 09 课版本。

        原子动作是尽可能最小的动作，它们可以：
        - 被独立校验
        - 被隔离测试
        - 被安全执行
        - 在需要时被回滚

        Args:
            step: 规划中的一个步骤（例如 "Write an explanation of AI agents"）

        Returns:
            包含 "action" 和 "inputs" 的原子动作字典；若生成失败则返回 None
        """
        return create_atomic_action(self.llm, step)
    
    # ============================================================
    # 第 10 课：Atom of Thought（AoT，思维原子）
    # ============================================================

    def create_aot_plan(self, goal: str) -> dict | None:
        """
        生成一张 AoT 执行图。

        第 10 课版本。

        Args:
            goal: 要达成的目标

        Returns:
            包含原子节点及依赖关系的 AoT 图
        """
        return create_aot_graph(self.llm, goal)
    
    def execute_aot_plan(self, graph: dict) -> list:
        """
        按依赖关系执行一张 AoT 图。

        Args:
            graph: AoT 图

        Returns:
            执行结果的列表
        """
        def execute_action(action: str):
            # 实际动作执行的占位实现
            return f"Executed: {action}"
        
        return execute_graph(graph, execute_action)
    
    # ============================================================
    # 主运行方法（随课程演进）
    # ============================================================

    def run(self, user_input: str) -> str:
        """
        agent 的主入口。

        该方法随课程演进，使用不同的能力。
        当前处于：第 07 课（带记忆）

        Args:
            user_input: 用户的问题或请求

        Returns:
            agent 的回复
        """
        result = self.run_with_memory(user_input)
        
        if result and "reply" in result:
            return result["reply"]
        
        # 回退到简单生成
        return self.generate_with_role(user_input)