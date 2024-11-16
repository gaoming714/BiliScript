import time
import librosa
import random
from pathlib import Path
import pendulum
import shutil
from util import (
    logConfig,
    logger,
    lumos,
    clean_cache,
    ffmpeg,
    Nox
)

logConfig("logs/download.log", rotation="10 MB", level="DEBUG", mode=1, tqdm_hold=True)

def get_bpm(audio_file):
    y, sr = librosa.load(audio_file)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return tempo[0]

def launch():
    clip_folder = Path('data/clips')
    mp4_list = list(clip_folder.glob('**/*.mp4'))
    random.shuffle(mp4_list)
    audio_path = Path() / "data" / "audio" / "bgm.mp4"
    speed_video(mp4_list, audio_path)
    add_bgm()
    copy_to_dist()

def add_bgm(volume = 1):
    video_path = Path() / "cache" / "concat.mp4"
    audio_path = Path() / "data" / "audio" / "bgm.mp4"
    output_file = Path() / "cache" / "final.mp4"

    input_files = f'-i {video_path} -i {audio_path}' 
    mana = (
        f'{ffmpeg} {input_files} '
        f'-c:v copy -c:a aac -map 0:v:0 -map 1:a:0 '
        f'-filter:a "volume={volume}" -shortest {output_file}'
    )
    lumos(mana)

def speed_video(mp4_list, baseline_path):
    baseline = get_bpm(baseline_path)
    bpm_list = [get_bpm(video) for video in mp4_list]
    # input_files = "-i a.mp4"
    input_files = " ".join([f"-i {file}" for file in mp4_list]) # "-i mp4 -i mp4"
    output_file = Path() / "cache" / "concat.mp4"

    speed_list = [baseline / bpm for bpm in bpm_list]
    speed_list = [max(0.5, min(speed, 100)) for speed in speed_list]

    filter_parts = []
    concat_parts = []

    for i in range(len(mp4_list)):
        filter_parts.append(f"[{i}:v]setpts=PTS/{speed_list[i]},scale=1080:1920[v{i}]")
        filter_parts.append(f"[{i}:a]atempo={speed_list[i]},volume=1[a{i}]")
        concat_parts.extend([f"[v{i}]", f"[a{i}]"])

    filter_complex = "; ".join(filter_parts) + f"; {''.join(concat_parts)}concat=n={len(mp4_list)}:v=1:a=1[v][a]"
    mana = (
        f'{ffmpeg} {input_files} '
        f'-filter_complex "{filter_complex}" '
        f'-map "[v]" -map "[a]" -c:v libx264 -c:a aac {output_file}'
    )
    lumos(mana)

def copy_to_dist():
    # copy to dist
    now = pendulum.now("Asia/Shanghai")
    now_iso = now.to_iso8601_string()[:22].replace(":","-")

    # 定义源文件和目标目录
    source_path = Path("cache/final.mp4")
    dist_path = Path("dist") / (now_iso + ".mp4")
    # 确保 dist 目录存在，如果不存在则创建
    dist_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(3):
        if source_path.exists() and source_path.stat().st_size > 50:
            logger.debug(f"File '{source_path}' has a valid size.")
            break  # 文件有大小，退出函数
        logger.debug(f"Attempt {attempt + 1}: File '{source_path}' is empty or does not exist. Retrying in 3 seconds...")
        time.sleep(3)
    shutil.copy(source_path, dist_path)

if __name__ == '__main__':
    clean_cache()
    launch()
