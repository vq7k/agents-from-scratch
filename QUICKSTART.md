# 快速开始(Quick Start)指南

10 分钟跑通「从零构建 AI Agent」。

## 前置条件

- Python 3.10 或更高版本
- 8GB 以上内存(用于运行本地模型)
- 约 5-10GB 可用磁盘空间(用于模型文件)

## 第 1 步:安装依赖

```bash
pip install llama-cpp-python
```

**可选但推荐:**
```bash
# 先创建一个虚拟环境
python -m venv venv
source venv/bin/activate  # Windows 上为:venv\Scripts\activate
pip install llama-cpp-python
```

## 第 2 步:下载模型

你需要一个 GGUF 模型文件。最简单的做法如下:

1. 打开 https://huggingface.co/bartowski/Meta-Llama-3-8B-Instruct-GGUF
2. 下载 `Meta-Llama-3-8B-Instruct-Q4_K_M.gguf`(约 5GB)
3. 把它放到 `models/` 目录下
4. 将其重命名为 `llama-3-8b-instruct.gguf`(可选,为了简化）

**可选的其他模型:**
- Mistral 7B:https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.2-GGUF
- Gemma 7B:https://huggingface.co/bartowski/gemma-7b-it-GGUF

## 第 3 步:验证环境

```bash
python setup_check.py
```

这会检查:
- Python 版本
- 依赖
- models 目录
- 仓库结构

## 第 4 步:运行示例

```bash
python complete_example.py
```

这会运行全部 10 节课的示例。你也可以打开 `complete_example.py`,修改模型路径,或注释掉想跳过的课程。

## 第 6 步:开始学习

现在按顺序阅读各节课:

1. `lessons/01_basic_llm_chat.md` —— 理解基础
2. `lessons/02_system_prompt.md` —— 加入行为
3. `lessons/03_structured_output.md` —— 让它变得可靠
4. …… 依此类推,一直到第 10 课

每节课都建立在上一节之上。

## 故障排查

### 「Module 'llama_cpp' not found」

```bash
pip install llama-cpp-python
```

### 「Model file not found」

请检查:
1. 模型文件是否在 `models/` 目录下
2. `complete_example.py` 中的路径是否与实际文件名一致
3. 文件是否带有 `.gguf` 扩展名

### 「Out of memory」错误

试试更小的模型或更低的量化精度:
- Q4_K_M:约 5GB 内存
- Q5_K_M:约 6GB 内存  
- Q8_0:约 8GB 内存

### 响应缓慢

对 CPU 推理来说这是正常现象。每次响应需要 10-30 秒,具体取决于:
- 你的 CPU 速度
- 模型大小
- 响应长度

## 后续步骤

- **阅读 philosophy.md**,理解本项目的方法论
- **逐节学习课程**,一次一节
- **修改这个 Agent** 来做实验
- **查看 examples/**,获取完整的代码示例

## 获取帮助

- 查阅已有的 [GitHub Issues](https://github.com/your-repo/issues)
- 仔细阅读各课的 markdown 文件
- 在 [GitHub Discussions](https://github.com/your-repo/discussions) 中提问

## 成功的小贴士

1. **不要跳课** —— 它们彼此层层递进
2. **运行代码** —— 只读是不够的
3. **动手实验** —— 修改示例,看看会发生什么
4. **保持耐心** —— 本地推理很慢,但值得
5. **阅读注释** —— 代码里的注释解释了「为什么」

学习愉快! 🚀