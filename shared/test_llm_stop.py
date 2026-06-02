"""shared/llm.py:68 · stop 适配（pytest · TDD bug 复现）。对应答疑 Q10。

【这个测试在验证什么】
  本机模型其实是 qwen2.5（ChatML 系，回合结束符是 <|im_end|>），
  但 shared/llm.py:68 的默认 stop 还是老式 Vicuna 风格：["</s>", "\\n\\n", "User:", "Assistant:"]。
  其中的 "\\n\\n" 会惹祸——只要模型回答里出现一个空行，generate() 就在那里硬停，
  把空行后面的内容全丢掉。这就是要复现的 bug。

【本测试的思路】
  让模型输出“两段、中间空一行”的内容，把检测标记 DONE_MARKER 放在第二段（空行之后）：
    · 默认 stop 含 "\\n\\n" → 撞上中间那个空行就停 → 只剩第一段 → DONE_MARKER 丢失 → 断言失败（红）
    · 把 stop 改成 ["<|im_end|>"] → 不在空行停 → 完整输出 → DONE_MARKER 还在 → 断言通过（绿）

【现在跑是红的，这是对的】（TDD：先有一个会失败的测试，再去改代码让它变绿）
  改 shared/llm.py:68 的默认 stop 为 ["<|im_end|>"] 后重跑 → 转绿。

跑法：venv/bin/pytest shared/test_llm_stop.py
"""
import logging

from shared.llm import LocalLLM

logger = logging.getLogger(__name__)

# 这个 prompt 故意制造“两段 + 中间空行”的输出，并把检测标记放在第二段。
# 关键是下面那个 "\n\n"（空行）：它诱导模型在输出里也产生空行，
# 从而触发默认 stop 的 "\n\n" 截断；DONE_MARKER 在第二段，被截掉就检测得到。
PROMPT = (
    "请逐字重复下面的内容（包括中间的空行），不要添加任何解释或前缀：\n\n"
    "第一段：天气不错。\n\n第二段：DONE_MARKER"
)


def test_default_stop_should_not_truncate(model_path):
    """一句话：完整回答里本应含 DONE_MARKER；被 \\n\\n 截断就会缺它 → 修复 stop 前应 FAIL。"""
    # temperature=0：贪婪解码，让输出尽量稳定、可复现
    llm = LocalLLM(model_path, max_tokens=128, temperature=0.0)

    # generate() 不传 stop，就用 shared/llm.py:68 的“默认 stop”（当前含 "\n\n"）——正是要考验的对象
    out = llm.generate(PROMPT)
    logger.info("默认 stop 输出: %r", out)

    # 核心断言：DONE_MARKER（第二段的标记）应当出现在输出里。
    #   · 修复前：实测模型先吐 "1.0.0" + 一个空行，默认 stop 撞上空行就停，
    #            out 只剩 "1.0.0"、不含 DONE_MARKER → 失败（这就是你在 IDEA 看到的 'DONE_MARKER' not in '1.0.0'）。
    #   · 修复后（stop=["<|im_end|>"]）：模型完整输出，DONE_MARKER 在 → 通过。
    assert "DONE_MARKER" in out, (
        f'默认 stop 的 "\\n\\n" 截断了输出，只剩 {out!r}，第二段的 DONE_MARKER 丢失。'
        ' 修复：把 shared/llm.py:68 的默认 stop 改成 ["<|im_end|>"]。'
    )
