#!/bin/bash

# 确保脚本在正确的目录下运行
cd "$(dirname "$0")"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
    
    echo "正在安装依赖..."
    source venv/bin/activate
    ./venv/bin/python3 -m pip install -r requirements.txt
else
    echo "正在激活虚拟环境..."
    source venv/bin/activate
fi

# 运行程序
echo "启动日志分析工具..."
# 设置环境变量以抑制 IMK 警告
export PYTHON_IMK_SUPPRESS_WARNING=1
./venv/bin/python3 main.py 