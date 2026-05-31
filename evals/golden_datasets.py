"""
用于 Agent 评测的黄金数据集(Golden Datasets)。

黄金数据集是一组已知正确、必须始终通过的测试用例。
它们和 prompt 一起纳入版本控制 —— 当你修改 prompt 时,
就运行黄金数据集来确认没有改坏任何东西。

为什么叫"黄金"?
- 它们是你的事实来源(source of truth)
- 如果某个黄金用例失败,说明 Agent 坏了(而不是测试坏了)
- 它们既覆盖正常路径(happy path),也覆盖边界情况(edge case)
"""

# ============================================================
# 结构化输出黄金数据集
# 测试:JSON 解析、schema 合规性
#
# 注意:为清晰起见,schema 采用带示例的多行格式。
# 单行的 schema 经常会让模型困惑。
# ============================================================

STRUCTURED_OUTPUT_GOLDEN = [
    # 正常路径:标准问题
    {
        "input": "Explain quantum computing in one sentence",
        "schema": """{
  "topic": "the topic name as a string",
  "difficulty": "beginner" or "intermediate" or "advanced"
}

Example: {"topic": "machine learning", "difficulty": "intermediate"}""",
        "must_have_fields": ["topic", "difficulty"]
    },
    # 正常路径:简单问题
    {
        "input": "What is Python in one sentence?",
        "schema": """{
  "topic": "the topic name as a string",
  "difficulty": "beginner" or "intermediate" or "advanced"
}

Example: {"topic": "web development", "difficulty": "beginner"}""",
        "must_have_fields": ["topic", "difficulty"]
    },
    # 边界情况:含数字的问题
    {
        "input": "What is the significance of 42?",
        "schema": """{
  "answer": "your answer as a string"
}

Example: {"answer": "It is the meaning of life"}""",
        "must_have_fields": ["answer"]
    },
    # 边界情况:含特殊字符的问题
    {
        "input": "What does hello world mean in programming?",
        "schema": """{
  "explanation": "your explanation as a string"
}

Example: {"explanation": "It is a simple test program"}""",
        "must_have_fields": ["explanation"]
    },
]


# ============================================================
# Tool Call 黄金数据集
# 测试:正确的工具选择、合法的参数
# ============================================================

TOOL_CALL_GOLDEN = [
    # 正常路径:乘法
    {
        "input": "What is 42 * 7?",
        "expected_tool": "calculator",
        "expected_args": {"operation": "multiply"}
    },
    # 正常路径:加法
    {
        "input": "Calculate 100 + 50",
        "expected_tool": "calculator",
        "expected_args": {"operation": "add"}
    },
    # 正常路径:除法
    {
        "input": "What is 100 / 5?",
        "expected_tool": "calculator",
        "expected_args": {"operation": "divide"}
    },
    # 正常路径:减法
    {
        "input": "What's 50 minus 25?",
        "expected_tool": "calculator",
        "expected_args": {"operation": "subtract"}
    },
    # 边界情况:应用题
    {
        "input": "If I have 15 apples and buy 27 more, how many do I have?",
        "expected_tool": "calculator",
        "expected_args": {"operation": "add"}
    },
]


# ============================================================
# 决策黄金数据集
# 测试:根据输入正确路由
# ============================================================

DECISION_GOLDEN = [
    # 明确的摘要请求
    {
        "input": "Can you summarize this article for me?",
        "choices": ["answer_question", "summarize_text", "translate"],
        "expected": "summarize_text"
    },
    # 明确的翻译请求
    {
        "input": "Translate 'hello' to Spanish",
        "choices": ["answer_question", "summarize_text", "translate"],
        "expected": "translate"
    },
    # 明确的问题
    {
        "input": "What is the capital of France?",
        "choices": ["answer_question", "summarize_text", "translate"],
        "expected": "answer_question"
    },
    # 计算 vs 直接回答
    {
        "input": "What is 5 + 5?",
        "choices": ["answer_question", "calculate", "search"],
        "expected": "calculate"
    },
]


# ============================================================
# 记忆黄金数据集
# 测试:存储 → 检索 的循环
# ============================================================

MEMORY_GOLDEN = [
    # 姓名的存储与回忆
    {
        "store_input": "My name is Alice",
        "query_input": "What's my name?",
        "expected_in_response": "Alice"
    },
    # 偏好的存储与回忆
    {
        "store_input": "I prefer dark mode",
        "query_input": "What's my preference for display mode?",
        "expected_in_response": "dark"
    },
    # 地点的存储与回忆
    {
        "store_input": "I live in New York",
        "query_input": "Where do I live?",
        "expected_in_response": "New York"
    },
]


# ============================================================
# 边界情况黄金数据集
# 测试:经常会让 prompt 失效的边界条件
# ============================================================

EDGE_CASES_GOLDEN = {
    "empty_input": {
        "structured": {
            "input": "Respond with a greeting",
            "schema": '{"response": "your response"}\n\nExample: {"response": "Hello!"}',
            "must_have_fields": ["response"]
        }
    },
    "very_long_input": {
        "structured": {
            "input": "Summarize: " + "very " * 20 + "complex topic",
            "schema": '{"summary": "brief summary"}\n\nExample: {"summary": "A complex topic"}',
            "must_have_fields": ["summary"]
        }
    },
    "unicode_input": {
        "structured": {
            "input": "What does hello mean in Chinese?",
            "schema": '{"translation": "the translation"}\n\nExample: {"translation": "你好"}',
            "must_have_fields": ["translation"]
        }
    },
    "json_in_input": {
        "structured": {
            "input": "What format is this: key value pairs?",
            "schema": '{"parsed": "your answer"}\n\nExample: {"parsed": "dictionary"}',
            "must_have_fields": ["parsed"]
        }
    },
}
