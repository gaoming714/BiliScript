# -*- coding:utf-8 -*-
"""

"""

import urllib.request
import os
import json
import time
import hashlib
import random
import pendulum
from tqdm import tqdm
from alive_progress import alive_bar, alive_it
from loguru import logger

# package : poetry run pyinstaller dashboard.py --onefile --collect-all grapheme
# action : grapheme for alive_progress

import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ExpC
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile




import requests


# This example requires Selenium WebDriver 3.13 or newe
options = Options()
options.add_argument("-headless")  # headless

driver = webdriver.Firefox(executable_path="geckodriver", options=options)
wait = WebDriverWait(driver, 10)





def login():
    driver.get("https://passport.bilibili.com/login")

    print(driver.title)
    print("Please login \n")

    wait = WebDriverWait(driver, 120)
    first_result = wait.until(
        ExpC.presence_of_element_located((By.CLASS_NAME, "header-entry-mini"))
    )

    print("done")


def launch():
    ticktock = pendulum.now("Asia/Shanghai")
    # print(ticktock)
    print("=> ", ticktock.to_datetime_string())
    user_id = "30978137"
    # video_list = fetch_user(user_id, limit = 30)
    video_list = fetch_user_api(user_id)
    ext_videos(video_list)  # add some special BV _ id
    # print(video_list)

    ## debug
    # video_list = ["BV1oV4y1V7sK","BV1Zm4y1c71h"]
    # box = []

    for bv_id in alive_it(video_list):
        # online, play, like, coin, star, release_time, title = get_data(bv_id)
        # box.append([bv_id, online, play, like, coin, star, release_time, title])
        # bv_dict = get_data(bv_id)
        bv_dict = get_api(bv_id)
        if bv_dict == {} or bv_dict == None:
            print([bv_id, " => skip"])
            continue
        bv_dict["bv_id"] = bv_id
        play_video(bv_id, duration = bv_dict["duration"])
        time.sleep(1)  # for cid api should not be too fast
        # bar()
    # cmd_print(box)
    # # box is  [ { } , { } ]
    # monitor(box)


def fetch_user_api(user_id, limit=30):
    user_url = "https://api.bilibili.com/x/space/arc/search"
    payload = {"mid": user_id, "pn": 1, "ps": 30}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0"
    }
    r = requests.get(user_url, params=payload, headers=headers)
    if r.status_code != 200:
        print("user skip")
        return
    res = r.json()
    if not check_res(res):
        print("user skip")
        return
    vlist = res["data"]["list"]["vlist"]
    video_id_list = []
    for video_item in vlist:
        video_id_list.append(video_item["bvid"])
    return video_id_list


def ext_videos(video_list):
    ext_list = ["BV1WT411K7Ti", "BV1uT411P7Nq"]
    for id_item in ext_list:
        if id_item not in video_list:
            video_list.append(id_item)


def play_video(bv_id, duration = 15):
    video_url = "https://www.bilibili.com/video/" + bv_id
    driver.get(video_url)
    ticktock = pendulum.now("Asia/Shanghai")
    time.sleep(duration * 0.1)
    # action()
    time.sleep(duration * 0.8)
    return


def get_api(bv_id):
    ticktock = pendulum.now("Asia/Shanghai")

    view_url = "http://api.bilibili.com/x/web-interface/view"
    payload = {"bvid": bv_id}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0"
    }
    r = requests.get(view_url, params=payload, headers=headers)
    if r.status_code != 200:
        print("view skip")
        return
    res = r.json()
    if not check_res(res):
        print("view skip")
        return
    cid = res["data"]["cid"]  # maybe not stable
    title_str = res["data"]["title"][:30]
    rtime_num = res["data"]["pubdate"]
    rtime = pendulum.from_timestamp(rtime_num, tz="Asia/Shanghai")
    duration_num = res["data"]["duration"]
    play = res["data"]["stat"]["view"]
    like = res["data"]["stat"]["like"]
    coin = res["data"]["stat"]["coin"]
    star = res["data"]["stat"]["favorite"]
    his_rank = res["data"]["stat"]["his_rank"]
    now_rank = res["data"]["stat"]["now_rank"]
    evaluation_str = res["data"]["stat"]["evaluation"]
    # print(online)
    # print(his_rank)
    # print(now_rank)
    # print(evaluation_str)
    stay, rate = stay_rate(play, like, coin, star)

    # online data
    online_url = "http://api.bilibili.com/x/player/online/total"
    payload = {"bvid": bv_id, "cid": cid}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0"
    }
    r = requests.get(online_url, params=payload, headers=headers)
    if r.status_code != 200:
        print("online skip")
        return
    res = r.json()
    if not check_res(res):
        print("online skip")
        return
    online_str = res["data"]["total"]
    online = pretty_num(online_str)

    output_dict = {
        "online": online - 1,
        "play": play,
        "like": like,
        "coin": coin,
        "star": star,
        "stay": stay,
        "rate": rate,
        "duration": duration_num,
        "rtime": rtime.to_datetime_string(),  # to datetime str
        "mtime": ticktock.to_datetime_string(),  # to datetime str
        "title": title_str,
    }
    return output_dict


def stay_rate(play_num, like_num, coin_num, star_num):
    if play_num == 0:
        return 0, 0

    stay_num = like_num + star_num + coin_num * 5
    rate_num = stay_num / play_num

    return stay_num, rate_num


def pretty_num(origin_str):
    if origin_str in [" ", "  ", "-", "点赞", "投币", "收藏"]:
        output_num = 0
    elif not origin_str.isdigit():
        tmp_str = origin_str[:-1]
        output_num = int(float(tmp_str) * 10000)
    else:
        output_num = int(origin_str)
    return output_num


def check_res(json_dict):
    if type(json_dict) != type({}):
        print(json_dict)
        # raise
        return
    if "code" not in json_dict or "data" not in json_dict:
        print(json_dict)
        # raise
        return
    if json_dict["code"] != 0:
        print(json_dict)
        # raise
        return
    return True


def lumos(cmd):
    # print(cmd)
    # res = 0
    print("CMD ➜ " + cmd)
    res = os.system(cmd)
    return res

def action():
    hasher = hashlib.md5()
    hasher.update(url.encode('utf-8'))
    hashhex = hasher.hexdigest()

    like_els = driver.find_elements(By.XPATH, "/html/body/div[2]/div[4]/div[1]/div[3]/div[1]/span[1]")
    if like_els == []:
        return
    like_el = like_els[0]
    # if like_el.get_attribute("class") != "like on":
    #     try:
    #         like_el.click()
    #     except:
    #         return
    #     # print("Debug ➜ like + 1")
    # else:
    #     # have liked
    #     # print("Debug ➜ like ====  else")
    #     return
    
    ## comment
    # time.sleep(1)
    # driver.get(url)
    # time.sleep(3)
    try:
        input_el = driver.find_element(By.CLASS_NAME, "reply-box-textarea")
        input_el.click()

    except:
        return
    # if like_el.get_attribute("class") != "like on":
    #     like_el.click()

    try:
        input_el.send_keys("已赞，感谢点赞 ↓↓↓ 视频 ※ 感谢 =>  " + hashhex)
        input_el.send_keys(Keys.ENTER)
        input_el.send_keys("https://www.bilibili.com/video/BV1oT411K7yS/")
        input_el.send_keys(Keys.ENTER)
        input_el.send_keys("https://www.bilibili.com/video/BV1ND4y1i7Z5/")
        input_el.send_keys(Keys.ENTER)
        input_el.send_keys("https://www.bilibili.com/video/BV17W4y1B7yN/")
        time.sleep(3)
        send_el = driver.find_element(By.CLASS_NAME, "send-text")
        send_el.click()
        # print("Debug ➜ comment + 1")
    except:
        # print("Debug ➜ comment ====   else")
        return

if __name__ == "__main__":
    # login()
    # comment("BV1XS4y1s7HF")
    # launch()
    # login()
    while True:
        launch()
        time.sleep(60)
    # for item in range(1000):
    #     print("=====================================")
    #     launch()
