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
            f"{ffprobe} -v error -select_streams v:0 -show_entries stream=width,height,sample_aspect_ratio"
            f' -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
        )
        output = (
            subprocess.check_output(command, shell=True, text=True).strip().split("\n")
        )

        if len(output) >= 3:
            width, height, sar = output[0], output[1], output[2]
            resolution = f"{width}x{height}"
            return resolution == target_resolution and sar == target_sar
    except subprocess.CalledProcessError as e:
        logger.info(f"Error checking file {file_path}: {e}")
    return False


def convert_video(file_path):
    try:
        file_path = Path(file_path)
        originals_dir = file_path.parent / "originals"  # 子目录存放原始文件
        originals_dir.mkdir(exist_ok=True)  # 如果不存在，创建目录

        origin_path = originals_dir / (
            file_path.stem + file_path.suffix
        )  # 子目录中的原始文件路径
        output_path = file_path  # 转换后的文件名与原文件名相同

        # 将原始文件移动到子目录
        file_path.rename(origin_path)

        # 使用 ffmpeg 转换视频分辨率和 SAR
        command = (
            f'{ffmpeg} -i "{origin_path}" -vf "scale={target_resolution},setsar={target_sar}"'
            f' -c:v libx264 -c:a aac "{output_path}"'
        )
        subprocess.check_call(command, shell=True)
        logger.info(f"Successfully converted {origin_path} to {output_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error converting file {file_path}: {e}")
        # 如果转换失败，将文件移回原目录
        if origin_path.exists():
            origin_path.rename(file_path)
            logger.info(f"Restored original file to {file_path}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def launch():
    # 查找所有 mp4 文件并验证
    non_compliant_files = []
    for mp4_file in clips_dir.rglob("*.mp4"):
        if mp4_file.name.endswith("_converted.mp4"):
            continue
        if not check_video(mp4_file):
            non_compliant_files.append(mp4_file)

    # 输出结果并转换不符合条件的视频
    if non_compliant_files:
        logger.info("以下文件不符合分辨率和 SAR 要求，并将被转换:")
        for file in non_compliant_files:
            logger.info(file)
            convert_video(file)
    else:
        logger.info("所有文件都符合要求。")


if __name__ == "__main__":
    launch()
