"""
Agent 的规划功能。

规划是数据生成,而非推理。
计划是可检查、可修改的数据结构。
"""

from shared.llm import LocalLLM


def create_plan(llm: LocalLLM, goal: str) -> dict | None:
    """
    生成一个达成目标的计划。

    用于:第 08 课

    Args:
        llm: 要使用的语言模型
        goal: 要达成的目标

    Returns:
        以字典形式返回的计划,含一个 "steps" 列表;生成失败则返回 None
    """
    from shared.utils import extract_json_from_text
    
    prompt = f"""Create a step-by-step plan to achieve the goal. Respond with ONLY valid JSON.

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Required JSON format:
{{"steps": ["step1", "step2", "step3"]}}

Goal: {goal}

Response (JSON only):"""
    
    for attempt in range(3):
        response = llm.generate(prompt, temperature=0.0)
        plan = extract_json_from_text(response)
        
        if plan and "steps" in plan and isinstance(plan["steps"], list):
            return plan
    
    return None


def create_atomic_action(llm: LocalLLM, step: str) -> dict | None:
    """
    将一个计划步骤转换为一个原子动作。

    用于:第 09 课

    Args:
        llm: 要使用的语言模型
        step: 计划中的一个步骤

    Returns:
        以字典形式返回的原子动作;生成失败则返回 None
    """
    from shared.utils import extract_json_from_text
    
    prompt = f"""Convert this step into an atomic action. Respond with ONLY valid JSON.

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Required JSON format:
{{
  "action": "action_name",
  "inputs": {{"key": "value"}}
}}

The action should be a simple, atomic operation name.
The inputs should be a dictionary with the parameters needed for this action.

Step to convert:
{step}

Response (JSON only):"""
    
    for attempt in range(3):
        response = llm.generate(prompt, temperature=0.0)
        action = extract_json_from_text(response)
        
        if action and "action" in action:
            return action
    
    return None


def create_aot_graph(llm: LocalLLM, goal: str) -> dict | None:
    """
    生成一个 Atom of Thought (AoT) 执行图。

    用于:第 10 课

    Args:
        llm: 要使用的语言模型
        goal: 要达成的目标

    Returns:
        含节点和依赖关系的 AoT 图;生成失败则返回 None
    """
    from shared.utils import extract_json_from_text
    
    prompt = f"""Create an atomic execution graph for the goal. Each node is a single action. Dependencies are node IDs. Respond with ONLY valid JSON.

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Required JSON format:
{{"nodes": [{{"id": "1", "action": "research", "depends_on": []}}, {{"id": "2", "action": "write", "depends_on": ["1"]}}]}}

Each node must have:
- id: unique string like "1", "2", "3"
- action: what to do (e.g., "research", "write", "review")
- depends_on: list of node IDs that must complete first (empty [] for first step)

Goal: {goal}

Response (JSON only):"""
    
    for attempt in range(3):
        response = llm.generate(prompt, temperature=0.0)
        graph = extract_json_from_text(response)
        
        if graph and "nodes" in graph and isinstance(graph["nodes"], list):
            # 校验图结构
            valid_nodes = []
            for node in graph["nodes"]:
                if isinstance(node, dict) and "id" in node and "action" in node and "depends_on" in node:
                    # 确保 depends_on 是一个列表
                    if not isinstance(node["depends_on"], list):
                        continue
                    valid_nodes.append(node)
            
            if valid_nodes:
                return {"nodes": valid_nodes}
    
    return None


def execute_graph(graph: dict, executor_func) -> list:
    """
    按照依赖关系执行一个 AoT 图。

    Args:
        graph: 含节点和依赖关系的 AoT 图
        executor_func: 执行每个动作的函数(接收 action 字符串)

    Returns:
        按顺序排列的执行结果列表
    """
    if not graph or "nodes" not in graph:
        return []
    
    nodes = graph["nodes"]
    executed = set()
    results = []
    
    # 简单的拓扑执行
    # 在真实实现中,这里会更加复杂
    max_iterations = len(nodes) * 2
    iteration = 0
    
    while len(executed) < len(nodes) and iteration < max_iterations:
        iteration += 1
        
        for node in nodes:
            node_id = node["id"]
            
            # 已执行过则跳过
            if node_id in executed:
                continue
            
            # 检查是否所有依赖都已满足
            dependencies = node.get("depends_on", [])
            if all(dep in executed for dep in dependencies):
                # 执行该节点
                try:
                    result = executor_func(node["action"])
                    results.append({
                        "node_id": node_id,
                        "action": node["action"],
                        "result": result,
                        "success": True
                    })
                    executed.add(node_id)
                except Exception as e:
                    results.append({
                        "node_id": node_id,
                        "action": node["action"],
                        "error": str(e),
                        "success": False
                    })
                    # 即使失败也标记为已执行,以避免无限循环
                    executed.add(node_id)
    
    return results