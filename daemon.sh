#!/bin/bash

# 检查是否提供了参数
if [ -z "$1" ]; then
    echo "please add python file arg"
    exit 1
fi

# 获取 Python 文件路径
PYTHON_FILE="$1"

# 获取其他参数（如果有的话）
shift  # 移除第一个参数（Python 文件名）
OTHER_ARGS="$@"

# 检查参数是否以 .py 结尾
if [[ "$PYTHON_FILE" == *.py ]]; then
    uv run "$PYTHON_FILE" $OTHER_ARGS
else
    uv run "$PYTHON_FILE.py" $OTHER_ARGS
fi