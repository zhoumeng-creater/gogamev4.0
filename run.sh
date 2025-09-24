#!/bin/bash
# run.sh - Linux/Mac运行脚本

# 检查Python是否安装
if ! command -v python3 &> /dev/null
then
    echo "Python 3 未安装，请先安装Python 3.8或更高版本"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装/更新依赖
echo "检查依赖..."
pip install -q -r requirements.txt

# 运行程序
echo "启动围棋大师..."
python main.py