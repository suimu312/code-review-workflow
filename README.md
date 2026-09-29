# Code Review Workflow · 多Agent协作工作流

一个由 **3 个 Agent 协作完成**代码开发 + 审查 + 修复的 Simple Workflow MVP。
承接项目1（Code Review Agent），将单个 Agent 升级为多 Agent 协作流水线。

**代码仓库**：[https://github.com/suimu312/code-review-workflow](https://github.com/suimu312/code-review-workflow)

## 功能特性

- **3 个 Agent 协作**：编码Agent → 审查Agent → 修复Agent，接力完成"需求→代码→审查→修复"完整流程
- **消息传递与状态共享**：所有 Agent 通过共享的 `WorkflowContext` 传递数据
- **高级流程控制**：顺序执行、条件分支（有 Bug 才修复）、并行执行（审查阶段并行跑规则检查+LLM审查）、循环自检（修复Agent 内部循环）
- **可视化编排界面**：Web 界面实时展示节点状态流转 + 执行日志（SSE 实时推送）
- **执行日志与状态追踪**：完整记录每个节点执行状态
- **错误处理与恢复**：节点失败自动重试一次，失败不拖垮整个流程
- **复用项目1**：LLM 客户端、对话记忆直接复用于项目1

## 两种运行方式

### 方式 A：可视化界面（推荐）

```bash
pip install -r requirements.txt
python webapp.py
```

浏览器打开 **http://127.0.0.1:5000**，输入需求点"运行工作流"，
即可看到三个 Agent 的节点状态实时流转和日志。

### 方式 B：命令行

```bash
python main.py
```

## 快速开始

### 1. 安装依赖

```bash
pip install openai flask
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key（同项目1）
```

### 3. 运行（任选一种方式）

```bash
python webapp.py   # 可视化界面，浏览器打开 http://127.0.0.1:5000
python main.py     # 命令行
```

### 4. 示例

```
请输入需求 > 写一个函数，输入一个数字列表，返回它们的平均值

===== 编码Agent 生成的代码 =====
def average(nums):
    ...

===== 审查Agent 的审查意见 =====
- Bug/风险：列表为空时会除零...
- 改进建议：添加空列表判断...

===== 修复Agent 修复后的最终代码 =====
def average(nums):
    if not nums:
        return 0
    ...
```

## 项目结构

```
code-review-workflow/
├── main.py                    # CLI 入口
├── webapp.py                  # 可视化服务（Flask + SSE）
├── templates/
│   └── index.html             # 可视化编排界面
├── requirements.txt           # Python 依赖
├── .env.example               # 环境变量模板
├── README.md                  # 本文件
├── Design.md                  # 设计文档
├── core/                      # 复用自项目1的基础层
│   ├── __init__.py
│   ├── llm.py                 # LLM 客户端（带重试）
│   └── memory.py              # 对话记忆
├── workflow/                  # 工作流编排
│   ├── __init__.py
│   ├── context.py             # 共享状态容器
│   ├── agent_base.py          # Agent 基类
│   └── engine.py              # 编排引擎（流程控制/并行/分支/错误恢复）
└── agents/
    ├── __init__.py
    └── workflow_agents.py     # 编码/审查/修复 三个 Agent
```

## 技术栈

- **语言**：Python 3.10+
- **LLM 接口**：OpenAI SDK（兼容多家服务商）
- **复用**：项目1 的 `core/` 基础层
