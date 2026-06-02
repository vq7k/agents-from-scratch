"""
LocalLLM —— 对 llama-cpp-python 的简单封装。

本类提供了与本地语言模型交互的极简接口。
它刻意不包含任何魔法:
- 没有重试(在第 03 课加入)
- 没有 tool calling(在第 05 课加入)
- 没有记忆(在第 07 课加入)

只是文本进、文本出。
"""

from shared.llama_logging import disable_llama_logging
from llama_cpp import Llama

disable_llama_logging()

class LocalLLM:
    """
    使用 llama.cpp 进行本地 LLM 推理的极简封装。

    本类刻意保持简单,会在各节课中逐步扩展。
    """

    def __init__(
        self,
        model_path: str,
        temperature: float = 0.2,
        max_tokens: int = 512,
        n_ctx: int = 2048,
        n_gpu_layers: int = -1,
    ):
        """
        初始化本地 LLM。

        Args:
            model_path: GGUF 模型文件的路径
            temperature: 采样温度(0.0 = 确定性,1.0 = 有创造性)
            max_tokens: 每次响应生成的最大 token 数
            n_ctx: 上下文窗口大小
            n_gpu_layers: 卸载到 GPU 的层数(-1 = 全部,0 = 纯 CPU)。
                Apple Silicon 上默认 -1 即启用 Metal GPU 加速。
        """
        self.llm = Llama(
            model_path=model_path,
            temperature=temperature,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,  # -1：全部层用 GPU（Apple Silicon 上即 Metal 加速）
            verbose=False,
        )
        self.max_tokens = max_tokens
    
    def generate(self, prompt: str, temperature: float = None, stop: list[str] = None) -> str:
        """
        根据 prompt 生成文本。

        Args:
            prompt: 输入的文本 prompt
            temperature: 可选的温度覆盖值
            stop: 可选的停止序列列表

        Returns:
            生成的文本字符串
        """
        kwargs = {
            "prompt": prompt,
            "max_tokens": self.max_tokens,
            # FIXME（qwen 适配 · 必改）：这组 stop 是老式 Vicuna / Llama-2 风格，但本机模型其实是 qwen2.5（ChatML）。
            #   · "</s>" 是 Llama-2 的结束符，对 qwen 完全无效（qwen 的结束符是 <|im_end|>）；
            #   · "\n\n" 会误伤：qwen 回答里一出现空行就被提前截断。
            #   用 qwen 时改成 → "stop": stop if stop is not None else ["<|im_end|>"]
            "stop": stop if stop is not None else ["</s>", "\n\n", "User:", "Assistant:"],
        }
        
        if temperature is not None:
            kwargs["temperature"] = temperature
        
        # FIXME（qwen 适配 · 进阶/可选）：这里用 raw completion（__call__），不套任何对话模板。
        #   更彻底的做法是 self.llm.create_chat_completion(messages=[{"role": ..., "content": ...}])，
        #   它会自动读 GGUF 内置的 ChatML 模板 + 用正确 eos，换任何模型都不必再手改 stop。
        #   代价：generate() 入参要从「prompt 字符串」改成「messages 列表」，牵连所有调用方。
        #   教学版保留 raw 是有意为之（看清裸机制），知道有这条路即可。
        response = self.llm(**kwargs)
        return response["choices"][0]["text"].strip()