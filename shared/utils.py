"""
Agent 的工具函数。

这些都是平淡、可预测的辅助函数,做的事和名字完全一致。
这里没有任何花哨的东西。
"""

import json


def safe_json_parse(text: str) -> dict | None:
    """
    安全地解析 JSON 文本,失败时返回 None。

    Args:
        text: 可能是合法 JSON 的字符串

    Returns:
        解析后的 JSON 字典,解析失败则返回 None
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def extract_json_from_text(text: str) -> dict | None:
    """
    尝试从可能含有额外内容的文本中提取 JSON。

    这能处理模型在 JSON 前后添加说明文字的情况。

    Args:
        text: 可能包含 JSON 的文本

    Returns:
        若找到则返回解析后的 JSON,否则返回 None
    """
    if not text:
        return None
    
    # 清理文本——移除常见的 markdown 代码块
    text = text.strip()
    if text.startswith('```json'):
        text = text[7:]
    elif text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]
    text = text.strip()
    
    # 移除模型有时会加上的常见前缀
    prefixes = ["JSON:", "Response:", "Answer:", "Here's the JSON:", "The JSON is:"]
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    
    # 先尝试直接解析
    result = safe_json_parse(text)
    if result is not None:
        return result

    # 尝试在花括号之间查找 JSON(最常见的情况)
    start = text.find('{')
    end = text.rfind('}')
    
    if start != -1 and end != -1 and end > start:
        json_text = text[start:end+1]
        result = safe_json_parse(json_text)
        if result is not None:
            return result
        
        # 尝试修复常见问题:未闭合的字符串、缺失的引号
        # 这是一个简单的启发式方法——如果已经很接近,就尝试修复
        if json_text.count('"') % 2 != 0:
            # 引号数量为奇数——尝试闭合最后一个字符串
            last_quote = json_text.rfind('"')
            if last_quote > 0:
                # 检查它是否是一个起始引号
                before = json_text[:last_quote]
                if before.count('"') % 2 == 0:
                    # 这可能是一个未闭合的字符串,尝试添加一个闭合引号
                    try_fix = json_text[:last_quote+1] + '"' + json_text[last_quote+1:] + '}'
                    result = safe_json_parse(try_fix)
                    if result is not None:
                        return result
    
    # 尝试在方括号之间查找 JSON(用于数组)
    start = text.find('[')
    end = text.rfind(']')
    
    if start != -1 and end != -1 and end > start:
        json_text = text[start:end+1]
        result = safe_json_parse(json_text)
        if result is not None:
            return result
    
    # 最后手段:尝试从文本中提取键值对
    # 这非常依赖启发式,可能效果不佳
    if '{' in text or '[' in text:
        # 尝试查找任何类似 JSON 的结构
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('{') or line.startswith('['):
                result = safe_json_parse(line)
                if result is not None:
                    return result
    
    return None


def format_messages(messages: list[dict]) -> str:
    """
    将消息列表格式化为可读的字符串。

    Args:
        messages: 包含 'role' 和 'content' 键的消息字典列表

    Returns:
        格式化后的字符串表示
    """
    formatted = []
    for msg in messages:
        role = msg.get('role', 'unknown').upper()
        content = msg.get('content', '')
        formatted.append(f"[{role}]\n{content}\n")
    
    return "\n".join(formatted)