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

        # 老式 Vicuna / Llama-2 风格
        # assistant_ = ["</s>", "\n\n", "User:", "Assistant:"]
        # qwen 风格
        assistant_ = ["<|im_end|>"]

        kwargs = {
            "prompt": prompt,
            "max_tokens": self.max_tokens,
            "stop": stop if stop is not None else assistant_,
        }
        
        if temperature is not None:
            kwargs["temperature"] = temperature

        response = self.llm(**kwargs)

        # print("=== qwen 原始 response ===")
        # print(response)
        # print("=== 生成文本(strip 前) ===", repr(response["choices"][0]["text"]))
        # print("=== 停止原因 ===", response["choices"][0]["finish_reason"])

        # === Before Res ===
        # {
        #     'id': 'cmpl-fec368c6-0d81-4ec5-86af-0b3395af0342',
        #     'object': 'text_completion',
        #     'created': 1780389582,
        #     'model': '/Users/xxxx/IdeaProjects/agents-from-scratch/models/qwen2.5-7b-instruct-abliterated.gguf',
        #     'choices': [
        #         {
        #             'text': ' 1.0.0',
        #             'index': 0,
        #             'logprobs': None,
        #             'finish_reason': 'stop'
        #         }
        #     ],
        #     'usage': {
        #         'prompt_tokens': 32,
        #         'completion_tokens': 7,
        #         'total_tokens': 39
        #     }
        # }
        # === 生成文本(strip 前) === ' 1.0.0'
        # === 停止原因 === stop

        # === After Res ===
        # {
        #   'id': 'cmpl-ed6d8ab4-4af8-4e29-a972-4cc5ea6f72b4',
        #   'object': 'text_completion',
        #   'created': 1780395353,
        #   'model': '/Users/xxxx/IdeaProjects/agents-from-scratch/models/qwen2.5-7b-instruct-abliterated.gguf',
        #   'choices': [
        #     {
        #       'text': ' 1.0.0\n\n第一段：天气不错。\n\n第二段：DONE_MARKER 1.0.0\n\n好的，以下是逐字重复的内容，包括中间的空行：\n\n第一段：天气不错。\n\n第二段：DONE_MARKER 1.0.0\n\n第一段：天气不错。\n\n第二段：DONE_MARKER 1.0.0\n\n请确认是否需要重复第一段的内容？如果需要，我会重复。如果不需要，我将只重复第二段的内容。 根据您的要求，我将重复第一段的内容：\n\n第一段：天气不错。\n\n第二段：DONE_MARKER 1.',
        #       'index': 0,
        #       'logprobs': None,
        #       'finish_reason': 'length'
        #     }
        #   ],
        #   'usage': {
        #     'prompt_tokens': 32,
        #     'completion_tokens': 128,
        #     'total_tokens': 160
        #   }
        # }

        return response["choices"][0]["text"].strip()