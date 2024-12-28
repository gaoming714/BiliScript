from pathlib import Path
import pendulum
import random
import shutil
import ipdb
import srt
import time
import subprocess

from util import logConfig, logger, lumos, ffmpeg, clean_cache

logConfig("logs/download.log", rotation="10 MB", level="DEBUG")


def launch():
    # 定义 data 文件夹路径
    data_folder = Path("data/clips")
    # subtitle_folder = Path('data/subtitle')

    # 获取 data 文件夹下的所有 .mp4 文件
    raw_list = list(data_folder.glob("**/*.mp4"))
    random.shuffle(raw_list)

    max_duration = 100  # 45 秒
    mp4_list = []
    current_duration = 0
    # 逐个检查视频时长并添加到 mp4_list 中
    for video_file in raw_list:
        # video = mp.VideoFileClip(str(video_file))
        # video_duration = video.duration  # 获取视频时长（秒）
        video_duration = fetch_video_duration(video_file)
        logger.debug(f"{video_file} - {video_duration}s - {current_duration}s")
        # 检查是否超出最大时长
        if current_duration > max_duration:
            break
        # 添加视频文件到 mp4_list，并更新当前累计时长
        mp4_list.append(video_file)
        current_duration += video_duration

    # mp4_list = random.sample(mp4_list, 3)

    print("已添加的视频文件:", mp4_list)
    print("总时长:", current_duration, "秒")

    # concat
    input_files = " ".join([f"-i {video}" for video in mp4_list])
    output_file = Path("cache/concat.mp4")
    # magic = (
    #     f'{ffmpeg} {input_files}'
    #     f' -filter_complex "'
    #     f' [0:v]setpts=PTS/1.4[v1]; [0:a]atempo=1.4,volume=0.5[a1];'
    #     f' [1:v]setpts=PTS/1.4[v2]; [1:a]atempo=1.4,volume=0.5[a2];'
    #     f' [2:v]setpts=PTS/1.4[v3]; [2:a]atempo=1.4,volume=0.5[a3];'
    #     f' [v1][a1][v2][a2][v3][a3]concat=n=3:v=1:a=1[v][a]'
    #     f' "'
    #     f' -map "[v]" -map "[a]" cache/concat.mp4'
    # )

    filter_parts = []
    concat_parts = []

    for i in range(len(mp4_list)):
        filter_parts.append(
            f"[{i}:v]setpts=PTS/1.4[v{i}]; [{i}:a]atempo=1.4,volume=2[a{i}]"
        )
        concat_parts.extend([f"[v{i}]", f"[a{i}]"])

    filter_complex = (
        "; ".join(filter_parts)
        + f"; {''.join(concat_parts)}concat=n={len(mp4_list)}:v=1:a=1[v][a]"
    )

    # 构建完整的 ffmpeg 命令
    magic = (
        f"{ffmpeg} {input_files} "
        f'-filter_complex "{filter_complex}" '
        f'-map "[v]" -map "[a]" {output_file}'
    )

    lumos(magic)
    magic = ""

    # add bgm
    input_files = "-i cache/concat.mp4 -i data/audio/bgm.aac"
    magic = (
        f"{ffmpeg} {input_files}"
        f' -filter_complex "'
        f" [1:a]aloop=loop=-1:size=2e+9,volume=0.6[aud];"
        f" [0:a][aud]amix=duration=shortest"
        f' "'
        f" -c:v copy -shortest cache/withbgm.mp4"
    )

    lumos(magic)
    magic = ""

    # create subtitle
    magic = (
        f"faster-whisper-xxl.exe cache/withbgm.mp4"
        f" --language=Chinese --model=medium --output_dir=cache"
    )
    lumos(magic)
    magic = ""

    # add subtitle
    # create srt
    # "subtitles=cache/withbgm.srt:force_style='Fontname=$(pwd)/qingyin.ttf,Fontsize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H000000FF,Outline=1,Shadow=1,ShadowColour=&H00000000'"
    magic = (
        f"ffmpeg -i cache/withbgm.mp4"
        # f' -vf subtitles=cache/withbgm.srt '
        f" -vf \"subtitles=cache/withbgm.srt:force_style='Fontname=SimSun,Fontsize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H000000FF,Outline=1,Shadow=1,ShadowColour=&H00000000,Alignment=2,MarginV=10'\" "
        f" cache/output_video.mp4"
    )
    lumos(magic)
    magic = ""

    # copy to dist
    now = pendulum.now("Asia/Shanghai")
    now_iso = now.to_iso8601_string()[:23].replace(":", "-")

    # 定义源文件和目标目录
    source_path = Path("cache/output_video.mp4")

    dist_path = Path("dist") / (now_iso + ".mp4")

    # 确保 dist 目录存在，如果不存在则创建
    dist_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(3):
        if source_path.exists() and source_path.stat().st_size > 50:
            print(f"File '{source_path}' has a valid size.")
            break  # 文件有大小，退出函数
        print(
            f"Attempt {attempt + 1}: File '{source_path}' is empty or does not exist. Retrying in 3 seconds..."
        )
        time.sleep(3)
    shutil.copy(source_path, dist_path)


def fetch_video_duration(file_path):
    # 确保 file_path 是 Path 对象
    file_path = Path(file_path)
    # 检查文件是否存在
    if not file_path.is_file():
        raise FileNotFoundError(f"文件 {file_path} 不存在")
    # 使用 ffprobe 获取视频信息，ffprobe 是 ffmpeg 的一个工具
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # 读取时长（单位为秒），并转换为浮点数
    duration = float(result.stdout.strip())
    if duration > 0:
        return duration
    else:
        raise RuntimeError(f"ffprobe 调用失败: duration is zero")


if __name__ == "__main__":
    clean_cache()
    launch()
