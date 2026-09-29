"""编码Agent：根据需求生成 Python 代码。"""

from workflow.agent_base import BaseAgent
from workflow.context import WorkflowContext


class CoderAgent(BaseAgent):
    name = "编码Agent"

    def system_prompt(self) -> str:
        return (
            "你是团队中的编码工程师。你的职责：根据需求描述，编写清晰、正确的 Python 代码。\n"
            "要求：\n"
            "1. 代码可直接运行，包含完整的函数定义\n"
            "2. 添加必要的中文注释\n"
            "3. 只需输出代码本身，不要输出额外解释\n"
            "4. 用 ```python 代码块包裹代码"
        )

    def run(self, context: WorkflowContext) -> str:
        task = f"请根据以下需求编写 Python 代码：\n{context.input}"
        code = self._ask_llm(task)
        context.generated_code = code
        return code


class ReviewerAgent(BaseAgent):
    name = "审查Agent"

    def system_prompt(self) -> str:
        return (
            "你是团队中的资深代码审查专家。你的职责：审查编码工程师给出的代码，找出问题。\n"
            "请按以下结构输出审查意见：\n"
            "- Bug/风险：可能出错或异常的地方\n"
            "- 规范问题：命名、格式、可读性\n"
            "- 改进建议：具体、可落地的优化方向"
        )

    def run(self, context: WorkflowContext) -> str:
        # 从共享状态读取编码Agent的输出
        code = context.generated_code
        task = f"请审查以下代码：\n{code}"
        review = self._ask_llm(task)
        context.review_result = review
        return review


class FixerAgent(BaseAgent):
    name = "修复Agent"

    def system_prompt(self) -> str:
        return (
            "你是团队中的修复工程师。你的职责：根据审查意见修复代码，产出修正后的最终版本。\n"
            "要求：\n"
            "1. 保留原代码的功能，只修复审查中提出的问题\n"
            "2. 输出完整的最终代码，用 ```python 代码块包裹\n"
            "3. 不要输出解释，只输出代码"
        )

    def run(self, context: WorkflowContext) -> str:
        # 同时读取编码结果和审查意见，修复代码
        code = context.generated_code
        review = context.review_result
        task = f"原始代码：\n{code}\n\n审查意见：\n{review}\n\n请根据审查意见修复代码，输出修正后的完整代码。"
        fixed = self._ask_llm(task)
        context.fixed_code = fixed
        return fixed
