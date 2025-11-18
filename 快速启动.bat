@echo off
echo 启动米家监控系统...
cd /d "%~dp0"
call venv\Scripts\activate.bat
python -m src.main
