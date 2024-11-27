import time
import librosa
import random
from pathlib import Path
import pendulum
import shutil
from util import logConfig, logger, lumos, clean_cache, ffmpeg, Nox

logConfig("logs/concat.log", rotation="10 MB", level="DEBUG", mode=1)

"""
根据BGM改编切片的速度，并拼接
视频在clips中
BGM在audio中
background 在 video 中
cache工作目录 将left和right合并最后拼接上background
最终文件 dist
"""


def launch():
    clip_folder = Path("data/clips")
    mp4_list = list(clip_folder.glob("**/*.mp4"))
    audio_path = Path() / "data" / "audio" / "drop.aac"
    left_video = Path() / "cache" / "video_left.mp4"
    right_video = Path() / "cache" / "video_right.mp4"
    speed_video(mp4_list, audio_path, left_video, 5)  # create left and right
    speed_video(mp4_list, audio_path, right_video, 5)  # create left and right

    background_path = Path() / "data" / "video" / "white_video.mp4"
    mixin_video(background_path)
    add_bgm(audio_path)
    copy_to_dist()


def get_bpm(audio_file):
    y, sr = librosa.load(audio_file)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return tempo[0]


def speed_video(mp4_list, baseline_path, output_path, sample=None):
    if sample:
        mp4_list = random.sample(mp4_list, sample)
    baseline = get_bpm(baseline_path)
    bpm_list = [get_bpm(video) for video in mp4_list]
    # input_files = "-i a.mp4"
    input_files = " ".join([f"-i {file}" for file in mp4_list])  # "-i mp4 -i mp4"

    speed_list = [baseline / bpm for bpm in bpm_list]
    speed_list = [max(0.5, min(speed, 100)) for speed in speed_list]

    filter_parts = []
    concat_parts = []

    for i in range(len(mp4_list)):
        filter_parts.append(f"[{i}:v]setpts=PTS/{speed_list[i]},scale=1080:1920[v{i}]")
        filter_parts.append(f"[{i}:a]atempo={speed_list[i]},volume=1[a{i}]")
        concat_parts.extend([f"[v{i}]", f"[a{i}]"])

    filter_complex = (
        "; ".join(filter_parts)
        + f"; {''.join(concat_parts)}concat=n={len(mp4_list)}:v=1:a=1[v][a]"
    )
    magic = (
        f"{ffmpeg} {input_files} "
        f'-filter_complex "{filter_complex}" '
        f'-map "[v]" -map "[a]" -c:v libx264 -c:a aac -r 60 {output_path}'
    )
    lumos(magic)


def mixin_video(background_path):
    video_left_path = Path() / "cache" / "video_left.mp4"
    video_right_path = Path() / "cache" / "video_right.mp4"
    output_file = Path() / "cache" / "video_mixin.mp4"
    filter_complex = (
        "[1:v]scale=iw*0.74:ih*0.74[v1_scaled]; "
        "[2:v]scale=iw*0.74:ih*0.74[v2_scaled]; "
        "[0:v][v1_scaled]overlay=x=100:y=-100[bg_v1]; "
        "[bg_v1][v2_scaled]overlay=x=1060:y=-100[final]"
    )

    input_files = f"-i {background_path} -i {video_left_path} -i {video_right_path}"
    magic = (
        f"{ffmpeg} {input_files} "
        f'-filter_complex "{filter_complex}" '
        f'-map "[final]" '
        f"-t 02:15 -c:v libx264 -c:a aac {output_file}"
    )
    lumos(magic)


def add_bgm(audio_path, volume=1):
    video_path = Path() / "cache" / "video_mixin.mp4"
    output_file = Path() / "cache" / "final.mp4"

    input_files = f"-i {video_path} -i {audio_path}"
    magic = (
        f"{ffmpeg} {input_files} "
        f"-c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "
        f'-filter:a "volume={volume}" -shortest {output_file}'
    )
    lumos(magic)


def copy_to_dist():
    # copy to dist
    now = pendulum.now("Asia/Shanghai")
    now_iso = now.to_iso8601_string()[:23].replace(":", "-")

    # 定义源文件和目标目录
    source_path = Path("cache/final.mp4")
    dist_path = Path("dist") / (now_iso + ".mp4")
    # 确保 dist 目录存在，如果不存在则创建
    if not source_path.exists():
        logger.error(f"{source_path} missing.")
    dist_path.parent.mkdir(parents=True, exist_ok=True)
    time.sleep(1)
    shutil.copy(source_path, dist_path)

    if dist_path.exists():
        logger.success(f"{dist_path}")
    else:
        logger.error(f"{dist_path} Missing")


if __name__ == "__main__":
    clean_cache()
    launch()
