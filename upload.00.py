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
import click
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
        if Pooh.get("debug", False):
            browser = p.firefox.launch(headless=False)
        else:
            browser = p.firefox.launch(headless=True)
        context = browser.new_context(storage_state=Path(cookie_path))
        page = context.new_page()
        dist_folder = Path("dist")
        mp4_list = list(dist_folder.glob("*.mp4"))
        pbar = tqdm(total=len(mp4_list))
        for index, item in enumerate(mp4_list):
            logger.info(f"{item} - Waiting kimiDB")
            page.goto(
                "https://member.bilibili.com/platform/upload/video/frame?page_from=creative_home_top_upload"
            )
            title = kimiDB.fetch(
                "这是在健身？好努力的表情 Powered by 野生的宝可梦 , 仿写这个标题，要风趣幽默"
            )
            key_list = kimiDB.fetch(
                "这是在健身？ Powered by 野生的宝可梦 , 给我5个关键词"
            )
            # upload file
            upload_file(page, 0, item)
            # magic_text
            magic_text(page, title, "article", key_list)
            # pub clock
            tick = pendulum.parse("2024-12-13 06:00:00")
            target_tick = tick.add(hours=3 * index)
            pub_clock(page, target_tick)
            # submit
            page.locator(".submit-add").click()
            time.sleep(1)
            try:
                page.get_by_role("button", name="再投一个")
                print(f"Button 再投一个 appeared.")
            except:
                # 如果超时未出现，抛出异常
                raise RuntimeError(f"Button 再投一个 did not appear within 30s.")
            logger.success(f"{item}")
            pbar.update(1)
        pbar.close()


def cookie_create():
    logger.debug("Cookie Create launch")
    with sync_playwright() as p:
        if Pooh.get("debug", False):
            browser = p.firefox.launch(headless=False)
        else:
            browser = p.firefox.launch(headless=True)
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
        if Pooh.get("debug", False):
            browser = p.firefox.launch(headless=False)
        else:
            browser = p.firefox.launch(headless=True)
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


@click.command()
@click.option('--debug', is_flag=True, help="Enable debug mode")
def cli(debug):
    global Pooh
    boot()
    Pooh["debug"] = debug
    if debug:
        logger.info("debug mode")
    launch()

if __name__ == "__main__":
    cli()
    # boot()
    # launch()
