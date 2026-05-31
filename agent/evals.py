"""
Agent 评估框架。

Eval 是 Agent 的回归测试。
一个 eval 套件就是一个 Python 文件,运行你的 Agent 并断言没有出现回归。

本模块提供:
- 结构化输出校验
- tool call 准确性测试
- 记忆存储/检索循环测试
- 决策路由校验
"""

from typing import Any, Callable
from dataclasses import dataclass, field


@dataclass
class EvalResult:
    """单个 eval 用例的结果。"""
    passed: bool
    input: str
    expected: Any = None
    actual: Any = None
    error: str | None = None


@dataclass 
class EvalSuiteResult:
    """运行一个 eval 套件的结果。"""
    name: str
    passed: int = 0
    failed: int = 0
    results: list[EvalResult] = field(default_factory=list)
    
    @property
    def total(self) -> int:
        return self.passed + self.failed
    
    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0
    
    def add_result(self, result: EvalResult):
        """添加一个结果并更新计数。"""
        self.results.append(result)
        if result.passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def summary(self) -> str:
        """生成人类可读的摘要。"""
        status = "✓ PASSED" if self.failed == 0 else "✗ FAILED"
        return f"{self.name}: {status} ({self.passed}/{self.total})"


class AgentEval:
    """
    针对 Agent 能力的回归测试。

    用法:
        evaluator = AgentEval(agent)
        results = evaluator.test_structured_output(golden_cases)
        print(results.summary())
    """
    
    def __init__(self, agent):
        """
        用一个 Agent 实例初始化 evaluator。

        Args:
            agent: 待测试的 Agent 实例
        """
        self.agent = agent
    
    def test_structured_output(self, cases: list[dict]) -> EvalSuiteResult:
        """
        测试结构化输出能否正确解析并匹配 schema。

        这是一个 HARD 断言 —— JSON 必须始终有效。

        Args:
            cases: {"input": str, "schema": str, "must_have_fields": list[str]} 的列表

        Returns:
            包含通过/失败计数和详情的 EvalSuiteResult
        """
        suite = EvalSuiteResult(name="Structured Output")
        
        for case in cases:
            input_text = case["input"]
            schema = case["schema"]
            required_fields = case.get("must_have_fields", [])
            
            try:
                result = self.agent.generate_structured(input_text, schema)
                
                # 检查 1:是否得到了有效的 JSON?
                if result is None:
                    suite.add_result(EvalResult(
                        passed=False,
                        input=input_text,
                        expected="Valid JSON",
                        actual=None,
                        error="Failed to parse JSON after retries"
                    ))
                    continue
                
                # 检查 2:必填字段是否都存在?
                missing_fields = [f for f in required_fields if f not in result]
                if missing_fields:
                    suite.add_result(EvalResult(
                        passed=False,
                        input=input_text,
                        expected=f"Fields: {required_fields}",
                        actual=f"Missing: {missing_fields}",
                        error="Schema contract violated"
                    ))
                    continue
                
                # 通过所有检查
                suite.add_result(EvalResult(
                    passed=True,
                    input=input_text,
                    actual=result
                ))
                
            except Exception as e:
                suite.add_result(EvalResult(
                    passed=False,
                    input=input_text,
                    error=str(e)
                ))
        
        return suite
    
    def test_tool_calls(self, cases: list[dict]) -> EvalSuiteResult:
        """
        测试 tool call 准确性 —— 选对工具且参数有效。

        Args:
            cases: {"input": str, "expected_tool": str, "expected_args": dict(可选)} 的列表

        Returns:
            包含通过/失败计数的 EvalSuiteResult
        """
        suite = EvalSuiteResult(name="Tool Calls")
        
        for case in cases:
            input_text = case["input"]
            expected_tool = case["expected_tool"]
            expected_args = case.get("expected_args")
            
            try:
                tool_call = self.agent.request_tool(input_text)
                
                # 检查 1:是否得到了一个 tool call?
                if tool_call is None:
                    suite.add_result(EvalResult(
                        passed=False,
                        input=input_text,
                        expected=expected_tool,
                        actual=None,
                        error="No tool call generated"
                    ))
                    continue
                
                # 检查 2:是不是正确的工具?
                actual_tool = tool_call.get("tool")
                if actual_tool != expected_tool:
                    suite.add_result(EvalResult(
                        passed=False,
                        input=input_text,
                        expected=expected_tool,
                        actual=actual_tool,
                        error="Wrong tool selected"
                    ))
                    continue
                
                # 检查 3:参数是否有效?(如果指定了的话)
                if expected_args:
                    actual_args = tool_call.get("arguments", {})
                    for key, expected_val in expected_args.items():
                        if actual_args.get(key) != expected_val:
                            suite.add_result(EvalResult(
                                passed=False,
                                input=input_text,
                                expected=expected_args,
                                actual=actual_args,
                                error=f"Wrong argument: {key}"
                            ))
                            continue
                
                # 通过
                suite.add_result(EvalResult(
                    passed=True,
                    input=input_text,
                    expected=expected_tool,
                    actual=tool_call
                ))
                
            except Exception as e:
                suite.add_result(EvalResult(
                    passed=False,
                    input=input_text,
                    error=str(e)
                ))
        
        return suite
    
    def test_decisions(self, cases: list[dict]) -> EvalSuiteResult:
        """
        测试决策路由 —— Agent 从候选项中选出正确的动作。

        Args:
            cases: {"input": str, "choices": list[str], "expected": str} 的列表

        Returns:
            包含通过/失败计数的 EvalSuiteResult
        """
        suite = EvalSuiteResult(name="Decisions")
        
        for case in cases:
            input_text = case["input"]
            choices = case["choices"]
            expected = case["expected"]
            
            try:
                decision = self.agent.decide(input_text, choices)
                
                if decision is None:
                    suite.add_result(EvalResult(
                        passed=False,
                        input=input_text,
                        expected=expected,
                        actual=None,
                        error="No decision made"
                    ))
                elif decision != expected:
                    suite.add_result(EvalResult(
                        passed=False,
                        input=input_text,
                        expected=expected,
                        actual=decision,
                        error="Wrong decision"
                    ))
                else:
                    suite.add_result(EvalResult(
                        passed=True,
                        input=input_text,
                        expected=expected,
                        actual=decision
                    ))
                    
            except Exception as e:
                suite.add_result(EvalResult(
                    passed=False,
                    input=input_text,
                    error=str(e)
                ))
        
        return suite
    
    def test_memory_cycle(self, cases: list[dict]) -> EvalSuiteResult:
        """
        测试记忆的存储 → 检索循环。

        Args:
            cases: {"store_input": str, "query_input": str, "expected_in_response": str} 的列表

        Returns:
            包含通过/失败计数的 EvalSuiteResult
        """
        suite = EvalSuiteResult(name="Memory Cycle")
        
        for case in cases:
            store_input = case["store_input"]
            query_input = case["query_input"]
            expected_substring = case.get("expected_in_response", "")
            
            try:
                # 清空记忆以保证测试干净
                self.agent.memory.clear()
                
                # 步骤 1:存储
                store_response = self.agent.run_with_memory(store_input)
                if store_response is None:
                    suite.add_result(EvalResult(
                        passed=False,
                        input=store_input,
                        error="Failed to store to memory"
                    ))
                    continue
                
                # 步骤 2:查询
                query_response = self.agent.run_with_memory(query_input)
                if query_response is None:
                    suite.add_result(EvalResult(
                        passed=False,
                        input=query_input,
                        error="Failed to query memory"
                    ))
                    continue
                
                # 步骤 3:检查响应是否包含预期信息
                reply = query_response.get("reply", "")
                if expected_substring.lower() in reply.lower():
                    suite.add_result(EvalResult(
                        passed=True,
                        input=f"{store_input} → {query_input}",
                        expected=expected_substring,
                        actual=reply
                    ))
                else:
                    suite.add_result(EvalResult(
                        passed=False,
                        input=f"{store_input} → {query_input}",
                        expected=expected_substring,
                        actual=reply,
                        error="Expected content not in response"
                    ))
                    
            except Exception as e:
                suite.add_result(EvalResult(
                    passed=False,
                    input=store_input,
                    error=str(e)
                ))
        
        return suite
    
    def run_all(self, 
                structured_cases: list[dict] = None,
                tool_cases: list[dict] = None,
                decision_cases: list[dict] = None,
                memory_cases: list[dict] = None) -> list[EvalSuiteResult]:
        """
        运行所有 eval 套件。

        Args:
            structured_cases: 用于结构化输出测试的用例
            tool_cases: 用于 tool call 测试的用例
            decision_cases: 用于决策测试的用例
            memory_cases: 用于记忆测试的用例

        Returns:
            所有 EvalSuiteResult 的列表
        """
        results = []
        
        if structured_cases:
            results.append(self.test_structured_output(structured_cases))
        
        if tool_cases:
            results.append(self.test_tool_calls(tool_cases))
        
        if decision_cases:
            results.append(self.test_decisions(decision_cases))
        
        if memory_cases:
            results.append(self.test_memory_cycle(memory_cases))
        
        return results


def print_eval_report(results: list[EvalSuiteResult]):
    """
    打印格式化的 eval 报告。

    Args:
        results: 待报告的 EvalSuiteResult 列表
    """
    print("\n" + "="*50)
    print("EVAL REPORT")
    print("="*50)
    
    total_passed = 0
    total_failed = 0
    
    for suite in results:
        print(f"\n{suite.summary()}")
        
        # 显示失败项
        for result in suite.results:
            if not result.passed:
                print(f"  ✗ Input: {result.input[:50]}...")
                if result.expected:
                    print(f"    Expected: {result.expected}")
                if result.actual:
                    print(f"    Actual: {result.actual}")
                if result.error:
                    print(f"    Error: {result.error}")
        
        total_passed += suite.passed
        total_failed += suite.failed
    
    print("\n" + "-"*50)
    overall = "✓ ALL PASSED" if total_failed == 0 else f"✗ {total_failed} FAILED"
    print(f"Overall: {overall} ({total_passed}/{total_passed + total_failed})")
    print("="*50)
