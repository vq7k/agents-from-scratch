"""agent/agent.py · 真实调用链（pytest）。对应答疑「真实调用链」验证。

跑法：venv/bin/pytest agent/test_agent.py
"""
import logging

from agent.agent import Agent

logger = logging.getLogger(__name__)


def test_agent_generate_chain(model_path):
    """Agent → LocalLLM.generate()：simple_generate / generate_with_role 都应返回非空文本。"""
    agent = Agent(model_path)
    r1 = agent.simple_generate("用一句话解释什么是 AI Agent。")
    r2 = agent.generate_with_role("用一句话解释什么是大语言模型。")
    logger.info("simple_generate: %r", r1)
    logger.info("generate_with_role: %r", r2)
    assert r1.strip(), "simple_generate 应返回非空"
    assert r2.strip(), "generate_with_role 应返回非空"
