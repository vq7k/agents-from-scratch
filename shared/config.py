"""项目级共享配置：模型路径的单一真相源。

历史遗留：模型文件曾名为 llama-3-8b-instruct.gguf，但其内容实际是
Qwen2.5-7B-Instruct（abliterated 去审查版，general.name = "Qwen2.5 7B
Instruct Abliterated"），现已正名。所有代码统一从这里取模型路径，
换模型只需改这一处。
"""
import os

# 仓库根目录（本文件位于 <root>/shared/config.py）
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 模型文件名
MODEL_FILE = "qwen2.5-7b-instruct-abliterated.gguf"

# 绝对路径：从任意工作目录运行都可用
MODEL_PATH = os.path.join(ROOT, "models", MODEL_FILE)
