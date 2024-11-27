import time
import re
from pathlib import Path
import pendulum
import random
from tqdm.rich import tqdm
from playwright.sync_api import sync_playwright
import pandas as pd
import polars as pl
import ipdb
from tenacity import retry, stop_after_attempt
import requests

import tomllib
import kimiDB

from util import logConfig, logger, lumos, Nox

logConfig("logs/default.log", rotation="10 MB", level="DEBUG", mode=1)

Pooh = {}

cookie_path = Path() / "cookies" / "bilibili.json"


def launch():
    bvid_list = fetch_homepage(mid=30978137)
    logger.success("online video list")
    logger.success(bvid_list)
    panel = []
    for bvid in bvid_list:
        res = fetch_video(bvid=bvid)
        if res:
            panel.append(res.payload)
    # polars
    pl.Config.set_tbl_cols(50)  # 设置显示的最大列数
    pl.Config.set_tbl_rows(200)  # 设置显示的最大行数
    df = pl.DataFrame(panel)
    df = df.with_columns(pl.col("pubdate").dt.convert_time_zone("Asia/Shanghai"))
    df = df.with_columns(pl.col("title").str.slice(0, 10).alias("title"))


    columns = [col for col in df.columns if col != "title"] + ["title"]
    df = df.select(columns)

    # pandas
    # df = pd.DataFrame(panel)
    # df["pubdate"] = df["pubdate"].dt.tz_convert("Asia/Shanghai")
    # df["title"] = df["title"].str[:10]
    # columns = [col for col in df.columns if col != "title"] + ["title"]
    # df = df[columns]
    print(df)
    raise

    # df = df.with_columns(pl.col("pubdate").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S"))
    # df = pd.DataFrame.from_dict(panel, orient="index").reset_index()
    # df.rename(columns={"index": "BVID"}, inplace=True)
    ipdb.set_trace()


    raise
    {"BVIC":{"title":"abc", "desc":"desca","stat":{"view":123,"like":10}}}
    # https://space.bilibili.com/30978137?spm_id_from=333.1007.0.0
    # url = "https://api.bilibili.com/x/space/wbi/acc/info"
    # params = {
    #     "mid": 2,
    #     "wts": 30978137,
    #     "w_rid": "f7b376124782ae8cb42c56fdd69144ed"
    # }
    # response = requests.get(url, params=params)


    if not cookie_check():
        cookie_create()

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(storage_state=Path(cookie_path))
        page = context.new_page()
        dist_folder = Path("dist")
        mp4_list = list(dist_folder.glob("*.mp4"))
        pbar = tqdm(total=len(mp4_list))
        for index, item in enumerate(mp4_list):
            logger.info(f"{item} - Waiting kimiDB")
            title = kimiDB.fetch(
                "这一只小小酥请收下 卡点美女 Powered by 野生的宝可梦 , 仿写这个标题"
            )["data"]
            key_list = kimiDB.fetch(
                "这一只小小酥请收下 卡点美女 Powered by 野生的宝可梦 , 给我5个关键词"
            )["data"]
            page.goto(
                "https://member.bilibili.com/platform/upload/video/frame?page_from=creative_home_top_upload"
            )
            time.sleep(2)
            # upload file
            upload_file(page, 0, item)
            # magic_text
            magic_text(page, title, "article", key_list)
            # pub clock
            tick = pendulum.parse("2024-11-21 15:00:00")
            target_tick = tick.add(hours=1 * index)
            pub_clock(page, str(target_tick))
            # submit
            page.locator(".submit-add").click()
            logger.success(f"{item}")
            pbar.update(1)
        pbar.close()


def cookie_create():
    logger.debug("Cookie Create launch")
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://member.bilibili.com/platform/home/")
        time.sleep(5)
        while page.locator(".login_wp").count():
            logger.warning("Please Login~")
            time.sleep(3)
        # page.locator('#douyin-header-menuCt').get_by_role("link").nth(-1).hover()
        # time.sleep(1)
        # nick_name = page.locator('.userMenuPanelShadowAnimation').nth(-1).inner_text().split('\n')[0]
        # logger.info(f"Nickname:{nick_name}")
        time.sleep(3)
        if len(context.cookies()) >= 47:
            storage = context.storage_state(path=cookie_path)
            logger.success("Login success. Save to state.json.")
        else:
            storage = context.storage_state(path=cookie_path)
            logger.warning("Login fail. Use anonymous mode.")
        browser.close()


def cookie_check():
    logger.debug("Cookie Check launch")
    if not cookie_path.exists():
        return Nox(-1)
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(storage_state=Path(cookie_path))
        page = context.new_page()
        # page.set_viewport_size({"width": 1280, "height": 720})
        page.goto("https://member.bilibili.com/platform/home")
        time.sleep(3)
        if page.locator(".login_wp").count():
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
            # page.locator('#douyin-header-menuCt').get_by_role("link").nth(-1).hover()
            # time.sleep(1)
            # nick_name = page.locator('.userMenuPanelShadowAnimation').nth(-1).inner_text().split('\n')[0]
            # logger.info(f"Nickname:{nick_name}")
            time.sleep(1)
            return Nox(0)


def fetch_homepage(mid=None):
    logger.debug("Fetch home")
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"https://space.bilibili.com/{mid}/video")
        time.sleep(2)

        elem = page.locator("li.small-item a.title")
        vid_list = []
        for index in range(elem.count()):
            href = elem.nth(index).get_attribute("href")
            vid = href.split("/")[-2]
            vid_list.append(vid)
        return vid_list

def fetch_video(bvid=None):
    """
    return data:
        title
        pubdate - dt = pendulum.from_timestamp(timestamp)
        duration
        stat.view
        stat.reply
        stat.like
        stat.favorite
        stat.coin
        stat.share
    """
    url = "https://api.bilibili.com/x/web-interface/view"
    params = {
        "bvid": bvid  # 替换为你要查询的 BV 号
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        # 检查响应状态码
        if response.status_code == 200:
            # 获取 JSON 数据
            data = response.json()["data"]
        else:
            logger.debug(f"请求失败，状态码: {response.status_code}")
    except requests.RequestException as e:
        logger.debug(f"请求出错: {e}")
        return
    res_dict = {}
    res_dict["bvid"] = data["bvid"]
    res_dict["title"] = data["title"]
    res_dict["pubdate"] = pendulum.from_timestamp(data["pubdate"], tz="Asia/Shanghai")
    res_dict["duration"] = data["duration"]
    res_dict["view"] = data["stat"]["view"]
    res_dict["reply"] = data["stat"]["reply"]
    res_dict["like"] = data["stat"]["like"]
    res_dict["favorite"] = data["stat"]["favorite"]
    res_dict["coin"] = data["stat"]["coin"]
    res_dict["share"] = data["stat"]["share"]
    return Nox(0, res_dict)


def upload_file(page, mode, file_path):
    logger.debug("Upload launch")
    if mode == 0:
        page.locator(".bcc-upload-wrapper").locator("input").set_input_files(file_path)
        # finish
        while "上传完成" not in page.locator(".drag-list").inner_text():
            time.sleep(2)
        time.sleep(5)
    elif mode == 1:
        pass
        time.sleep(3)


def magic_text(page, title, article, keyword_list):
    logger.debug("Magic text launch")
    page.locator(".video-title").locator(".input-val").fill(title)
    # if page.locator(".titleInput").locator(".c-input_max").count():
    #     page.locator(".titleInput").locator("input").press("Backspace")
    # page.locator("#post-textarea").fill(article)

    # label
    for item in keyword_list:
        page.locator(".tag-container").locator("input").type(item)
        time.sleep(0.5)
        page.keyboard.press("Enter")
        time.sleep(0.5)
    time.sleep(0.5)

    # keyword
    # for item in keyword_list:
    #     page.locator("#post-textarea").type("#")
    #     page.locator("#post-textarea").type(item)
    #     time.sleep(0.5)
    #     page.keyboard.press("Tab")
    # time.sleep(0.5)


def pub_clock(page, pub_dt):
    logger.debug("Pub clock launch")
    pub_dt = pendulum.parse(pub_dt)
    now = pendulum.now("Asia/Shanghai")

    page.locator(".time-switch-wrp").locator(".switch-container").click()
    time.sleep(0.5)
    # page.locator(".date-picker-date").locator("p").evaluate(f"element => element.textContent = '{pub_tuple[0]}'")
    # time.sleep(0.5)
    # page.locator(".date-picker-timer").locator("p").evaluate(f"element => element.textContent = '{pub_tuple[1]}'")
    # time.sleep(0.5)
    time.sleep(0.5)
    page.locator(".date-picker-date").click()
    time.sleep(0.5)
    if pub_dt.month != now.month:
        page.locator(".date-picker-nav-wrp").locator(".next-btn-month").click()
        time.sleep(0.5)
    page.locator(".date-picker-body-wrp").get_by_text(
        str(pub_dt.day), exact=True
    ).click()
    time.sleep(0.5)
    page.locator(".date-picker-timer").click()
    time.sleep(0.5)
    page.locator(".time-picker-panel-select-wrp").nth(0).get_by_text(
        f"{pub_dt.hour:02}", exact=True
    ).click()
    time.sleep(0.5)
    page.locator(".time-picker-panel-select-wrp").nth(1).get_by_text(
        f"{pub_dt.minute:02}", exact=True
    ).click()
    time.sleep(0.5)
    page.locator(".date-picker-timer").click()
    time.sleep(0.5)


def boot():
    global Pooh
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)
    Pooh = config
    kimiDB.boot(Pooh.get("MOONSHOT_API_KEY", None))


if __name__ == "__main__":
    boot()
    # logger.debug(Pooh)
    # raise
    launch()
