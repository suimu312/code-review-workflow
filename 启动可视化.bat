@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动 Code Review Workflow 可视化界面...
echo 启动完成后，请在浏览器打开: http://127.0.0.1:5000
echo 按 Ctrl+C 可停止服务
echo.
python webapp.py
pause
