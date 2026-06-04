"""pytest 共享配置。

提供 model_path fixture（session 级，全程复用）；模型文件缺失则跳过，避免误报为失败。
"""
import os

import pytest

from shared.config import MODEL_PATH


@pytest.fixture(scope="session")
def model_path():
    if not os.path.exists(MODEL_PATH):
        pytest.skip(f"模型文件不存在，跳过：{MODEL_PATH}")
    return MODEL_PATH
