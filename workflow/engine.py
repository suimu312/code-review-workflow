"""Workflow 编排引擎：按顺序执行多个 Agent，维护共享状态与日志。"""

import logging

from core.llm import LLMClient
from workflow.context import WorkflowContext
from workflow.agent_base import BaseAgent
from agents.workflow_agents import CoderAgent, ReviewerAgent, FixerAgent

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    简单的顺序编排引擎（MVP）。

    核心职责：
    1. 流程控制：按注册顺序依次执行每个 Agent（顺序执行）
    2. 状态共享：为所有 Agent 提供同一个 WorkflowContext
    3. 错误处理：单个 Agent 失败可捕获并记录，不拖垮整个流程
    4. 执行日志：记录每个节点状态，便于追踪
    """

    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or LLMClient()
        # 节点注册表：新增 Agent 只需在列表里加一行，流程就自动包含它（可扩展性）
        self.nodes: list[BaseAgent] = [
            CoderAgent(self.llm),
            ReviewerAgent(self.llm),
            FixerAgent(self.llm),
        ]

    def run(self, user_input: str) -> WorkflowContext:
        """
        执行完整工作流。

        流程：编码Agent → 审查Agent → 修复Agent（顺序执行）
        """
        context = WorkflowContext(user_input)
        context.add_step("Workflow", "running", "工作流启动")

        for i, agent in enumerate(self.nodes):
            step_index = len(context.history)
            context.add_step(agent.name, "running", "开始执行")
            try:
                output = agent.run(context)
                context.set_step_done(step_index, output)
                logger.info("%s 完成", agent.name)
            except Exception as e:
                # 错误处理：记录失败，流程继续推进到下一个节点
                context.history[step_index]["status"] = "failed"
                context.history[step_index]["detail"] = f"执行失败: {e}"
                logger.exception("%s 执行失败", agent.name)

        context.add_step("Workflow", "done", "工作流结束")
        return context

    def log(self, context: WorkflowContext):
        """打印执行日志（状态追踪）。"""
        print("\n===== Workflow 执行日志 =====")
        for step in context.history:
            print(f"[{step['time']}] {step['agent']}: {step['status']}")
