"""shared/llm.py:68 · stop 适配（pytest · TDD bug 复现）。对应答疑 Q10。

默认 stop 含 "\\n\\n"，会把 qwen 的多段回答在第一个空行处截断、丢掉后文。
  · 现在跑：本用例【失败 / 红】——DONE_MARKER 被截掉。
  · 把 shared/llm.py:68 的默认 stop 改成 ["<|im_end|>"] 后再跑：【通过 / 绿】。

跑法：venv/bin/pytest shared/test_llm_stop.py
"""
import logging

from shared.llm import LocalLLM

logger = logging.getLogger(__name__)

# 强制两段之间有空行（\n\n），关键标记 DONE_MARKER 放在第二段（即 \n\n 之后）
PROMPT = (
    "请逐字重复下面的内容（包括中间的空行），不要添加任何解释或前缀：\n\n"
    "第一段：天气不错。\n\n第二段：DONE_MARKER"
)


def test_default_stop_should_not_truncate(model_path):
    """默认 stop 的 \\n\\n 会截断第二段、丢掉 DONE_MARKER → 修复 stop 前本用例应 FAIL。"""
    llm = LocalLLM(model_path, max_tokens=128, temperature=0.0)
    out = llm.generate(PROMPT)  # 用 generate() 的默认 stop
    logger.info("默认 stop 输出: %r", out)
    assert "DONE_MARKER" in out, (
        f'默认 stop 的 "\\n\\n" 截断了输出，只剩 {out!r}，第二段的 DONE_MARKER 丢失。'
        ' 修复：把 shared/llm.py:68 的默认 stop 改成 ["<|im_end|>"]。'
    )
