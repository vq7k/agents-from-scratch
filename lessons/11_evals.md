# 第 11 课 - Evals(Agent 的回归测试)

## 我们要回答什么问题?

**「我改了某个东西之后,怎么知道我的 Agent 还能正常工作?」**

一旦你有了工具、记忆和结构化输出,改动一个 prompt 就变得有风险。一处措辞上的小改动就可能破坏 JSON 解析;一次「改进」可能让工具调用变得不那么可靠。没有评估(eval),质量会在无声中退化。

一个评估套件(eval suite)其实就是一个 Python 文件:它运行你的 Agent,并断言某些东西没有出问题。

## 你将构建什么

一个评估(evaluation)系统,它能够:
- 测试 prompt 与 JSON 解析的可靠性
- 校验工具调用的准确性
- 检查记忆的存储与检索环节
- 在部署前捕获回归(regression)

## 引入的新概念

### 1. 评估套件(Eval Suites)

**评估套件**是一组测试用例,用来校验 Agent 的行为。每个用例都有一个输入和一个预期结果。每次改动 prompt 后,你都要运行这个套件。

这并不神奇——无非是用已知输入运行你的 Agent,然后检查输出。

### 2. 黄金数据集(Golden Datasets)

**黄金数据集**是你的事实基准(source of truth)——一批已知良好、必须始终通过的样例。如果某个黄金用例失败了,那说明 Agent 坏了(而不是测试坏了)。

黄金数据集与你的 prompt 一同纳入版本控制。当你改动 prompt 时,就运行黄金数据集,以验证没有任何东西被破坏。

### 3. 硬断言 vs 软断言(Hard vs Soft Assertions)

**硬断言**必须始终通过:
- JSON 必须有效
- 必需字段必须存在
- 工具名称必须与可用工具匹配

**软断言**通常应当通过:
- 答案在语义上是正确的
- 措辞是恰当的
- 工具参数是最优的

先从硬断言开始,之后再加入软断言。

## 为什么这在真实世界里会失败

一处改进了措辞的 prompt 改动,可能会:
- 让输出变得更啰嗦
- 把 JSON 挤出上下文窗口(context window)
- 破坏解析
- ……而这一切都没有改变答案的正确性

这正是评估存在的意义。它们能捕获这些无声的失败。

## 我们(暂时)不做什么

- 不做运行时监控([第 12 课](12_telemetry.md))
- 不做 A/B 测试
- 不做生产环境可观测性(observability)
- 不做 LLM-as-judge 式评估(目前太复杂)

## 代码

查看 `agent/evals.py`:

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvalResult:
    """单个评估用例的结果。"""
    passed: bool
    input: str
    expected: Any = None
    actual: Any = None
    error: str | None = None


@dataclass 
class EvalSuiteResult:
    """运行一个评估套件的结果。"""
    name: str
    passed: int = 0
    failed: int = 0
    results: list[EvalResult] = field(default_factory=list)
    
    @property
    def pass_rate(self) -> float:
        return self.passed / (self.passed + self.failed) if (self.passed + self.failed) > 0 else 0.0
    
    def summary(self) -> str:
        status = "✓ PASSED" if self.failed == 0 else "✗ FAILED"
        return f"{self.name}: {status} ({self.passed}/{self.passed + self.failed})"


class AgentEval:
    """针对 Agent 能力的回归测试。"""
    
    def __init__(self, agent):
        self.agent = agent
    
    def test_structured_output(self, cases: list[dict]) -> EvalSuiteResult:
        """测试结构化输出能否正确解析并符合 schema。"""
        suite = EvalSuiteResult(name="Structured Output")
        
        for case in cases:
            result = self.agent.generate_structured(case["input"], case["schema"])
            
            # 检查 1:我们拿到有效的 JSON 了吗?
            if result is None:
                suite.add_result(EvalResult(
                    passed=False,
                    input=case["input"],
                    error="Failed to parse JSON"
                ))
                continue
            
            # 检查 2:必需字段都在吗?
            missing = [f for f in case.get("must_have_fields", []) if f not in result]
            if missing:
                suite.add_result(EvalResult(
                    passed=False,
                    input=case["input"],
                    error=f"Missing fields: {missing}"
                ))
                continue
            
            suite.add_result(EvalResult(passed=True, input=case["input"], actual=result))
        
        return suite
```

注意:
- **纯 Python** —— 不需要任何测试框架
- **结构化结果** —— 每条结果都记录了输入、预期、实际、错误
- **可组合** —— 既能运行单个套件,也能运行多个
- **可操作** —— 失败时会准确告诉你哪里出了问题

## 黄金数据集

查看 `evals/golden_datasets.py`:

```python
STRUCTURED_OUTPUT_GOLDEN = [
    {
        "input": "Explain quantum computing in one sentence",
        "schema": """{
  "topic": "the topic name as a string",
  "difficulty": "beginner" or "intermediate" or "advanced"
}

Example: {"topic": "machine learning", "difficulty": "intermediate"}""",
        "must_have_fields": ["topic", "difficulty"]
    },
]

TOOL_CALL_GOLDEN = [
    {
        "input": "What is 42 * 7?",
        "expected_tool": "calculator",
        "expected_args": {"operation": "multiply"}
    },
]

MEMORY_GOLDEN = [
    {
        "store_input": "My name is Alice",
        "query_input": "What's my name?",
        "expected_in_response": "Alice"
    },
]
```

注意:
- **带示例的多行 schema** —— 单行 schema 常常会让模型困惑
- **纳入版本控制** —— 它们存放在你的仓库里
- **覆盖边界情况** —— 特殊字符、数字等
- **具体的断言** —— 不是「它能工作」,而是「这个字段存在」

## 如何运行

查看 `complete_example.py` 中的 `lesson_11_evals()` 方法:

```python
from agent.agent import Agent
from agent.evals import AgentEval, print_eval_report
from evals.golden_datasets import (
    STRUCTURED_OUTPUT_GOLDEN,
    TOOL_CALL_GOLDEN,
    MEMORY_GOLDEN
)

agent = Agent("models/qwen2.5-7b-instruct-abliterated.gguf")
evaluator = AgentEval(agent)

# 运行全部评估
results = evaluator.run_all(
    structured_cases=STRUCTURED_OUTPUT_GOLDEN,
    tool_cases=TOOL_CALL_GOLDEN,
    memory_cases=MEMORY_GOLDEN
)

# 打印报告
print_eval_report(results)
```

输出示例:

```
==================================================
EVAL REPORT
==================================================

Structured Output: ✓ PASSED (4/4)
Tool Calls: ✓ PASSED (5/5)
Memory Cycle: ✓ PASSED (3/3)

--------------------------------------------------
Overall: ✓ ALL PASSED (12/12)
==================================================
```

或者当有东西出问题时:

```
==================================================
EVAL REPORT
==================================================

Structured Output: ✗ FAILED (3/4)
  ✗ Input: What does 'hello world' mean in progra...
    Expected: Fields: ['explanation']
    Actual: Missing: ['explanation']
    Error: Schema contract violated

--------------------------------------------------
Overall: ✗ 1 FAILED (11/12)
==================================================
```

## 应该测试什么

| 组件 | 评估什么 | 断言示例 |
| --------- | ------------ | ----------------- |
| 结构化输出 | JSON 有效性 + schema 契约 | `parse_json(output) is not None and matches schema` |
| 决策 | 路由是否正确 | `decision in valid_choices` |
| 工具调用 | 工具是否正确 + 参数是否正确 | `tool_call["tool"] == "calculator"` |
| 记忆 | 存储/检索环节 | `agent.memory.get_all()` 包含已保存的事实 |

## 与第 03 课的对比

**第 03 课(结构化输出):**
- 生成时的一次性校验
- JSON 失败则重试
- 没有历史记录

**第 11 课(评估):**
- 跨多个用例的系统化测试
- 随时间追踪成功率
- 在部署前捕获回归

## 关键洞见

### 评估不过就是断言

这里没有魔法。你运行 Agent、检查输出、报告通过/失败。其威力在于系统化地去做这件事。

### 黄金数据集就是你的契约

当有人问「这个 Agent 能用吗?」时,你就指向黄金数据集。100% 通过率 = 能用;低于此 = 有具体的失败需要修复。

### 每次改动前都跑一遍评估

工作流程:
1. 改动 prompt
2. 运行评估
3. 若有失败,修复或回退
4. 提交

这就是你防止质量退化的方法。

### 从简单开始

你不需要 1000 个测试用例。每项能力先从 5-10 个黄金用例开始。等你在生产中发现边界情况时再逐步增加。

## 常见问题

**「评估太慢了」**
- 跑一个更小的子集做快速检查
- 在提交前跑完整套件
- 考虑缓存模型加载

**「软断言不稳定(flaky)」**
- 一开始只用硬断言
- 等你有足够数据后再加入软断言
- 在语义匹配之前,先考虑精确匹配

**「我不知道该测什么」**
- 从「顺利路径(happy path)」开始
- 加入那些在生产中出过问题的用例
- 覆盖边界情况(空输入、特殊字符等)

## 练习

1. 添加一个当前会失败的新黄金用例,然后修复 prompt
2. 故意破坏一个 prompt,验证评估能否捕获到这次回归
3. 添加一个边界情况(空输入、超长输入、unicode)
4. 为规划(第 08 课)创建黄金数据集

## 接下来是什么?

在[第 12 课](12_telemetry.md)中,我们将加入**遥测(telemetry)**——理解你的 Agent 在运行时(而不仅仅是在测试中)正在做什么。

---

**核心要点:** 评估 = 系统化测试。黄金数据集 = 你的契约。每次改动 prompt 之前都跑一遍。
