"""
Agent 遥测 —— 运行时可观测性。

遥测就是结构化日志,没有什么魔法。
它是你可以检查的数据,用来理解 Agent 做了什么。

本模块提供:
- 结构化 JSON 日志(而非 print 语句)
- 用于关联相关操作的 span 和 trace
- metric 聚合(延迟、成功率、重试次数)
"""

import json
import time
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, asdict, field
from typing import Any, Callable, Optional
from pathlib import Path


@dataclass
class Span:
    """
    一个 trace 中的单个操作。

    一个 span 捕获一个离散动作:一次 LLM 调用、一次工具执行、
    一次记忆操作等等。
    """
    span_id: str
    trace_id: str
    event_type: str
    timestamp: str
    duration_ms: Optional[float] = None
    data: Optional[dict] = None
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典,排除值为 None 的项。"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Metrics:
    """Agent 的聚合 metric。"""
    llm_calls: int = 0
    llm_failures: int = 0
    llm_retries: int = 0
    tool_calls: int = 0
    tool_failures: int = 0
    memory_operations: int = 0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    
    @property
    def avg_latency_ms(self) -> float:
        """LLM 调用的平均延迟。"""
        return self.total_latency_ms / self.llm_calls if self.llm_calls > 0 else 0.0
    
    @property
    def llm_success_rate(self) -> float:
        """LLM 调用成功率(0.0 到 1.0)。"""
        return 1 - (self.llm_failures / self.llm_calls) if self.llm_calls > 0 else 0.0
    
    @property
    def tool_success_rate(self) -> float:
        """tool call 成功率(0.0 到 1.0)。"""
        return 1 - (self.tool_failures / self.tool_calls) if self.tool_calls > 0 else 0.0
    
    def to_dict(self) -> dict:
        """将 metric 导出为字典。"""
        return {
            "llm_calls": self.llm_calls,
            "llm_failures": self.llm_failures,
            "llm_retries": self.llm_retries,
            "llm_success_rate": f"{self.llm_success_rate:.2%}",
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "tool_calls": self.tool_calls,
            "tool_failures": self.tool_failures,
            "tool_success_rate": f"{self.tool_success_rate:.2%}",
            "memory_operations": self.memory_operations,
        }


class Telemetry:
    """
    用于 Agent 可观测性的简易遥测。

    用法:
        telemetry = Telemetry()
        telemetry.start_trace()

        # 记录操作
        telemetry.log_llm_call(prompt, response, duration_ms)
        telemetry.log_tool_call(tool_name, args, result)

        # 查看 metric
        print(telemetry.get_metrics())
    """
    
    def __init__(self, log_file: str = "agent_telemetry.jsonl"):
        """
        初始化遥测。

        Args:
            log_file: JSONL 日志文件的路径(为 None 时禁用文件日志)
        """
        self.log_file = log_file
        self.current_trace_id: Optional[str] = None
        self.metrics = Metrics()
        self._spans: list[Span] = []  # 内存中的 span 缓冲区
    
    def start_trace(self) -> str:
        """
        开启一个新的 trace(一次完整的 Agent 交互)。

        Returns:
            trace ID
        """
        self.current_trace_id = str(uuid4())[:8]
        return self.current_trace_id
    
    def _log_span(self, span: Span):
        """将 span 写入日志文件和内存缓冲区。"""
        self._spans.append(span)
        
        if self.log_file:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(span.to_dict()) + "\n")
    
    def log_llm_call(self, 
                     prompt_length: int,
                     response_length: int,
                     duration_ms: float,
                     success: bool = True,
                     attempt: int = 1,
                     error: str = None):
        """
        记录一次 LLM 调用。

        Args:
            prompt_length: prompt 的字符长度
            response_length: 响应的字符长度
            duration_ms: 耗时(毫秒)
            success: 调用是否成功(JSON 是否解析成功等)
            attempt: 重试尝试次数(1 = 首次尝试)
            error: 失败时的错误信息
        """
        span = Span(
            span_id=str(uuid4())[:8],
            trace_id=self.current_trace_id or "no-trace",
            event_type="llm_call",
            timestamp=datetime.now().isoformat(),
            duration_ms=round(duration_ms, 2),
            data={
                "prompt_length": prompt_length,
                "response_length": response_length,
                "attempt": attempt,
                "success": success
            },
            error=error
        )
        
        self._log_span(span)

        # 更新 metric
        self.metrics.llm_calls += 1
        self.metrics.total_latency_ms += duration_ms
        if not success:
            self.metrics.llm_failures += 1
        if attempt > 1:
            self.metrics.llm_retries += 1
    
    def log_tool_call(self,
                      tool_name: str,
                      arguments: dict,
                      result: Any = None,
                      duration_ms: float = None,
                      error: str = None):
        """
        记录一次 tool call。

        Args:
            tool_name: 被调用工具的名称
            arguments: 传给工具的参数
            result: 工具执行的结果
            duration_ms: 耗时(毫秒)
            error: 失败时的错误信息
        """
        span = Span(
            span_id=str(uuid4())[:8],
            trace_id=self.current_trace_id or "no-trace",
            event_type="tool_call",
            timestamp=datetime.now().isoformat(),
            duration_ms=round(duration_ms, 2) if duration_ms else None,
            data={
                "tool": tool_name,
                "arguments": arguments,
                "result": str(result)[:200] if result else None  # 截断过长的结果
            },
            error=error
        )
        
        self._log_span(span)

        # 更新 metric
        self.metrics.tool_calls += 1
        if error:
            self.metrics.tool_failures += 1
    
    def log_memory_operation(self,
                             operation: str,
                             data: str = None):
        """
        记录一次记忆操作。

        Args:
            operation: 操作类型(add、get、clear)
            data: 涉及的数据(为存储而截断)
        """
        span = Span(
            span_id=str(uuid4())[:8],
            trace_id=self.current_trace_id or "no-trace",
            event_type="memory",
            timestamp=datetime.now().isoformat(),
            data={
                "operation": operation,
                "data": data[:100] if data else None  # 截断
            }
        )
        
        self._log_span(span)
        self.metrics.memory_operations += 1
    
    def log_decision(self,
                     choices: list[str],
                     selected: str,
                     duration_ms: float = None):
        """
        记录一次决策。

        Args:
            choices: 可选的候选项
            selected: 做出的选择
            duration_ms: 耗时(毫秒)
        """
        span = Span(
            span_id=str(uuid4())[:8],
            trace_id=self.current_trace_id or "no-trace",
            event_type="decision",
            timestamp=datetime.now().isoformat(),
            duration_ms=round(duration_ms, 2) if duration_ms else None,
            data={
                "choices": choices,
                "selected": selected
            }
        )
        
        self._log_span(span)
    
    def get_metrics(self) -> dict:
        """以字典形式获取聚合后的 metric。"""
        return self.metrics.to_dict()
    
    def get_recent_spans(self, n: int = 10) -> list[dict]:
        """
        获取最近的 n 个 span。

        Args:
            n: 要返回的 span 数量

        Returns:
            span 字典的列表
        """
        return [s.to_dict() for s in self._spans[-n:]]
    
    def get_trace_spans(self, trace_id: str) -> list[dict]:
        """
        获取某个特定 trace 的所有 span。

        Args:
            trace_id: 用于筛选的 trace ID

        Returns:
            该 trace 的 span 字典列表
        """
        return [s.to_dict() for s in self._spans if s.trace_id == trace_id]
    
    def clear(self):
        """清空所有 span 并重置 metric。"""
        self._spans = []
        self.metrics = Metrics()
        if self.log_file and Path(self.log_file).exists():
            Path(self.log_file).unlink()
    
    def print_summary(self):
        """打印人类可读的 metric 摘要。"""
        m = self.get_metrics()
        print("\n" + "="*40)
        print("TELEMETRY SUMMARY")
        print("="*40)
        print(f"LLM Calls:      {m['llm_calls']}")
        print(f"  Success Rate: {m['llm_success_rate']}")
        print(f"  Avg Latency:  {m['avg_latency_ms']}ms")
        print(f"  Retries:      {m['llm_retries']}")
        print(f"Tool Calls:     {m['tool_calls']}")
        print(f"  Success Rate: {m['tool_success_rate']}")
        print(f"Memory Ops:     {m['memory_operations']}")
        print("="*40)


def traced(telemetry: Telemetry, event_type: str):
    """
    为任意函数添加遥测的装饰器。

    用法:
        @traced(telemetry, "my_operation")
        def my_function():
            ...

    Args:
        telemetry: 用于记录日志的 Telemetry 实例
        event_type: 要记录的事件类型

    Returns:
        被装饰后的函数
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            start = time.time()
            error = None
            result = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                duration_ms = (time.time() - start) * 1000
                span = Span(
                    span_id=str(uuid4())[:8],
                    trace_id=telemetry.current_trace_id or "no-trace",
                    event_type=event_type,
                    timestamp=datetime.now().isoformat(),
                    duration_ms=round(duration_ms, 2),
                    data={"function": func.__name__},
                    error=error
                )
                telemetry._log_span(span)
        
        return wrapper
    return decorator
