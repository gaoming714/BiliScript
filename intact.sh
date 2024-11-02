#!/bin/bash

# check file_name
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <file.mp4>"
    exit 1
fi

file_name="$1"

error_output=$(ffmpeg -i "$file_name" -v error -f null - 2>&1 1>/dev/null)

# 检查error_output是否为空
if [ -n "$error_output" ]; then
    # echo "ffmpeg 产生了错误输出:"
    # echo "$error_output"
    exit 1
else
    # echo "ffmpeg 没有产生错误输出."
    exit 0
fi
