# 第 12 课 - 遥测(运行时可观测性)

## 我们要回答什么问题?

**「我的 Agent 在运行时到底在做什么?」**

评估(eval)告诉你 Agent 在部署前能否工作;遥测(telemetry)告诉你部署期间正在发生什么。没有遥测,调试就是靠猜。

## 你将构建什么

一个遥测系统,它能够:
- 记录每一次 LLM 调用的输入与输出
- 追踪工具调用的成功/失败率
- 测量延迟(latency)与重试次数
- 借助追踪(trace)实现事后调试

## 引入的新概念

### 1. 结构化日志(Structured Logging)

**结构化日志**指的是 JSON 日志,而非 print 语句。每条日志条目都有一致的 schema:时间戳、事件类型、数据、错误。

```json
{"event_type": "llm_call", "timestamp": "2024-01-15T10:30:00", "duration_ms": 1523, "success": true}
```

这是可搜索、可解析、机器可读的。

### 2. Span 与 Trace

一个 **span** 是一次操作——单次 LLM 调用、一次工具执行、一次记忆访问。

一个 **trace** 是一次完整的 Agent 交互——由一个 trace ID 串联起来的多个 span。

当某处失败时,你找到对应的 trace,就能逐步看清究竟发生了什么。

### 3. 指标(Metrics)

**指标**是聚合后的数字:
- `llm_success_rate` —— JSON 正确解析的频率有多高?
- `avg_latency_ms` —— LLM 调用耗时多久?
- `tool_failure_rate` —— 工具调用失败的频率有多高?

指标让你一眼看出 Agent 的健康状况。

## 我们(暂时)不做什么

- 不做分布式追踪(仅限单机)
- 不做生产环境仪表盘(基于文件的日志)
- 不做告警(人工检查)
- 不用 OpenTelemetry(保持简单)

## 代码

查看 `agent/telemetry.py`:

```python
import json
import time
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Span:
    """一个 trace 中的单次操作。"""
    span_id: str
    trace_id: str
    event_type: str
    timestamp: str
    duration_ms: Optional[float] = None
    data: Optional[dict] = None
    error: Optional[str] = None


@dataclass
class Metrics:
    """Agent 的聚合指标。"""
    llm_calls: int = 0
    llm_failures: int = 0
    llm_retries: int = 0
    tool_calls: int = 0
    tool_failures: int = 0
    total_latency_ms: float = 0.0
    
    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.llm_calls if self.llm_calls > 0 else 0.0
    
    @property
    def llm_success_rate(self) -> float:
        return 1 - (self.llm_failures / self.llm_calls) if self.llm_calls > 0 else 0.0


class Telemetry:
    """面向 Agent 可观测性的简易遥测。"""
    
    def __init__(self, log_file: str = "agent_telemetry.jsonl"):
        self.log_file = log_file
        self.current_trace_id = None
        self.metrics = Metrics()
    
    def start_trace(self) -> str:
        """开启一个新的 trace(一次完整的 Agent 交互)。"""
        self.current_trace_id = str(uuid4())[:8]
        return self.current_trace_id
    
    def log_llm_call(self, prompt_length: int, response_length: int, 
                     duration_ms: float, success: bool = True, error: str = None):
        """记录一次 LLM 调用。"""
        span = Span(
            span_id=str(uuid4())[:8],
            trace_id=self.current_trace_id or "no-trace",
            event_type="llm_call",
            timestamp=datetime.now().isoformat(),
            duration_ms=round(duration_ms, 2),
            data={"prompt_length": prompt_length, "response_length": response_length},
            error=error
        )
        
        # 写入日志文件
        with open(self.log_file, "a") as f:
            f.write(json.dumps(asdict(span)) + "\n")
        
        # 更新指标
        self.metrics.llm_calls += 1
        self.metrics.total_latency_ms += duration_ms
        if not success:
            self.metrics.llm_failures += 1
```

注意:
- **dataclass** —— 干净、带类型的结构
- **JSONL 格式** —— 每行一个 JSON 对象,易于解析
- **指标累加** —— 边运行边追踪聚合值
- **trace 串联** —— 所有 span 共享同一个 trace ID

## 如何运行

查看 `complete_example.py` 中的 `lesson_12_telemetry()` 方法:

```python
from agent.agent import Agent
from agent.telemetry import Telemetry

agent = Agent("models/llama-3-8b-instruct.gguf")
telemetry = Telemetry()

# 开启一个 trace
trace_id = telemetry.start_trace()
print(f"Trace ID: {trace_id}")

# 模拟若干操作(实际使用中,这些来自被插桩的 Agent)
import time

start = time.time()
result = agent.generate_structured("What is Python?", '{"answer": string}')
duration = (time.time() - start) * 1000

telemetry.log_llm_call(
    prompt_length=100,
    response_length=len(str(result)),
    duration_ms=duration,
    success=result is not None
)

# 查看指标
telemetry.print_summary()
```

输出示例:

```
========================================
TELEMETRY SUMMARY
========================================
LLM Calls:      3
  Success Rate: 100.00%
  Avg Latency:  1245ms
  Retries:      0
Tool Calls:     2
  Success Rate: 100.00%
Memory Ops:     1
========================================
```

## 查看日志文件

遥测会记录到 `agent_telemetry.jsonl`:

```jsonl
{"span_id": "a1b2c3d4", "trace_id": "x9y8z7w6", "event_type": "llm_call", "timestamp": "2024-01-15T10:30:00.123456", "duration_ms": 1523.45, "data": {"prompt_length": 256, "response_length": 89, "success": true}}
{"span_id": "e5f6g7h8", "trace_id": "x9y8z7w6", "event_type": "tool_call", "timestamp": "2024-01-15T10:30:02.456789", "duration_ms": 5.23, "data": {"tool": "calculator", "arguments": {"a": 42, "b": 7, "operation": "multiply"}}}
```

要调试某次具体交互,按 trace_id 过滤:
```bash
grep "x9y8z7w6" agent_telemetry.jsonl
```

## 应该记录什么

| 事件 | 要捕获的数据 | 为什么 |
|-------|-----------------|-----|
| LLM 调用 | prompt_length、response_length、duration_ms、success | 追踪延迟,识别慢/失败的调用 |
| 工具请求 | tool_name、arguments | 调试错误的工具选择 |
| 工具执行 | tool_name、result、error | 调试工具失败 |
| 记忆操作 | operation、data | 追踪正在被存储/检索的内容 |
| 决策 | choices、selected | 调试路由问题 |

## 与第 11 课的对比

**第 11 课(评估):**
- 在部署前运行
- 已知输入、预期输出
- 二元的通过/失败
- 捕获回归

**第 12 课(遥测):**
- 在部署期间运行
- 未知输入、观测到的输出
- 持续监控
- 支持调试

两者互补。评估阻止糟糕的代码上线;遥测帮你理解已上线的代码正在做什么。

## 关键洞见

### 遥测不过就是结构化日志

没有魔法。你只是在往文件里写 JSON。其威力在于:
- 一致的 schema
- 串联相关事件的 trace ID
- 聚合后的指标

### Trace 是你调试的超能力

当某个用户报告「这个 Agent 给了个奇怪的答案」时,你可以:
1. 拿到 trace ID
2. 找到该 trace 的所有 span
3. 看清究竟发生了什么

没有 trace,你只能靠猜。

### 指标告诉你系统健康状况

瞥一眼指标,就能知道是否有东西出了问题:
- 成功率在下降?检查 prompt 是否有问题
- 延迟在上升?检查模型/硬件
- 重试在增加?检查 JSON 解析

### 从简单开始,之后再加码

这个实现把日志记录到文件,作为起点已经够用。之后你可能会加入:
- 数据库存储
- 实时仪表盘
- 基于阈值的告警

但请从一个文件开始。

## 常见问题

**「日志文件太大了」**
- 滚动日志(每天/每小时一个新文件)
- 生产环境中只记录失败
- 截断过长的数据字段

**「我找不到需要的那个 trace」**
- 在面向用户的错误信息中加入 trace ID
- 在你的应用日志里记录 trace ID
- 考虑给 trace 加上用户 ID

**「遥测拖慢了我的 Agent」**
- 异步记录日志(先缓冲,再写入)
- 减少每个 span 捕获的数据量
- 采样记录,而非全量记录

## 练习

1. 给 agent loop 加上遥测,追踪一次完整的多步交互
2. 统计 20 次结构化输出调用的 JSON 解析成功率
3. 对比不同 prompt 长度之间的延迟
4. 在日志中找出一个失败的 span,调试究竟哪里出了问题

## 接下来是什么?

恭喜!你已经完成了核心课程。

你现在拥有一个具备以下能力的 Agent:
- 结构化输出(第 03 课)
- 决策(第 04 课)
- 工具调用(第 05 课)
- agent loop(第 06 课)
- 记忆(第 07 课)
- 规划(第 08 课)
- 原子动作(第 09 课)
- 依赖图(第 10 课)
- 回归测试(第 11 课)
- 运行时可观测性(第 12 课)

这是一个完整、可观测、可测试的 Agent,从第一性原理(first principles)一步步构建而成。

---

**核心要点:** 遥测 = 结构化日志 + trace + 指标。它把「有东西出问题了」变成「这里就是确切发生的事」。
