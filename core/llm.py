"""LLM 客户端（从项目1复用）：支持 OpenAI 兼容接口，带指数退避重试。"""

import os
import time
import logging
from openai import OpenAI, APIError, APITimeoutError, RateLimitError

logger = logging.getLogger(__name__)


class LLMClient:
    """对 OpenAI SDK 的薄封装，统一处理配置、重试和超时。"""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_retries: int = 3,
        timeout: int = 60,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "your-api-key-here")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_retries = int(os.getenv("MAX_RETRIES", max_retries))
        self.timeout = int(os.getenv("REQUEST_TIMEOUT", timeout))

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )
        logger.info("LLMClient 初始化完成，模型=%s", self.model)

    def chat(self, messages: list[dict]) -> str:
        """发起对话，带指数退避重试，返回助手文本内容。"""
        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
                return resp.choices[0].message.content or ""
            except (APITimeoutError, RateLimitError, APIError) as e:
                last_err = e
                wait = 2 ** (attempt - 1)
                logger.warning("LLM 请求第 %d 次失败: %s，%d 秒后重试…", attempt, e, wait)
                time.sleep(wait)
        raise RuntimeError(f"LLM 连续 {self.max_retries} 次请求失败: {last_err}")
