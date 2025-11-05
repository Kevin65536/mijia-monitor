@echo off
REM 米家设备监控系统 - 开发环境启动脚本 (Windows)

echo =========================================
echo 米家设备监控系统 - 开发模式
echo =========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未检测到Python,请先安装Python 3.9+
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist venv (
    echo [1/3] 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo [2/3] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo [3/3] 安装依赖...
pip install -r requirements.txt

echo.
echo =========================================
echo 启动应用程序...
echo =========================================
echo.

REM 运行应用
python -m src.main

deactivate
pause
