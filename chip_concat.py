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
BGm在audio中
cache工作目录
最终文件 dist
"""


def launch():
    clip_folder = Path("data/clips")
    mp4_list = list(clip_folder.glob("**/*.mp4"))
    random.shuffle(mp4_list)
    mp4_list = mp4_list[:12]
    logger.debug("Select: ", mp4_list)
    audio_path = Path() / "data" / "audio" / "bgm.mp4"
    concat_path = Path() / "cache" / "concat.mp4"
    speed_video(mp4_list, audio_path, concat_path)
    add_bgm(audio_path)
    add_intro()
    copy_to_dist()


def get_bpm(audio_file):
    y, sr = librosa.load(audio_file)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return tempo[0]


def speed_video(mp4_list, baseline_path, output_path):
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
        f'-map "[v]" -map "[a]" '
        f"-c:v libx264 -c:a aac "
        f"-r 60 "
        f"{output_path}"
    )
    lumos(magic)


def add_bgm(audio_path, volume=1):
    video_path = Path() / "cache" / "concat.mp4"
    output_file = Path() / "cache" / "main.mp4"

    input_files = f"-i {video_path} -i {audio_path}"
    # audio shortest
    magic = (
        f"{ffmpeg} {input_files} "
        f"-map 0:v:0 -map 1:a:0 "
        f"-c:v copy -c:a aac "
        f'-filter:a "volume={volume}" '
        f"-shortest "
        f"{output_file}"
    )
    # audio loop
    # magic = (
    #     f'{ffmpeg} {input_files} '
    #     f'-filter_complex "[1:a]aloop=loop=-1:size=2e+09[aout]" '
    #     f'-map 0:v:0 -map [aout] '
    #     f'-c:v copy -c:a aac '
    #     f'-shortest {output_file}'
    # )
    lumos(magic)


def add_intro(volume=1):
    logger.debug("add prefix and suffix")
    prefix_path = Path() / "data" / "video" / "prefix.mp4"
    suffix_path = Path() / "data" / "video" / "suffix.mp4"
    video_path = Path() / "cache" / "main.mp4"
    output_path = Path() / "cache" / "final.mp4"

    mp4_list = [video_path]
    if prefix_path.exists():
        mp4_list.insert(0, prefix_path)
    if suffix_path.exists():
        mp4_list.append(suffix_path)
    if len(mp4_list) == 1:
        logger.debug("No prefix or suffix video.")
        shutil.copy(video_path, output_path)
        return
    logger.debug(mp4_list)

    input_files = " ".join([f"-i {file}" for file in mp4_list])  # "-i mp4 -i mp4"

    filter_parts = []
    concat_parts = []

    for i in range(len(mp4_list)):
        filter_parts.append(f"[{i}:v]scale=1080:1920[v{i}]")
        filter_parts.append(f"[{i}:a]volume={volume}[a{i}]")
        concat_parts.extend([f"[v{i}]", f"[a{i}]"])

    filter_complex = (
        "; ".join(filter_parts)
        + f"; {''.join(concat_parts)}concat=n={len(mp4_list)}:v=1:a=1[v][a]"
    )
    magic = (
        f"{ffmpeg} {input_files} "
        f'-filter_complex "{filter_complex}" '
        f'-map "[v]" -map "[a]" '
        f"-c:v libx264 -c:a aac "
        f"-r 60 "
        f"{output_path}"
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
    for _ in range(10):
        clean_cache()
        launch()
