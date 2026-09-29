"""工作流共享状态：所有 Agent 通过它传递消息、共享数据。"""

import json
import time
import logging

logger = logging.getLogger(__name__)


class WorkflowContext:
    """
    Workflow 的共享状态容器。

    这是 Agent 间"消息传递/状态共享"的核心：每个 Agent 从 context 读取输入，
    把输出写回 context，后一个 Agent 就能读到前一个 Agent 的结果。
    同时记录完整执行历史，供日志与状态追踪使用。
    """

    def __init__(self, initial_input: str):
        self.input = initial_input          # 用户/初始需求
        self.generated_code = ""            # 编码Agent 输出
        self.review_result = ""             # 审查Agent 输出
        self.fixed_code = ""                # 修复Agent 输出
        self.history: list[dict] = []       # 执行历史（每个步骤一条）
        self._start_time = time.time()

    def add_step(self, agent_name: str, status: str, detail: str = ""):
        """记录一步执行。status: pending/running/done/failed"""
        self.history.append({
            "agent": agent_name,
            "status": status,
            "detail": detail,
            "time": time.strftime("%H:%M:%S"),
        })
        logger.info("[%s] %s %s", agent_name, status, detail[:80])

    def set_step_done(self, index: int, output: str):
        """标记某步完成并写入结果摘要。"""
        self.history[index]["status"] = "done"
        self.history[index]["output_preview"] = output[:200]

    def to_dict(self) -> dict:
        """导出状态，便于日志和展示。"""
        return {
            "input": self.input,
            "generated_code": self.generated_code,
            "review_result": self.review_result,
            "fixed_code": self.fixed_code,
        }

    def summary(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
