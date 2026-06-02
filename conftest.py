"""pytest 共享配置。

提供 model_path fixture（session 级，全程复用）；模型文件缺失则跳过，避免误报为失败。
"""
import os

import pytest

ROOT = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="session")
def model_path():
    p = os.path.join(ROOT, "models", "llama-3-8b-instruct.gguf")
    if not os.path.exists(p):
        pytest.skip(f"模型文件不存在，跳过：{p}")
    return p
