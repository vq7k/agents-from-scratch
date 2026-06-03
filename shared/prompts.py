"""
Agent 的 prompt 模板。

这些函数构建的 prompt 会随课程逐步演进:
- 第 01 课:base_prompt(纯文本)
- 第 02 课:system_prompt(加入角色)
- 第 03 课:json_contract(加入结构)
- 第 04 课及之后:用于决策、工具、规划的专用 prompt

在 Agent 系统中,prompt 是一等公民。
"""


def base_prompt(user_input: str) -> str:
    """
    最简单的 prompt —— 只有用户的文本。

    用于:第 01 课

    Args:
        user_input: 用户的问题或请求

    Returns:
        原封不动的用户输入
    """
    return user_input


def system_prompt(role: str, user_input: str) -> str:
    """
    加入 system 角色来塑造行为。

    用于:第 02 课

    Args:
        role: 对助手角色和行为的描述
        user_input: 用户的问题或请求

    Returns:
        包含 system 和 user 两部分的格式化 prompt
    """
    return f"""<SYSTEM>
{role}
</SYSTEM>

<USER>
{user_input}
</USER>"""


def json_contract(schema: str, content: str) -> str:
    """
    强制输出结构化的 JSON。

    用于:第 03 课

    Args:
        schema: JSON schema 的描述
        content: 待处理的内容

    Returns:
        强制输出 JSON 的 prompt
    """
    return f"""Return ONLY valid JSON.
No explanations. No markdown. No extra text.

Schema:
{schema}

内容:
{content}"""


def decision_prompt(choices: list[str], user_input: str) -> str:
    """
    让模型从有限的选项集合中做出选择。

    用于:第 04 课

    Args:
        choices: 可选的动作/决策列表
        user_input: 需要据此做决策的输入

    Returns:
        强制做出决策的 prompt
    """
    options = "\n".join(f"- {choice}" for choice in choices)
    
    return f"""你必须从以下选项中选择一个。
Return ONLY valid JSON.

可选项:
{options}

Schema:
{{ "decision": string }}

输入:
{user_input}"""


def tool_call_prompt(tools: dict, user_input: str) -> str:
    """
    向模型请求一次 tool call。

    用于:第 05 课

    Args:
        tools: 可用工具及其 schema 的字典
        user_input: 用户的请求

    Returns:
        请求一次 tool call 的 prompt
    """
    return f"""你可以请求一次工具调用。

可用工具:
{tools}

Return ONLY valid JSON.

Schema:
{{
  "tool": string,
  "arguments": object
}}

用户请求:
{user_input}"""


def agent_step_prompt(state: dict, user_input: str) -> str:
    """
    基于当前状态生成 Agent 的下一个动作。

    用于:第 06 课

    Args:
        state: 当前的 Agent 状态
        user_input: 用户输入或系统观察结果

    Returns:
        用于执行 Agent 单步的 prompt
    """
    return f"""你是一个 agent。

当前状态:
{state}

决定下一个动作。

Return ONLY valid JSON.

Schema:
{{
  "action": string,
  "reason": string
}}

用户输入:
{user_input}"""


def memory_prompt(state: dict, memory: list, user_input: str) -> str:
    """
    带记忆上下文的 Agent prompt。

    用于:第 07 课

    Args:
        state: 当前的 Agent 状态
        memory: 相关记忆的列表
        user_input: 用户输入

    Returns:
        带记忆上下文的 prompt
    """
    return f"""你是一个带记忆的 agent。

当前状态:
{state}

相关记忆:
{memory}

决定接下来做什么。

Return ONLY valid JSON.

Schema:
{{
  "action": string,
  "save_to_memory": string | null
}}

用户输入:
{user_input}"""


def planning_prompt(goal: str) -> str:
    """
    生成实现目标的规划。

    用于:第 08 课

    Args:
        goal: 要实现的目标

    Returns:
        用于生成规划的 prompt
    """
    return f"""制定一个分步骤的计划来达成目标。

Return ONLY valid JSON.

Schema:
{{
  "steps": [string]
}}

目标:
{goal}"""


def atomic_action_prompt(step: str) -> str:
    """
    把规划中的一个步骤转换成原子动作。

    用于:第 09 课

    Args:
        step: 规划中的一个步骤

    Returns:
        用于生成原子动作的 prompt
    """
    return f"""将这个步骤转换为一个原子动作。

Return ONLY valid JSON.

Schema:
{{
  "action": string,
  "inputs": object
}}

步骤:
{step}"""


def aot_prompt(goal: str) -> str:
    """
    生成 Atom of Thought 执行图。

    用于:第 10 课

    Args:
        goal: 要实现的目标

    Returns:
        用于生成 AoT 图的 prompt
    """
    return f"""为目标生成一个原子执行图。

Return ONLY valid JSON.

Schema:
{{
  "nodes": [
    {{
      "id": string,
      "action": string,
      "depends_on": [string]
    }}
  ]
}}

目标:
{goal}"""