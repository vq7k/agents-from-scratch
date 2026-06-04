#!/usr/bin/env python3
"""
完整的 Agent 示例

本脚本演示了使用全部 12 节课功能的 agent。
它旨在作为各部分如何组合在一起的参考。
"""

import textwrap
import time

from agent.agent import Agent
from shared.config import MODEL_PATH


def lesson_01_basic_chat():
    """第 01 课:基础 LLM 交互"""
    print("\n" + "="*50)
    print("LESSON 01: Basic LLM Chat")
    print("="*50)
    
    agent = Agent(MODEL_PATH)
    response = agent.simple_generate("解释一下什么是 AI agent?")
    print(f"Response: {response}")


def lesson_02_with_role():
    """第 02 课:System prompt"""
    print("\n" + "="*50)
    print("LESSON 02: With System Prompt")
    print("="*50)
    
    agent = Agent(MODEL_PATH)
    response = agent.generate_with_role("解释一下什么是 AI agent?")
    print(f"Response: {response}")


def lesson_03_structured():
    """第 03 课:结构化输出"""
    print("\n" + "="*50)
    print("LESSON 03: Structured Output")
    print("="*50)

    agent = Agent(MODEL_PATH)

    # schema:给模型看的 "输出格式说明" , 不是拿去 json.parse 的真 JSON。
    #   它会被塞进 prompt(见 Agent.generate_structured), 模型照着它产出真正的 JSON。
    #   写法是 TypeScript 风味的 "伪 schema":
    #     string       → 这个字段要填一个字符串
    #     "a" | "b"    → 这个字段只能取列出的值之一(枚举)
    #   所以这里出现 string、| 是故意的 (标准 JSON 并不允许),因为它的读者是 LLM,不是解析器。
    #   (三引号里顶格写,是为了发给模型的文本不带多余缩进。)
    schema = """{
  "topic": string,
  "difficulty": "beginner" | "intermediate" | "advanced"
}"""

    result = agent.generate_structured(
        "解释一下量子计算",
        schema
    )
    print(f"Structured result: {result}")


def lesson_04_decisions():
    """第 04 课:决策"""
    print("\n" + "="*50)
    print("LESSON 04: Decision Making")
    print("="*50)

    agent = Agent(MODEL_PATH)

    decision = agent.decide(
        "你能帮我总结一下这篇文章吗?",
        choices=["answer_question", "summarize_text", "translate"]
    )
    print(f"Decision: {decision}")


def lesson_05_tools():
    """第 05 课:tool calling"""
    print("\n" + "="*50)
    print("LESSON 05: Tool Calling")
    print("="*50)

    agent = Agent(MODEL_PATH)

    tool_call = agent.request_tool("42 乘以 7 等于多少?")
    print(f"Tool request: {tool_call}")

    if tool_call:
        result = agent.execute_tool_call(tool_call)
        print(f"Tool result: {result}")


def lesson_06_agent_loop():
    """第 06 课:Agent 循环"""
    print("\n" + "="*50)
    print("LESSON 06: Agent Loop")
    print("="*50)
    
    agent = Agent(MODEL_PATH)
    
    print("\nNote: Repetition in early iterations is expected.")
    print("The agent refines its understanding step by step and may repeat analysis")
    print("before converging on a clearer explanation.\n")
    
    results = agent.run_loop("帮我理解循环", max_steps=3)
    
    for i, result in enumerate(results, 1):
        print(f"Iteration {i}:")
        action = result.get("action", "unknown")
        reason = result.get("reason", "No reason provided")
        print(f"  Action: {action}")
        print(f"  Reason: {reason}")
        if i < len(results):
            print()


def lesson_07_memory():
    """第 07 课:记忆"""
    print("\n" + "="*50)
    print("LESSON 07: Memory")
    print("="*50)

    agent = Agent(MODEL_PATH)

    # 第一次交互——存储名字
    response1 = agent.run_with_memory("我叫小爱")
    if response1 and "reply" in response1:
        print(f"Response 1: {response1['reply']}")
        if response1.get("save_to_memory"):
            print(f"  → Saved to memory: {response1['save_to_memory']}")
    else:
        print(f"Response 1: {response1}")

    # 第二次交互——回忆名字
    response2 = agent.run_with_memory("我叫什么名字?")
    if response2 and "reply" in response2:
        print(f"Response 2: {response2['reply']}")
        if response2.get("save_to_memory"):
            print(f"  → Saved to memory: {response2['save_to_memory']}")
    else:
        print(f"Response 2: {response2}")

    print(f"\nMemory contents: {agent.memory.get_all()}")


def lesson_08_planning():
    """第 08 课:规划"""
    print("\n" + "="*50)
    print("LESSON 08: Planning")
    print("="*50)

    agent = Agent(MODEL_PATH)

    plan = agent.create_plan("写一篇关于 AI agent 的博客文章")
    print(f"Plan: {plan}")

    if plan:
        results = agent.execute_plan(plan)
        print(f"Execution results: {results}")


def lesson_09_atomic_actions():
    """第 09 课:原子动作"""
    print("\n" + "="*50)
    print("LESSON 09: Atomic Actions")
    print("="*50)

    agent = Agent(MODEL_PATH)

    # 将一个计划步骤转换为原子动作
    step = "写一段对 AI agent 的讲解"
    atomic_action = agent.create_atomic_action(step)
    print(f"Step: {step}")
    print(f"Atomic action: {atomic_action}")

    # 以计划中的某个步骤为例
    plan = agent.create_plan("创建一个关于 Python 的教程")
    if plan and "steps" in plan and plan["steps"]:
        first_step = plan["steps"][0]
        atomic_action_from_plan = agent.create_atomic_action(first_step)
        print(f"\nPlan step: {first_step}")
        print(f"Atomic action from plan step: {atomic_action_from_plan}")


def lesson_10_aot():
    """第 10 课:Atom of Thought(思维原子)"""
    print("\n" + "="*50)
    print("LESSON 10: Atom of Thought")
    print("="*50)

    agent = Agent(MODEL_PATH)
    
    graph = agent.create_aot_plan("研究并撰写一篇文章")
    print(f"AoT graph: {graph}")
    
    if graph:
        results = agent.execute_aot_plan(graph)
        print(f"Execution results: {results}")


def lesson_11_evals():
    """第 11 课:Evals(回归测试)"""
    print("\n" + "="*50)
    print("LESSON 11: Evals")
    print("="*50)
    
    from agent.evals import AgentEval, print_eval_report
    from evals.golden_datasets import (
        STRUCTURED_OUTPUT_GOLDEN,
        TOOL_CALL_GOLDEN,
        DECISION_GOLDEN,
        MEMORY_GOLDEN
    )
    
    agent = Agent(MODEL_PATH)
    evaluator = AgentEval(agent)
    
    print("\nRunning eval suites...")
    print("(This may take a minute as it runs multiple agent calls)\n")
    
    # 为演示只跑一个子集(完整套件可能很慢)
    # 为了快速演示,从每个套件取前 2 个用例
    results = evaluator.run_all(
        structured_cases=STRUCTURED_OUTPUT_GOLDEN[:2],
        tool_cases=TOOL_CALL_GOLDEN[:2],
        decision_cases=DECISION_GOLDEN[:2],
        memory_cases=MEMORY_GOLDEN[:1]
    )
    
    # 打印报告
    print_eval_report(results)

    # 展示如何访问单个结果
    print("\nAccessing individual suite results:")
    for suite in results:
        print(f"  {suite.name}: {suite.pass_rate:.0%} pass rate")


def lesson_12_telemetry():
    """第 12 课:Telemetry(运行时可观测性)"""
    print("\n" + "="*50)
    print("LESSON 12: Telemetry")
    print("="*50)
    
    from agent.telemetry import Telemetry
    
    agent = Agent(MODEL_PATH)
    telemetry = Telemetry(log_file="agent_telemetry.jsonl")
    
    # 清除之前的 telemetry,保证演示干净
    telemetry.clear()
    
    print("\nRunning agent operations with telemetry...")
    
    # 为本次交互启动一个 trace
    trace_id = telemetry.start_trace()
    print(f"Trace ID: {trace_id}")
    
    # 操作 1:结构化输出
    print("\n1. Structured output call...")
    start = time.time()
    result1 = agent.generate_structured(
        "Python 是什么?",
        '{"answer": string, "difficulty": "beginner" | "intermediate" | "advanced"}'
    )
    duration1 = (time.time() - start) * 1000
    
    telemetry.log_llm_call(
        prompt_length=150,
        response_length=len(str(result1)) if result1 else 0,
        duration_ms=duration1,
        success=result1 is not None,
        error=None if result1 else "Failed to parse JSON"
    )
    print(f"   Result: {result1}")
    print(f"   Duration: {duration1:.0f}ms")
    
    # 操作 2:tool 调用
    print("\n2. Tool call...")
    start = time.time()
    tool_call = agent.request_tool("15 乘以 8 等于多少?")
    duration2 = (time.time() - start) * 1000
    
    telemetry.log_llm_call(
        prompt_length=200,
        response_length=len(str(tool_call)) if tool_call else 0,
        duration_ms=duration2,
        success=tool_call is not None
    )
    
    if tool_call:
        telemetry.log_tool_call(
            tool_name=tool_call.get("tool", "unknown"),
            arguments=tool_call.get("arguments", {}),
            result=agent.execute_tool_call(tool_call) if tool_call else None,
            duration_ms=1.0  # tool 执行很快
        )
        print(f"   Tool: {tool_call}")
    
    # 操作 3:记忆
    print("\n3. Memory operation...")
    start = time.time()
    result3 = agent.run_with_memory("我最喜欢的颜色是蓝色")
    duration3 = (time.time() - start) * 1000
    
    telemetry.log_llm_call(
        prompt_length=300,
        response_length=len(str(result3)) if result3 else 0,
        duration_ms=duration3,
        success=result3 is not None
    )
    telemetry.log_memory_operation("add", "favorite color is blue")
    print(f"   Result: {result3}")
    
    # 打印 telemetry 摘要
    telemetry.print_summary()

    # 展示最近的 span
    print("\nRecent spans:")
    for span in telemetry.get_recent_spans(5):
        event = span.get("event_type", "unknown")
        duration = span.get("duration_ms", "N/A")
        print(f"  [{event}] duration={duration}ms")
    
    print(f"\nTelemetry logged to: agent_telemetry.jsonl")
    print("View with: cat agent_telemetry.jsonl | head -5")


def main():
    """运行所有课程示例"""
    print("\n" + "#"*50)
    print("# AI Agent Examples - All Lessons")
    print("#"*50)
    
    try:
        # 注释掉你想跳过的课程
        # lesson_01_basic_chat()
        # lesson_02_with_role()
        # lesson_03_structured()
        lesson_04_decisions()
        # lesson_05_tools()
        # lesson_06_agent_loop()
        # lesson_07_memory()
        # lesson_08_planning()
        # lesson_09_atomic_actions()
        # lesson_10_aot()
        # lesson_11_evals()
        # lesson_12_telemetry()
        
        print("\n" + "="*50)
        print("All examples completed!")
        print("="*50)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Downloaded a GGUF model")
        print("2. Placed it in the models/ directory")
        print("3. Updated the model path in this script")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()