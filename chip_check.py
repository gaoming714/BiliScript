import os
from pathlib import Path
import subprocess
from util import logConfig, logger, lumos, clean_cache, ffmpeg, ffprobe, Nox

# 目标目录和条件
clips_dir = Path("data/clips")
target_resolution = "1080x1920"
target_sar = "1:1"

# 检查是否符合条件的函数
def check_video(file_path):
    try:
        # 使用 ffmpeg 获取文件的分辨率和 SAR
        command = (
            f"{ffprobe} -v error -select_streams v:0 -show_entries stream=width,height,sample_aspect_ratio "
            f"-of default=noprint_wrappers=1:nokey=1 \"{file_path}\""
        )
        output = subprocess.check_output(command, shell=True, text=True).strip().split("\n")
        
        if len(output) >= 3:
            width, height, sar = output[0], output[1], output[2]
            resolution = f"{width}x{height}"
            return resolution == target_resolution and sar == target_sar
    except subprocess.CalledProcessError as e:
        logger.info(f"Error checking file {file_path}: {e}")
    return False
def launch():
    # 查找所有 mp4 文件并验证
    non_compliant_files = []
    for mp4_file in clips_dir.rglob("*.mp4"):
        if not check_video(mp4_file):
            non_compliant_files.append(mp4_file)

    # 输出结果
    if non_compliant_files:
        logger.info("以下文件不符合分辨率和 SAR 要求:")
        for file in non_compliant_files:
            logger.info(file)
    else:
        logger.info("所有文件都符合要求。")

if __name__ == "__main__":
    launch()