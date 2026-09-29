"""Agent 基类：统一所有节点的接口和日志能力。"""

import logging
from abc import ABC, abstractmethod

from core.llm import LLMClient
from core.memory import ConversationMemory
from workflow.context import WorkflowContext

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    所有 Workflow 节点的基类。

    每个 Agent 有独立的名字和专属 System Prompt（自建对话记忆），
    通过 run(context) 接收共享状态、返回输出文本，实现节点解耦。
    """

    name: str = "base"

    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or LLMClient()
        self.memory = ConversationMemory(system_prompt=self.system_prompt())

    @abstractmethod
    def system_prompt(self) -> str:
        """返回该 Agent 的角色设定。"""
        ...

    @abstractmethod
    def run(self, context: WorkflowContext) -> str:
        """执行该 Agent 的任务，返回输出文本。"""
        ...

    def _ask_llm(self, task: str) -> str:
        """把任务交给 LLM，返回回答。"""
        self.memory.add("user", task)
        return self.llm.chat(self.memory.get_messages())
