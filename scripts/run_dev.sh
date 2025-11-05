#!/bin/bash
# 米家设备监控系统 - 开发环境启动脚本

echo "========================================="
echo "米家设备监控系统 - 开发模式"
echo "========================================="
echo

# 检查Python
if ! command -v python &> /dev/null; then
    echo "错误: 未检测到Python,请先安装Python 3.9+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "[1/3] 创建虚拟环境..."
    python -m venv venv
fi

# 激活虚拟环境
echo "[2/3] 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "[3/3] 安装依赖..."
pip install -r requirements.txt

echo
echo "========================================="
echo "启动应用程序..."
echo "========================================="
echo

# 运行应用
python -m src.main

deactivate
