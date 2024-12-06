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

cookie_path = Path() / "cookies" / "xhs-nt.json"


def launch():
    if not cookie_check():
        cookie_create()

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(storage_state=Path(cookie_path))
        page = context.new_page()
        dist_folder = Path("dist")
        mp4_list = list(dist_folder.glob("*.mp4"))
        pbar = tqdm(total=len(mp4_list))
        for index, item in enumerate(mp4_list):
            logger.info(f"{item} - Waiting kimiDB")
            title = kimiDB.fetch(
                "收下这份美女,教你卡点舞动起来 , 仿写这个标题，不要标点最多20个字"
            )["data"]
            article = kimiDB.fetch(
                "收下这份美女 ， 模特, 给我一小段小红书文案，简短的"
            )["data"]
            key_list = kimiDB.fetch("收下这份美女 , 模特，给我5个关键词")["data"]
            page.goto("https://creator.xiaohongshu.com/publish/publish?from=menu")
            time.sleep(3)
            # upload file
            upload_file(page, 0, item)
            # magic_text
            magic_text(page, title, article, key_list)
            # pub clock
            tick = pendulum.parse("2024-11-21 15:00:00")
            target_tick = tick.add(hours=1 * index)
            pub_clock(page, str(target_tick))
            # submit
            if page.get_by_role("button", name="发布").count():
                page.get_by_role("button", name="发布").click()
            else:
                page.get_by_role("button", name="定时发布").count()
            time.sleep(1)
            logger.success(f"{item}")
            pbar.update(1)
        pbar.close()


def cookie_create():
    logger.debug("Cookie Create launch")
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://creator.xiaohongshu.com/login")
        time.sleep(5)
        while page.locator(".login-box-container").count():
            logger.warning("Please Login~")
            time.sleep(3)
        time.sleep(1)
        nick_name = page.locator(".name-box").inner_text()
        logger.info(f"Nickname: {nick_name}")
        if len(context.cookies()) >= 16:
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
        page.goto("https://creator.xiaohongshu.com/login")
        time.sleep(5)
        if page.locator(".login-box-container").count():
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
            time.sleep(1)
            nick_name = page.locator(".name-box").inner_text()
            logger.info(f"Nickname: {nick_name}")
            return Nox(0)


def upload_file(page, mode, file_path):
    logger.debug("Upload launch")
    if mode == 0:
        page.locator(".header").get_by_text("上传视频").click()
        page.locator(".upload-wrapper").get_by_role("textbox").set_input_files(
            file_path
        )
        while "修改封面" not in page.locator(".operator").nth(0).inner_text():
            time.sleep(2)
    elif mode == 1:
        page.locator(".header").get_by_text("上传图文").click()
        page.locator(".upload-wrapper").get_by_role("textbox").set_input_files(
            file_path
        )
        time.sleep(3)


def magic_text(page, title, article, keyword_list):
    logger.debug("magic text launch")
    page.locator(".titleInput").locator("input").fill(title)
    if page.locator(".titleInput").locator(".c-input_max").count():
        page.locator(".titleInput").locator("input").press("Backspace")
    page.locator("#quillEditor div").fill(article)
    # keyword
    for item in keyword_list:
        page.locator("#quillEditor div").type("#")
        page.locator("#quillEditor div").type(item)
        time.sleep(2)
        page.keyboard.press("Enter")
    time.sleep(0.5)


def pub_clock(page, pub_dt):
    logger.debug("Pub clock launch")
    pub_str = pub_dt[:16]
    page.locator(".el-radio").get_by_text("定时发布").click()
    time.sleep(0.5)
    page.get_by_placeholder("选择日期和时间").fill(pub_dt[:16])
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
