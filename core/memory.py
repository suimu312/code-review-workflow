"""对话记忆（从项目1复用）：滑动窗口多轮上下文。"""

from collections import deque


class ConversationMemory:
    """滑动窗口对话记忆，系统消息始终保留在头部。"""

    def __init__(self, system_prompt: str, max_turns: int = 10):
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        self._messages: deque[dict] = deque(maxlen=max_turns * 2)

    def add(self, role: str, content: str):
        self._messages.append({"role": role, "content": content})

    def get_messages(self) -> list[dict]:
        return [{"role": "system", "content": self.system_prompt}] + list(self._messages)

    def clear(self):
        self._messages.clear()

    def __len__(self):
        return len(self._messages)
