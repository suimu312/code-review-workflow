#!/usr/bin/env python3
"""Code Review Workflow — 多Agent协作工作流 CLI 入口。"""

import os
import sys
import logging


def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


_load_env()

from workflow.engine import WorkflowEngine


BANNER = """
╔══════════════════════════════════════════════╗
║   Code Review Workflow · 多Agent协作工作流   ║
╠══════════════════════════════════════════════╣
║   流程：编码Agent → 审查Agent → 修复Agent    ║
║   输入一个需求，三个Agent自动接力完成。      ║
╚══════════════════════════════════════════════╝
"""


def main():
    logging.basicConfig(level=logging.WARNING,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    if os.getenv("OPENAI_API_KEY", "") in ("", "your-api-key-here"):
        print("提示：尚未配置 API Key。请复制 .env.example 为 .env 并填写。")

    print(BANNER)
    print("示例：写一个函数，输入一个数字列表，返回它们的平均值")
    user_input = input("\n请输入需求 > ").strip()
    if not user_input:
        user_input = "写一个函数，输入一个数字列表，返回它们的平均值"
        print(f"（未输入，使用示例）→ {user_input}")

    engine = WorkflowEngine()
    print("\n工作流启动，三个 Agent 依次执行，请稍候…\n")

    try:
        context = engine.run(user_input)
    except Exception as e:
        print(f"\n[错误] 工作流执行失败: {e}")
        return

    # 输出结果
    engine.log(context)

    print("\n===== 编码Agent 生成的代码 =====")
    print(context.generated_code)

    print("\n===== 审查Agent 的审查意见 =====")
    print(context.review_result)

    print("\n===== 修复Agent 修复后的最终代码 =====")
    print(context.fixed_code)

    print("\n===== 最终共享状态 =====")
    print(context.summary())


if __name__ == "__main__":
    main()
