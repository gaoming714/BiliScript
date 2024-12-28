import time
import re
from pathlib import Path
import pendulum
import random
from tqdm.rich import tqdm
from playwright.sync_api import sync_playwright
import ipdb
from tenacity import retry, stop_after_attempt
import requests

import tomllib
import kimiDB

from util import logConfig, logger, lumos, Nox

logConfig("logs/default.log", rotation="10 MB", level="DEBUG", mode=1)

Pooh = {}

cookie_path = Path() / "cookies" / "bilibili_slaver.json"
cookie_path = Path() / "cookies" / "bilibili_fang.json"


def launch():
    if not cookie_check():
        cookie_create()
    bvid_list = fetch_homepage(mid=30978137)


    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(storage_state=Path(cookie_path))
        page = context.new_page()
        ipdb.set_trace()
        # pbar = tqdm(total=len(bvid_list))
        for index, item in enumerate(bvid_list):
            logger.info(f"{item}")
            page.goto(
                f"https://www.bilibili.com/video/{item}/"
            )
            time.sleep(3)
            page.locator("#bilibili-player video").click()
            time.sleep(1)
            if page.locator(".video-like.on").count():
                logger.debug("已经点赞")
                continue
            else:
                page.locator(".video-like").click()
                title = page.locator(".video-info-title").inner_text()
                time.sleep(80)
                continue
                logger.debug(f"title: {title}")
                res = kimiDB.fetch(f"这里是标题：{title}, 参考这个标题，提出一个简短的引战话题")
                logger.debug(res)
                page.get_by_placeholder("发个友善的弹幕见证当下").click()
                time.sleep(2)
                page.get_by_placeholder("发个友善的弹幕见证当下").fill(res)
                time.sleep(2)
                page.get_by_text("发送", exact=True).click()
                # page.mouse.wheel(0, 1000)
                time.sleep(0.5)
                page.locator("#commentbox  #input").first.click()
                page.locator("#commentbox  #input").first.fill(f"{res} \n这里留言给你发脸换资源")
                time.sleep(1)
                page.get_by_role("button", name="发布").click()
                time.sleep(10)


        # dist_folder = Path("dist")
        # mp4_list = list(dist_folder.glob("*.mp4"))
        # pbar = tqdm(total=len(mp4_list))
        # for index, item in enumerate(mp4_list):
        #     logger.info(f"{item} - Waiting kimiDB")
        #     title = kimiDB.fetch(
        #         "这一只小小酥请收下 卡点美女 Powered by 野生的宝可梦 , 仿写这个标题"
        #     )
        #     key_list = kimiDB.fetch(
        #         "这一只小小酥请收下 卡点美女 Powered by 野生的宝可梦 , 给我5个关键词"
        #     )
        #     page.goto(
        #         "https://member.bilibili.com/platform/upload/video/frame?page_from=creative_home_top_upload"
        #     )
        #     time.sleep(2)
        #     # upload file
        #     upload_file(page, 0, item)
        #     # magic_text
        #     magic_text(page, title, "article", key_list)
        #     # pub clock
        #     tick = pendulum.parse("2024-11-21 15:00:00")
        #     target_tick = tick.add(hours=1 * index)
        #     pub_clock(page, str(target_tick))
        #     # submit
        #     page.locator(".submit-add").click()
        #     logger.success(f"{item}")
        #     pbar.update(1)
        # pbar.close()


def cookie_create():
    logger.debug("Cookie Create launch")
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.bilibili.com")
        logger.warning("Please Login~")
        time.sleep(3)
        while page.locator(".header-login-entry").count():
            logger.warning("Please Login~")
            time.sleep(3)
        page.locator(".header-entry-mini").hover()
        time.sleep(1)
        nick_name = page.locator('a.nickname-item').inner_text()
        logger.info(f"Nickname:{nick_name}")
        time.sleep(3)
        if len(context.cookies()) >= 32:
            storage = context.storage_state(path=cookie_path)
            logger.success(f"Login success. Save {cookie_path}")
        else:
            logger.warning("Login fail. Use anonymous mode.")
        browser.close()


def cookie_check():
    logger.debug("Cookie Check launch")
    if not cookie_path.exists():
        return False
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(storage_state=Path(cookie_path))
        page = context.new_page()
        page.goto("https://www.bilibili.com")
        time.sleep(3)
        if page.locator(".header-login-entry").count():
            logger.warning("Not Login")
            if cookie_path.exists():
                logger.warning(f"cookie out of time delete. {cookie_path}")
                magic = f"rm {cookie_path}"
                if len(magic) < 5:
                    logger.error("rm action")
                    raise
                lumos(magic)
            return False
        else:
            page.locator(".header-entry-mini").hover()
            time.sleep(1)
            nick_name = page.locator('a.nickname-item').inner_text()
            logger.info(f"Nickname:{nick_name}")
            time.sleep(0.2)            
            logger.success("login success")
            return True

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
    # cookie_create()
    boot()
    # print(Pooh)
    # raise
    while True:
        launch()
