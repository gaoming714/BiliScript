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

cookie_path = Path() / "cookies" / "bilibili_master.json"


def launch():
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
            )
            key_list = kimiDB.fetch(
                "这一只小小酥请收下 卡点美女 Powered by 野生的宝可梦 , 给我5个关键词"
            )
            page.goto(
                "https://member.bilibili.com/platform/upload/video/frame?page_from=creative_home_top_upload"
            )
            time.sleep(2)
            # upload file
            upload_file(page, 0, item)
            # magic_text
            magic_text(page, title, "article", key_list)
            # pub clock
            tick = pendulum.parse("2024-12-08 06:00:00")
            target_tick = tick.add(hours=1 * index)
            pub_clock(page, target_tick)
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
            ipdb.set_trace()
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
    logger.debug(f"Pub clock launch => {pub_dt}")
    now = pendulum.now("Asia/Shanghai")
    page.locator(".time-switch-wrp").locator(".switch-container").click()
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
    # print(Pooh)
    # raise
    launch()
