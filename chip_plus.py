from pathlib import Path
import pendulum
import random
import shutil
import time
import re
import os

import srt

from util import logConfig, logger, lumos, ffmpeg, clean_cache

logConfig("logs/download.log", rotation="10 MB", level="DEBUG")


def launch():
    # 定义文件夹路径
    raw_folder = Path("data/raw")
    clip_folder = Path("data/clips")
    clip_folder.mkdir(parents=True, exist_ok=True)  # 确保输出文件夹存在

    # 获取 raw_folder 文件夹下的所有 .mp4 文件
    raw_list = list(raw_folder.glob("**/*.mp4"))

    # 遍历每个 .mp4 文件
    for raw_file in raw_list:
        # 检查是否存在同名的 .srt 文件
        srt_file = raw_file.with_suffix(".srt")  # 获取同名的 .srt 文件路径
        if srt_file.exists():
            logger.debug(f"字幕文件已存在: {srt_file}")
        else:
            # 如果 .srt 文件不存在，调用 listen 函数
            listen(raw_file)
        # action
        create_clips(raw_file)


def listen(mp4_file):
    srt_folder = mp4_file.parent
    magic = (
        f"faster-whisper-xxl.exe {mp4_file}"
        f" --language=Chinese --model=medium --output_dir={srt_folder}"
    )
    lumos(magic)


def parse_srt(file_path):
    """
    解析 SRT 文件，返回时间和字幕内容的列表
    """
    # 定义 SRT 时间解析的正则表达式
    srt_time_pattern = re.compile(r"\[(\d+):(\d+\.\d+) --> (\d+):(\d+\.\d+)\] (.+)")
    subtitles = []
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            match = srt_time_pattern.match(line)
            if match:
                start_minute = int(match.group(1))
                start_second = float(match.group(2))
                end_minute = int(match.group(3))
                end_second = float(match.group(4))
                text = match.group(5).strip()

                # 计算开始和结束时间（秒）
                start_time = start_minute * 60 + start_second
                end_time = end_minute * 60 + end_second

                subtitles.append({"start": start_time, "end": end_time, "text": text})
    return subtitles


def read_srt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        subtitles = []
        for sub in srt.parse(file.read()):
            start_seconds = sub.start.total_seconds()  # 获取字幕开始的总秒数
            end_seconds = sub.end.total_seconds()  # 获取字幕结束的总秒数
            subtitles.append(
                {
                    "start": start_seconds,  # 字幕开始的总秒数
                    "end": end_seconds,  # 字幕结束的总秒数
                    "text": sub.content.strip(),  # 字幕内容
                }
            )
    return subtitles


def create_clips(mp4_file, min_duration=10):
    """
    根据同名 SRT 文件中每一句的时间信息，创建 MP4 切片
    """
    srt_file = mp4_file.with_suffix(".srt")
    if not srt_file.exists():
        logger.debug(f"没有找到 SRT 文件: {srt_file}")
        return

    # 解析 SRT 文件
    subtitles = read_srt(srt_file)
    logger.debug(subtitles)
    clip_folder = Path("data/clips")
    clip_folder.mkdir(exist_ok=True)

    start_time = None
    end_time = None
    for idx, subtitle in enumerate(subtitles):
        if start_time == None:
            start_time = subtitle["start"]
        duration = subtitle["end"] - start_time
        if duration > min_duration:
            end_time = subtitle["end"]
        else:
            continue
        if end_time == None:
            end_time = subtitle["end"]

        hex_index = f"{idx:04x}"
        output_file = clip_folder / f"{mp4_file.stem}_clip_{hex_index}.mp4"

        # ffmpeg 命令创建切片
        command = (
            f"{ffmpeg} -i {mp4_file} -ss {start_time} -to {end_time} "
            f"-c:v libx264 -c:a aac {output_file}"
        )

        logger.debug(f"正在创建切片: {output_file}")
        lumos(command)

        # reset start_time end_time
        start_time = None
        end_time = None


if __name__ == "__main__":
    launch()
