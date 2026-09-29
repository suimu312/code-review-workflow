"""Workflow 三个 Agent：编码 / 审查（并行）/ 修复（循环自检）。

体现高级流程控制：
- 审查Agent 内部并行执行"规则检查 + LLM审查"两个子任务
- 修复Agent 内部循环"修复→自检→再修"最多 2 轮
"""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed

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
            "你是团队中的资深代码审查专家。你的职责：审查代码，找出问题。\n"
            "请按以下结构输出审查意见：\n"
            "- Bug/风险：可能出错或异常的地方\n"
            "- 规范问题：命名、格式、可读性\n"
            "- 改进建议：具体、可落地的优化方向"
        )

    def run(self, context: WorkflowContext) -> str:
        code = context.generated_code

        # 并行执行两个独立子任务（体现并行执行）
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_llm = executor.submit(self._llm_review, code)
            future_rule = executor.submit(self._rule_review, code)
            llm_result = future_llm.result(timeout=120)
            rule_result = future_rule.result(timeout=30)

        # 合并两个子任务结果
        review = f"【规则静态检查】\n{rule_result}\n\n【LLM深度审查】\n{llm_result}"
        context.review_result = review
        return review

    def _rule_review(self, code: str) -> str:
        """规则审查：不依赖 LLM，用正则做基础静态检查。"""
        issues = []
        if "import" not in code:
            issues.append("- 缺少 import 语句（可能依赖未声明）")
        if "def " not in code:
            issues.append("- 未发现函数定义")
        if "TODO" in code or "FIXME" in code:
            issues.append("- 存在 TODO/FIXME 待办标记")
        if len(code.splitlines()) > 60:
            issues.append("- 函数/代码过长，建议拆分")
        if not issues:
            issues.append("- 未发现明显结构性问题")
        return "\n".join(issues)

    def _llm_review(self, code: str) -> str:
        """LLM 深度审查。"""
        task = f"请审查以下代码：\n{code}"
        return self._ask_llm(task)


class FixerAgent(BaseAgent):
    name = "修复Agent"

    def system_prompt(self) -> str:
        return (
            "你是团队中的修复工程师。你的职责：根据审查意见修复代码。\n"
            "要求：\n"
            "1. 保留原功能，只修复审查指出的问题\n"
            "2. 输出完整的最终代码，用 ```python 代码块包裹\n"
            "3. 不要输出解释，只输出代码"
        )

    def run(self, context: WorkflowContext) -> str:
        code = context.generated_code
        review = context.review_result

        # 循环自检：修复 → 检查 → 再修，最多 2 轮（体现循环控制）
        current = code
        for round_no in (1, 2):
            task = (
                f"原始代码：\n{current}\n\n审查意见：\n{review}\n\n"
                f"第 {round_no} 轮修复：请根据审查意见修复代码，输出修正后的完整代码。"
            )
            current = self._ask_llm(task)

            # 简单自检：确认输出里仍有函数定义，否则继续下一轮
            if "def " in current:
                break

        context.fixed_code = current
        return current
