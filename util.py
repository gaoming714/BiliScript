import os
import sys
import time
import json
import hashlib
import pendulum
from pathlib import Path
from loguru import logger


def lumos(cmd, warning=False):
    # res = 0
    if warning == True:
        logger.warning("➜  " + cmd)
    else:
        logger.debug("➜  " + cmd)
    res = os.system(cmd)
    return res


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


def check_intact(video_path):
    cmd = "sh intact.sh {}".format(video_path)
    if not video_path.exists():
        return False
    if lumos(cmd) == 0:
        return True
    else:
        return False


def set_datetime(record):
    record["extra"]["datetime"] = pendulum.now("Asia/Shanghai").to_iso8601_string()[:22]


def logConfig(log_file="logs/default.log", rotation="10 MB", level="DEBUG", mode=0):
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
            " [ <level>{level: <8}</level>] "
            + "<green>🧀 </green>"
            + "<level>{message}</level>"
        )
    if mode == 1:
        style = (
            "<green>{extra[datetime]}</green>"
            + " [ <level>{level: <8}</level>] "
            + "<green>🧀 </green>"
            + "<level>{message}</level>"
        )
    else:
        style = (
            "<green>{extra[datetime]}</green>"
            + " [ <level>{level: <8}</level>] "
            + "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
            + "<green>🧀 </green>"
            + "<level>{message}</level>"
        )
    # alternative ➲ ⛏ ☄ ➜ ♻ ✨
    logger.configure(patcher=set_datetime)
    logger.add(sys.stderr, level=level, colorize=True, format=style)
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

