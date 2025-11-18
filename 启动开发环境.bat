@echo off
echo =========================================
echo   米家设备监控系统 - 开发环境
echo =========================================
echo.
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo.
echo ✓ 开发环境已激活
echo Python版本:
python --version
echo.
echo 命令:
echo   - python -m src.main          启动GUI程序
echo   - python cli_monitor.py       启动CLI版本
echo   - pyinstaller mi-monitor.spec 打包为EXE
echo.
cmd /k
