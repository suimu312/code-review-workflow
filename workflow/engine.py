"""Workflow 编排引擎：顺序执行 + 条件分支 + 并行执行 + 错误恢复 + 事件推送。

MVP 升级版，支撑可视化界面：
- on_event 回调：每个节点的状态变化实时推送给前端
- 条件分支：审查无 Bug 时跳过修复节点
- 错误恢复：节点失败自动重试一次
- 执行日志：完整记录每个节点状态
"""

import logging
import threading
from typing import Callable

from core.llm import LLMClient
from workflow.context import WorkflowContext
from agents.workflow_agents import CoderAgent, ReviewerAgent, FixerAgent

logger = logging.getLogger(__name__)

# 事件回调签名: on_event(event_type: str, **data)
EventCallback = Callable[[str, dict], None]


class WorkflowEngine:
    """
    简单的可视化编排引擎。

    流程：编码Agent → 审查Agent（并行子任务）→ [条件]修复Agent → 结束
    """

    def __init__(self, llm: LLMClient | None = None, on_event: EventCallback | None = None):
        self.llm = llm or LLMClient()
        self.on_event = on_event or (lambda _type, **_data: None)
        self.nodes = [
            CoderAgent(self.llm),
            ReviewerAgent(self.llm),
            FixerAgent(self.llm),
        ]
        self._run_lock = threading.Lock()

    # ---------- 事件推送 ----------
    def _emit(self, event_type: str, **data):
        data.setdefault("agent", "")
        self.on_event(event_type, **data)

    # ---------- 单节点执行（带错误恢复） ----------
    def _run_node(self, agent, context: WorkflowContext) -> str:
        """
        执行一个节点。失败时记录并自动重试一次（错误恢复机制）。
        """
        step_index = len(context.history)
        context.add_step(agent.name, "running", "开始执行")
        self._emit("node_start", agent=agent.name)

        for attempt in (1, 2):  # 最多尝试 2 次
            try:
                output = agent.run(context)
                context.set_step_done(step_index, output)
                self._emit("node_done", agent=agent.name, output=output)
                return output
            except Exception as e:
                logger.exception("%s 第 %d 次执行失败", agent.name, attempt)
                if attempt == 1:
                    context.history[step_index]["detail"] = f"第1次失败: {e}，重试中…"
                    self._emit("node_retry", agent=agent.name, message=str(e))
                else:
                    context.history[step_index]["status"] = "failed"
                    context.history[step_index]["detail"] = f"执行失败: {e}"
                    self._emit("node_failed", agent=agent.name, message=str(e))
                    return ""

        return ""

    # ---------- 条件分支判断 ----------
    def _needs_fix(self, review: str) -> bool:
        """根据审查意见判断是否需要修复（条件分支）。"""
        lowered = review.lower()
        return any(k in lowered for k in ("bug", "风险", "error", "错误", "建议修复", "严重"))

    # ---------- 主流程 ----------
    def run(self, user_input: str) -> WorkflowContext:
        context = WorkflowContext(user_input)
        self._emit("workflow_start", agent="Workflow", message="工作流启动")

        # 1. 编码
        code = self._run_node(self.nodes[0], context)
        if not code:
            self._emit("workflow_failed", agent="Workflow", message="编码Agent 失败，流程终止")
            return context

        # 2. 审查（内部并行执行子任务）
        review = self._run_node(self.nodes[1], context)

        # 3. 条件分支：有 Bug 才修复，否则跳过
        if self._needs_fix(review):
            self._emit("branch_yes", agent="Workflow", message="审查发现问题，进入修复节点")
            self._run_node(self.nodes[2], context)
        else:
            self._emit("branch_no", agent="Workflow", message="审查通过，无需修复，跳过修复节点")

        self._emit("workflow_done", agent="Workflow", message="工作流结束", summary=context.summary())
        return context
