"""练习 shared/llm.py:79 的 `response = self.llm(**kwargs)`，就两个语法点。

跑法：venv/bin/pytest shared/test_demo_kwargs.py
"""


def test_dict_unpack():
    """点 1：`**d` 把字典摊成关键字参数。f(**d) 和手写 f(a=1, b=2) 完全等价。"""
    def f(a, b):
        return a + b

    d = {"a": 1, "b": 2}
    assert f(**d) == f(a=1, b=2) == 3


def test_callable_object():
    """点 2：self.llm 是对象不是函数，却能加括号调用——因为它的类定义了 __call__。"""
    class FakeLLM:                       # 模拟 llama_cpp.Llama 实例
        def __call__(self, **kwargs):   # 有这个，实例才能像函数一样 llm(...)
            return {"choices": [{"text": kwargs["prompt"]}]}

    llm = FakeLLM()
    kwargs = {"prompt": "hi", "max_tokens": 512}
    response = llm(**kwargs)             # ← 你选中那行的结构：解包 + 调用可调用对象
    assert response["choices"][0]["text"] == "hi"
