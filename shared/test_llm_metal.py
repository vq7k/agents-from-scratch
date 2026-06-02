"""shared/llm.py · Metal 验证（pytest）。对应答疑 Q2：n_gpu_layers=-1 是否真走 Metal。

跑法：venv/bin/pytest shared/test_llm_metal.py
"""
import logging
import time

from shared.llm import LocalLLM

logger = logging.getLogger(__name__)


def _speed(model_path, n_gpu):
    llm = LocalLLM(model_path, max_tokens=64, n_gpu_layers=n_gpu)
    t = time.time()
    out = llm.llm("用一句话解释什么是 AI Agent。", max_tokens=64, stop=["<|im_end|>"])
    dt = time.time() - t
    return out["usage"]["completion_tokens"] / dt


def test_metal_faster_than_cpu(model_path):
    """Metal（n_gpu_layers=-1）应快于纯 CPU（n_gpu_layers=0）。"""
    gpu = _speed(model_path, -1)
    cpu = _speed(model_path, 0)
    logger.info("Metal %.1f tok/s  vs  CPU %.1f tok/s  (%.1fx)", gpu, cpu, gpu / cpu)
    assert gpu > cpu, f"Metal({gpu:.1f}) 应快于 CPU({cpu:.1f})——Metal 可能没生效"
