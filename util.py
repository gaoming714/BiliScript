import os
import sys
import time
import json
import shutil
import hashlib
import subprocess
import pendulum
from pathlib import Path
from loguru import logger
from tqdm.rich import tqdm

# disable warning for tqdm.rich
import warnings
from tqdm.std import TqdmExperimentalWarning

warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)


def lumos(cmd, mode=1, quiet=False):
    if mode == 2:
        logger.warning("➜  " + cmd)
    elif mode == 1:
        logger.debug("➜  " + cmd)
    elif mode == 0:
        logger.debug("➜  " + cmd)
    else:
        raise
    if quiet == True:
        cmd = cmd + " >nul 2>&1"
    res = os.system(cmd)
    return res


ffmpeg = Path("runtime") / "ffmpeg.exe" if (Path("runtime") / "ffmpeg.exe").exists() else "ffmpeg"
ffprobe = Path("runtime") / "ffprobe.exe" if (Path("runtime") / "ffprobe.exe").exists() else "ffprobe"
wget = Path("runtime") / "wget.exe" if (Path("runtime") / "wget.exe").exists() else "wget"
curl = Path("runtime") / "curl.exe" if (Path("runtime") / "curl.exe").exists() else "curl"


def make_hash(file_path):
    md5_hash = hashlib.md5()
    sha1_hash = hashlib.sha1()
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            md5_hash.update(data)
            sha1_hash.update(data)
            sha256_hash.update(data)

    return md5_hash.hexdigest(), sha1_hash.hexdigest(), sha256_hash.hexdigest()


def show_local(path=Path("./downloads"), prefix=None):
    if not check_folder(path):
        return []
    mp4_files = list(path.glob("{}.*.mp4").format(prefix))
    video_ids = []
    for video in mp4_files:
        id = str(video).split(".")[-2]
        if check_intact(video):
            logger.debug("Exists {}".format(id))
            video_ids.append(id)
        else:
            logger.warning("Incomplete {}".format(id))
            pass
    return video_ids


def check_folder(path, mkdir=False):
    if path.exists():
        if path.is_dir():
            logger.debug("Exists Folder {}".format(path))
            return True
        else:
            raise
    else:
        if mkdir:
            logger.debug("Mk Folder {}".format(path))
            os.makedirs(path)
            return True
        else:
            logger.debug("No Folder {}".format(path))
            return False


def create_hash(path):
    if not path.exists():
        return
    with open(path, "rb") as fp:
        context = fp.read()
    md5sum = hashlib.md5(context).hexdigest()
    return md5sum


def check_hash(video_path, md5dot):
    if not video_path.exists():
        return False
    idx = str(video_path).split(".")[-2]
    with open(video_path, "rb") as fp:
        video_context = fp.read()
    md5sum = hashlib.md5(video_context).hexdigest()
    if md5sum == md5dot:
        return True
    else:
        logger.debug(
            "ID {} diff hash MD5 \n".format(idx)
            + " Video_PATH:  {}\n".format(video_path)
            + " DB - File:  {} - {}".format(md5dot, md5sum)
        )
        return False


def check_intact_old(video_path):
    cmd = "sh intact.sh {}".format(video_path)
    if not video_path.exists():
        logger.error("File not found {}".format(video_path))
        return False
    if lumos(cmd) == 0:
        logger.debug("check_intact_inner success {}".format(video_path))
        return True
    else:
        logger.debug("check_intact_inner fail {}".format(video_path))
        return False

def check_intact(file_path):
    try:
        result = subprocess.run(
            [f"{ffmpeg}", "-v", "error", "-i", file_path, "-f", "null", "-"],
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            text=True
        )
        if result.stderr.strip():
            logger.warning("File has errors:")
            # logger.debug(result.stderr)
            return False
        else:
            logger.debug("File is valid.")
            return True
    except Exception as e:
        # logger.debug(f"Error checking file: {e}")
        return False

def clean_cache():
    # 定义缓存文件夹路径
    cache_folder = Path("cache")
    now = pendulum.now("Asia/Shanghai")
    now_iso = now.to_iso8601_string()[:23].replace(":", "-")
    # 创建以当前时间命名的子文件夹
    target_dir = cache_folder / now_iso
    target_dir.mkdir(parents=True, exist_ok=True)
    # 如果 cache 文件夹存在且不为空，则删除其所有内容
    if cache_folder.exists() and any(cache_folder.iterdir()):
        for item in cache_folder.iterdir():
            # if item.is_dir():
            #     shutil.rmtree(item)  # 删除子文件夹
            # else:
            #     item.unlink()        # 删除文件
            if item.is_file():  # 只处理文件，排除文件夹
                shutil.move(item, target_dir / item.name)
        print("Cache folder cleared.")

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

class Nox:
    def __init__(self, code, payload=None):
        self.code = code
        self.payload = payload

        if code == 0 and payload == None:
            self.payload = "Success"

    def __bool__(self):
        return self.code == 0

    def __repr__(self):
        if self:
            return f"Status(code={self.code}, payload='{self.payload}')"
        else:
            return f"Status(code={self.code}, error='{self.payload}')"


def set_datetime(record):
    record["extra"]["datetime"] = pendulum.now("Asia/Shanghai").to_iso8601_string()[:23]


def logConfig(
    log_file="logs/default.log", rotation="10 MB", level="DEBUG", mode=2, tqdm_hold=True
):
    """
    配置 Loguru 日志记录
    :param log_level: 日志级别，如 "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    :param log_file: 日志文件路径
    :param rotation: 日志文件轮换设置，如 "10 MB" 表示文件大小达到 10MB 时轮换
    使用方法

    # 在程序开始时配置日志
    from model.util import logConfig, logger
    logConfig(log_file="myapp.log", rotation="5 MB")
    # 使用 logger 记录日志
    logger.info("This is an info message")
    logger.debug("This is a debug message")
    """
    logger.remove()  # 移除默认的处理程序（如果有的话）
    if mode == 0:
        style = (
            " <level>{level: <8}</level>"
            + "<green>❯ </green>"
            + "<level>{message}</level>"
        )
    if mode == 1:
        style = (
            "<green>{extra[datetime]}</green>"
            + " <level>{level: <8}</level>"
            + "<green>❯ </green>"
            + "<level>{message}</level>"
        )
    else:
        style = (
            "<green>{extra[datetime]}</green>"
            + " <level>{level: <8}</level>"
            + "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
            + "<green>❯ </green>"
            + "<level>{message}</level>"
        )
    # alternative ➲ ⛏ ☄ ➜ ♻ ✨ 🧀 ❯
    logger.configure(patcher=set_datetime)
    if tqdm_hold == True:
        stdout = lambda msg: tqdm.write(msg, end="")
    else:
        stdout = sys.stderr

    logger.add(stdout, level=level, colorize=True, format=style)
    logger.add(
        log_file, colorize=False, encoding="utf-8", format=style, rotation=rotation
    )
    logger.add(
        log_file + ".rich",
        colorize=True,
        encoding="utf-8",
        format=style,
        rotation=rotation,
    )
    logger.add(
        log_file + ".error",
        level="ERROR",
        colorize=False,
        encoding="utf-8",
        format=style,
        rotation=rotation,
    )
    logger.add(
        log_file + ".error.rich",
        level="ERROR",
        colorize=True,
        encoding="utf-8",
        format=style,
        rotation=rotation,
    )
