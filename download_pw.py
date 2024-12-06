import time
import json
import hashlib
import os
from pathlib import Path
from tqdm.rich import tqdm
import tomllib
import threading
import platform
import ipdb
from playwright.sync_api import sync_playwright

import requests
from bs4 import BeautifulSoup
import sqliteDB

# import mQueue
import queue
import sqlite3
from util import (
    logConfig,
    logger,
    lumos,
    check_folder,
    create_hash,
    check_hash,
    check_intact,
    Nox,
)

logConfig("logs/download.log", rotation="10 MB", level="DEBUG", mode=1)


# multithreading semaphore
# if platform.system() == "Windows":
#     max_threads = min(os.cpu_count(), 4)
# else:
#     max_threads = min(os.cpu_count(), 4)

max_threads = 1
semaphore = threading.BoundedSemaphore(max_threads)
TQ = queue.Queue()


MAIN_PATH = None  # default ./downloads
USER = []
MANUAL = []
cookie_path = Path() / "cookies" / "download.json"

## sqlite ##
conn = sqlite3.connect("db.sqlite3")
# mainDB = sqliteDB


def launch():
    if not cookie_check(cookie_path):
        cookie_create(cookie_path)

    for user in USER:
        # 检查目标人物主页，添加queue
        scrapy_home(user)
        # 下载队列中的视频
        download_queue()

    if type(conn) == sqlite3.Connection:
        conn.close()  # for sqlite only


def boot():
    global MAIN_PATH
    global USER
    global MANUAL
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)
    MAIN_PATH = Path(config.get("MAIN_PATH", "./downloads"))
    for user in config["USER"]:
        if user.get("active", True):
            USER.append(user)
    MANUAL = config["MANUAL"]
    sqliteDB.init_db(conn, table="douyin")
    # print(USER)


def cookie_create(cookie_path=Path() / "cookies" / "download.json"):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        # page.set_viewport_size({"width": 1280, "height": 720})
        page.goto("https://www.douyin.com/")
        # Scan RQ Manual
        time.sleep(5)
        while page.locator(".semi-button-primary").first.inner_text() == "登录":
            logger.warning("Please Login~")
            time.sleep(3)
        page.locator("#douyin-header-menuCt").get_by_role("link").nth(-1).hover()
        time.sleep(1)
        nick_name = (
            page.locator(".userMenuPanelShadowAnimation")
            .nth(-1)
            .inner_text()
            .split("\n")[0]
        )
        logger.info(f"Nickname:{nick_name}")
        time.sleep(1)
        if len(context.cookies()) >= 47:
            storage = context.storage_state(path=cookie_path)
            logger.success("Login success. Save to state.json.")
        else:
            storage = context.storage_state(path=cookie_path)
            logger.warning("Login fail. Use anonymous mode.")
        browser.close()


def cookie_check(cookie_path=Path() / "cookies" / "download.json"):
    if not cookie_path.exists():
        return Nox(-1)
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(storage_state=Path(cookie_path))
        page = context.new_page()
        # page.set_viewport_size({"width": 1280, "height": 720})
        page.goto("https://www.douyin.com/")
        time.sleep(7)
        if page.locator(".semi-button-primary").first.inner_text() == "登录":
            logger.debug("login fail")
            if cookie_path.exists():
                logger.warning(f"cookie out of time delete. {cookie_path}")
                magic = f"rm {cookie_path}"
                if len(magic) < 5:
                    logger.error("rm action")
                    raise
                lumos(magic)
            return Nox(-1)
        else:
            logger.debug("login success")
            page.locator("#douyin-header-menuCt").get_by_role("link").nth(-1).hover()
            time.sleep(1)
            nick_name = (
                page.locator(".userMenuPanelShadowAnimation")
                .nth(-1)
                .inner_text()
                .split("\n")[0]
            )
            logger.info(f"Nickname:{nick_name}")
            time.sleep(1)
            return Nox(0)

def scrapy_home(user):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(storage_state=Path(cookie_path))
        page = context.new_page()
        
        video_online_vid_list = scrapy_video(page, user["url"])
        folder = MAIN_PATH / user["symbol"]
        if not check_folder(folder, True):
            logger.error(f"No Folder {folder}")
            return
        for vid in video_online_vid_list:
            v_path = folder / f"{user["symbol"]}.{vid}.mp4"
            result = sqliteDB.fetch_db_by_vid(conn, "douyin", vid=vid)
            el = {}
            el["vid"] = vid
            el["symbol"] = user["symbol"]
            el["nickname"] = user["nickname"]
            el["md5"] = ""
            if result:
                if check_hash(v_path, result["md5"]):
                    logger.debug(f"Hash Match ID {vid}")
                    continue
                elif result["md5"] == "":
                    logger.debug(f"Hash Empty ID {vid}")
                else:
                    logger.error(f"Hash Abort ID {vid}")
            else:
                sqliteDB.insert_db(conn, "douyin", el)
            logger.info(f"MQ for ID {vid}")
            TQ.put(vid)

        # 关闭浏览器
        browser.close()

def scrapy_video(page, user_url):
    user_url = pretty_user(user_url)
    page.goto(user_url)
    # page.pause()
    time.sleep(4)
    logger.info(f"Title: {page.title()} \n URL: {user_url}")
    if "验证码中间页" in page.title():
        logger.info("Error 验证码")
        raise
    video_count = 0
    retry_flag = 0
    while True:
        new_count = video_count
        video_els = page.locator(".TyuBARdT")
        new_count = video_els.count()
        if new_count == video_count:
            logger.debug("same length videos")
            if retry_flag <= 2:
                retry_flag += 1
            else:
                break
        else:
            video_count = new_count
        page.locator(".z_YvCWYy").hover()
        time.sleep(0.2)
        page.mouse.wheel(0, 1000)
        time.sleep(1)
    out_vid_list = []
    for index in range(video_els.count()):
        video_url = video_els.nth(index).get_attribute("href")
        if video_url.startswith("/video/"):
            vid = video_url.split("/")[-1]
            out_vid_list.append(vid)
    return out_vid_list


def pretty_user(user_url):
    if user_url.startswith("http"):
        return user_url
    elif user_url.startswith("http"):
        return "https://www.douyin.com/user" + user_url
    else:
        return "https://www.douyin.com/user/" + user_url


def download_queue():
    if max_threads == 1:
        pbar = tqdm(total=TQ.qsize())
        while not TQ.empty():
            vid = TQ.get()
            v = sqliteDB.fetch_db_by_vid(conn, "douyin", vid)
            vid = v["vid"]
            symbol = v["symbol"]
            folder = MAIN_PATH / v["symbol"]
            v_path = folder / f"{symbol}.{vid}.mp4"
            # check_folder(folder)
            if download_by_dlpanda(vid, symbol, folder):
                md5sum = create_hash(v_path)
                sqliteDB.update_db_by_vid(conn, "douyin", vid, {"md5": md5sum})
            pbar.update(1)
        pbar.close()
    else:
        threads = []
        pbar = tqdm(total=TQ.qsize())
        while not TQ.empty():
            vid = TQ.get()
            v = sqliteDB.fetch_db_by_vid(conn, "douyin", vid)
            # vid = v["vid"]
            symbol = v["symbol"]
            folder = MAIN_PATH / v["symbol"]
            v_path = folder / f"{symbol}.{vid}.mp4"
            # check_folder(folder)
            t = threading.Thread(
                target=multi,
                args=(vid, symbol, folder, semaphore, pbar),
            )
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        pbar.close()


def download_manual(vid_list=[]):
    symbol = "_"
    logger.info("Download Manual")
    folder = MAIN_PATH / "TEMP"
    check_folder(folder)

    for vid in tqdm(vid_list):
        if check_intact(folder / f"{symbol}.{vid}.mp4"):
            continue
        download_by_dlpanda(vid, symbol, folder)


def multi(vid, symbol="_", folder=Path("./downloads"), semaphore=None, pbar=None):
    with semaphore:
        v_path = folder / f"{symbol}.{vid}.mp4"
        if download_by_dlpanda(vid, symbol, folder):
            md5sum = create_hash(v_path)
            if type(conn) == sqlite3.Connection:
                connM = sqlite3.connect("db.sqlite3")
                # sqliteDB.delete_db_by_vid(connM, vid, table="queue")
                sqliteDB.update_db_by_vid(connM, "douyin", vid, {"md5": md5sum})
                connM.close()
            else:
                sqliteDB.update_db_by_vid(conn, "douyin", vid, {"md5": md5sum})
        pbar.update(1)
        return


def download_by_dlpanda(vid, symbol="", path=Path("./downloads")):
    video_url = "https://www.douyin.com/video/" + vid
    dlpre_url = "https://dlpanda.com/?url="
    dltoken_url = "&token=G7eRpMaa"
    dlpanda_url = dlpre_url + video_url + dltoken_url
    logger.debug("Analysis " + vid)

    r = requests.get(dlpanda_url)
    soup = BeautifulSoup(r.text, "lxml")
    try:
        href_info = soup.find("a", "primary-solid-btn")["href"]
        download_info = soup.find("a", "primary-solid-btn")["download"]
    except:
        logger.error("No video, douyin_url " + video_url)
        logger.error("No video, dlpanda_url " + dlpanda_url)
        return

    source_url = "https://dlpanda.com" + href_info
    logger.debug(source_url)
    target_name_ol = download_info.split("]")[-1]  # remove [DLpanda]
    target_vid_ol = target_name_ol.split(".")[0]
    if target_vid_ol and target_vid_ol != vid:
        logger.error("Fail not same ID " + vid)
        logger.error(source_url)
        logger.error(target_name_ol)
        return

    target_name = f"{symbol}.{vid}.mp4"
    target_path = path / target_name
    cmd = f"curl -s -k -o '{target_path}' '{source_url}'"
    # logger.debug(cmd)
    for num in range(3):
        if num != 0:
            logger.warning(f"Retry \n Retry {num} times for ID {vid}")
        lumos(cmd)
        if check_intact(target_path):
            logger.success(f"Success {vid} ")
            return True
    record_fail(vid, target_name)
    logger.error(f"Fail ID {vid}")
    logger.error(source_url)
    logger.error(target_path)
    return


def record_fail(vid, target_name):
    with open("FailID.txt", "a", encoding="utf-8") as file:
        file.write('"{}",\n'.format(vid))
    with open("Fails.txt", "a", encoding="utf-8") as file:
        file.write("{}\n".format(target_name))


if __name__ == "__main__":
    boot()
    launch()
