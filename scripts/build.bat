@echo off
REM 米家设备监控系统 - 打包脚本 (Windows)
REM 使用方法: 双击运行此文件或在命令行中执行 build.bat

echo ========================================
echo 米家设备监控系统 - 打包工具
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未检测到Python,请先安装Python 3.9+
    pause
    exit /b 1
)

echo [1/5] 检查依赖...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
)

echo.
echo [2/5] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [3/5] 开始打包...
pyinstaller mi-monitor.spec

if errorlevel 1 (
    echo.
    echo 打包失败!
    pause
    exit /b 1
)

echo.
echo [4/5] 复制必要文件...
if not exist dist\config mkdir dist\config
copy config\config.yaml dist\config\ >nul 2>&1

if not exist dist\data mkdir dist\data
if not exist dist\logs mkdir dist\logs

echo.
echo [5/5] 创建启动脚本...
(
    echo @echo off
    echo cd /d "%%~dp0"
    echo start "" "MiMonitor.exe"
) > dist\启动监控.bat

echo.
echo ========================================
echo 打包完成!
echo ========================================
echo.
echo 可执行文件位置: dist\MiMonitor.exe
echo.
echo 发布说明:
echo 1. 将 dist 目录下的所有文件打包发布
echo 2. 用户首次运行需要登录米家账号
echo 3. 配置文件位于 config\config.yaml
echo.
pause
