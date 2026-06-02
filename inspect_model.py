"""看一眼本机模型（其实是 qwen2.5）自己声明的"结束符"。

用法：在 IDEA 里右键这个文件 → Run（普通运行就行，不用 pytest）。约 1 秒。
原理：GGUF 模型文件里记着它自己的特殊 token，llama_cpp 能直接读出来。
"""
import os

from llama_cpp import Llama

MODEL = os.path.join(os.path.dirname(__file__), "models", "llama-3-8b-instruct.gguf")

# vocab_only=True：只加载词表，不加载几 GB 权重，所以很快
llm = Llama(MODEL, vocab_only=True, verbose=False)

eos_id = llm.token_eos()                                          # 模型声明的"结束符"编号
eos_text = llm.detokenize([eos_id], special=True).decode("utf-8")  # 把编号翻译回字符串

print("=========================================")
print("本机模型的结束符（eos）：")
print("  编号 eos_token_id =", eos_id)
print("  对应字符串        =", repr(eos_text))   # ← 这就是证据：它是 <|im_end|>
print("=========================================")
print("所以默认 stop 该用它：[\"<|im_end|>\"]")
