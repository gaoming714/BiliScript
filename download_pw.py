import time
import json
import hashlib
import os
from pathlib import Path
from tqdm.rich import tqdm
import tomlkit
import threading
import platform
import ipdb
from playwright.sync_api import sync_playwright

import requests
from bs4 import BeautifulSoup
import boxDB
import jsonDB
import sqliteDB
import mQueue
import queue
import sqlite3
from util import (
    logConfig,
    logger,
    lumos,
    check_folder,
    show_local,
    create_hash,
    check_hash,
    check_intact,
)

logConfig("logs/download.log", rotation="10 MB", level="DEBUG", lite=True)


# multithreading semaphore
# if platform.system() == "Windows":
#     max_threads = min(os.cpu_count(), 4)
# else:
#     max_threads = min(os.cpu_count(), 4)

max_threads = 1
semaphore = threading.BoundedSemaphore(max_threads)
TQ = queue.Queue()
# MQ = []

# import warnings
# from tqdm.std import TqdmExperimentalWarning
# warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)
MAIN_PATH = Path("./downloads")
USER = []
MANUAL = []


## python pure BOX(dict) ##
# conn = BOX
# mainDB = sqliteDB

## DB json ##
# conn = Path("db.json")
# mainDB = sqliteDB

## sqlite ##
conn = sqlite3.connect("db.sqlite3")
mainDB = sqliteDB

def launch():
    if not Path("state.json").exists():
        store_cookie()
    # download_manual(MANUAL)
    # download_queue()
    fetch_user()

    # download_queue()
    # print(BOX)
    if type(conn) == sqlite3.Connection:
        conn.close()  # for sqlite only


def boot():
    global MAIN_PATH
    global USER
    global MANUAL
    with open("config.toml", "r", encoding="utf-8") as f:
        config = tomlkit.parse(f.read())
    MAIN_PATH = Path(config.get("MAIN_PATH", "./downloads"))
    for user in config["USER"]:
        if not user.get("skip", False):
            USER.append(user)
    MANUAL = config["MANUAL"]


def store_cookie():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        # page.set_viewport_size({"width": 1280, "height": 720})
        page.goto("https://www.douyin.com/")
        # page.wait_for_selector("#svg_icon_avatar")

        # Scan RQ Manual
        logger.warning("Please Login~")
        time.sleep(100)
        # for i in range(200):
        #     element = page.query_selector("#svg_icon_avatar")
        #     if element is None:
        #         # Login success
        #         print("Login success")
        #         break
        #     time.sleep(1)

        if len(context.cookies()) >= 47:
            storage = context.storage_state(path="state.json")
            logger.success("Login success. Save to state.json.")
        else:
            storage = context.storage_state(path="state.json")
            logger.warning("Login fail. Use anonymous mode.")
        browser.close()


def fetch_user():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(storage_state=Path("state.json"))
        page = context.new_page()
        for user in USER:
            video_online_vid_list = scrapy_video(page, user["url"])
            folder = MAIN_PATH / user["symbol"]
            if not check_folder(folder, True):
                logger.error("No Folder {}".format(folder))
                continue
            for vid in video_online_vid_list:
                v_path = folder / "{}.{}.mp4".format(user["symbol"], vid)
                result = mainDB.fetch_db_by_vid(conn, vid)
                el = {}
                el["vid"] = vid
                el["symbol"] = user["symbol"]
                el["nickname"] = user["nickname"]
                el["md5"] = ""
                if result:
                    if check_hash(v_path, result["md5"]):
                        logger.debug("Hash match ID {}".format(vid))
                        continue
                    elif result["md5"] == "":
                        logger.debug("Empty ID {}".format(vid))
                    else:
                        logger.error("Abort ID {}".format(vid))
                else:
                    mainDB.insert_db(conn, el)
                logger.info("MQ for ID {}".format(vid))
                TQ.put(vid)
                # if vid not in MQ:
                #     MQ.append(vid)

            # 下载队列中的视频
            download_queue()
            # 如果需要显示队列长度，可以取消下面的注释
            # logger.info(f"当前下载队列长度: {len(MQ)}/20")

        # 关闭浏览器
        browser.close()

    # 如果需要打印最终的下载队列，可以取消下面的注释
    # print("最终下载队列:")
    # print(MQ)


def scrapy_video(page, user_url):
    user_url = pretty_user(user_url)
    page.goto(user_url)
    # page.pause()
    time.sleep(4)
    logger.info("Title: {} \n URL: {}".format(page.title(), user_url))
    if "验证码中间页" in page.title():
        raise
    video_count = 0
    retry_flag = 0
    while True:
        new_count = video_count
        video_els = page.locator(".TyuBARdT")
        new_count = video_els.count()
        if new_count == video_count:
            if retry_flag <= 2:
                retry_flag += 1
            else:
                break
        else:
            video_count = new_count
        page.locator(".z_YvCWYy").hover()
        time.sleep(0.2)
        page.mouse.wheel(0,1000)
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
            v = mainDB.fetch_db_by_vid(conn, vid)
            vid = v["vid"]
            symbol = v["symbol"]
            folder = MAIN_PATH / v["symbol"]
            v_path = folder / "{}.{}.mp4".format(symbol, vid)
            # check_folder(folder)
            if download_by_dlpanda(vid, symbol, folder):
                md5sum = create_hash(v_path)
                mainDB.update_db_by_vid(conn, vid, {"md5": md5sum})
            pbar.update(1)
        pbar.close()
    else:
        threads = []
        pbar = tqdm(total=TQ.qsize())
        while not TQ.empty():
            vid = TQ.get()
            v = mainDB.fetch_db_by_vid(conn, vid)
            # vid = v["vid"]
            symbol = v["symbol"]
            folder = MAIN_PATH / v["symbol"]
            v_path = folder / "{}.{}.mp4".format(symbol, vid)
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
        if check_intact(folder / "{}.{}.mp4".format(symbol, vid)):
            continue
        download_by_dlpanda(vid, symbol, folder)



def multi(vid, symbol="_", folder=Path("./downloads"), semaphore=None, pbar=None):
    with semaphore:
        v_path = folder / "{}.{}.mp4".format(symbol, vid)
        if download_by_dlpanda(vid, symbol, folder):
            md5sum = create_hash(v_path)
            if type(conn) == sqlite3.Connection:
                connM = sqlite3.connect("db.sqlite3")
                # mainDB.delete_db_by_vid(connM, vid, table="queue")
                mainDB.update_db_by_vid(connM, vid, {"md5": md5sum})
                connM.close()
            else:
                mainDB.update_db_by_vid(conn, vid, {"md5": md5sum})
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

    target_name = "{}.{}.mp4".format(symbol, vid)
    target_path = path / target_name
    cmd = "curl -s -k -o '{}' '{}'".format(target_path, source_url)
    # logger.debug(cmd)
    for num in range(3):
        if num != 0:
            logger.warning("Retry \n Retry {} times for ID {}".format(num, vid))
        lumos(cmd)
        if check_intact(target_path):
            logger.success("Success {} ".format(vid))
            return True
    record_fail(vid, target_name)
    logger.error("Fail ID {}".format(vid))
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
