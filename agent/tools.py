"""
Agent 的 tool 定义。

Tool 是 API,而不是能力。
Agent 请求 tool;由系统来执行它们。
"""

from typing import Any


def calculator(a: float, b: float, operation: str = "add") -> float:
    """
    简单的计算器 tool。

    Args:
        a: 第一个数
        b: 第二个数
        operation: "add"、"subtract"、"multiply"、"divide" 之一

    Returns:
        运算结果
    """
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else float('inf'),
    }
    
    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")
    
    return operations[operation](a, b)


def get_tool_schema() -> dict:
    """
    获取可用 tool 的 schema。

    这是 agent 在决定调用哪个 tool 时所看到的内容。

    Returns:
        tool 名称到其 schema 的字典
    """
    return {
        "calculator": {
            "description": "Perform basic arithmetic operations",
            "parameters": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The operation to perform"
                }
            },
            "required": ["a", "b"]
        }
    }


def execute_tool(tool_name: str, arguments: dict) -> Any:
    """
    按名称并使用给定参数执行一个 tool。

    Args:
        tool_name: 要执行的 tool 名称
        arguments: tool 的参数字典

    Returns:
        tool 执行的结果

    Raises:
        ValueError: 如果 tool 不存在
    """
    tools = {
        "calculator": calculator,
    }
    
    if tool_name not in tools:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    return tools[tool_name](**arguments)