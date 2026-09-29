"""可视化 Workflow 服务：Flask + SSE 实时推送工作流状态。

运行：python webapp.py
访问：浏览器打开 http://127.0.0.1:5000
"""

import os
import json
import queue
import threading
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

from flask import Flask, request, Response, render_template
from workflow.engine import WorkflowEngine

app = Flask(__name__)

# 事件队列：后端把工作流事件放进去，SSE 端读取发给浏览器
event_queue: queue.Queue = queue.Queue()


def _emit(event_type: str, **data):
    """把事件打包进 SSE 队列。"""
    event_queue.put({"type": event_type, **data})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/run", methods=["POST"])
def run():
    """触发工作流（后台线程执行），立即返回。"""
    data = request.get_json(silent=True) or {}
    user_input = data.get("input", "").strip()
    if not user_input:
        user_input = "写一个函数，输入一个数字列表，返回它们的平均值和最大值"

    def worker():
        # 清空旧事件
        while not event_queue.empty():
            event_queue.get()
        engine = WorkflowEngine(on_event=_emit)
        try:
            engine.run(user_input)
        except Exception as e:
            _emit("workflow_failed", agent="Workflow", message=str(e))

    threading.Thread(target=worker, daemon=True).start()
    return {"ok": True}


@app.route("/events")
def events():
    """SSE 流：把队列里的事件实时推给浏览器。"""
    def generate():
        while True:
            try:
                evt = event_queue.get(timeout=15)
                yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"
            except queue.Empty:
                yield ": keep-alive\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    print("可视化 Workflow 界面已启动：http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
