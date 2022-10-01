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
# action : grapheme


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ExpC

SRC_audio = "inputAudio"
SRC_video = "inputVideo"
DIST = "output"

FILE_list = None

best_online = 0
best_moment = None

#This example requires Selenium WebDriver 3.13 or newe
options = Options()
options.add_argument('-headless') # headless
driver = webdriver.Firefox(executable_path='geckodriver', options=options)
wait = WebDriverWait(driver, 10)


def load():
    pass
    # global SRC
    # global DIST
    # global CURL_cmd
    # global FILE_list
    # data = None
    # with open("info.json", 'r', encoding='utf-8') as f:
    #     data = json.load(f)
    #     SRC = data["src"]
    #     DIST = data["dist"]
    #     CURL_cmd = data["curlCmd"]
    #     FILE_list = data["infoArr"]

def login():
    driver.get("https://passport.bilibili.com/login")

    print(driver.title)
    print("Please login \n")

    wait = WebDriverWait(driver, 120)
    first_result = wait.until(ExpC.presence_of_element_located((By.CLASS_NAME, "header-entry-mini")))

    print("done")


def launch():
    global best_online
    global best_moment
    ticktock = pendulum.now("Asia/Shanghai")
    # print(ticktock)
    print("=> ", ticktock.to_datetime_string())
    user_id = "30978137"
    video_list = fetch_user(user_id, limit = 20)
    box = []
    flag = " "
    total_online = 0

    pretty = "\n"
    # with alive_bar(len(video_list)) as bar:
    for bv_id in alive_it(video_list):
        online, play, like, star, release_time, title = get_data(bv_id)
        box.append([bv_id, online, play, like, star, release_time, title])
        # bar()
    for item in box:
        bv_id, online, play, like, star, release_time, title  = item
        if online == "" or play == "" or like == "" or star == "":
            print(bv_id, " => skip")
            continue
        if online.isdigit():
            online_num = int(online) - 1
            total_online += online_num
            online  = str(online_num)
            if online_num > 999:
                online = "^"   + online
            elif online_num > 99:
                online = "$ "   + online
            elif online_num > 50:
                online = "@  "  + online
            elif online_num > 24:
                online = "&  "  + online
            elif online_num > 9:
                online = "+  "  + online
            elif online_num > 0:
                online = "    " + online
            elif online_num == 0:
                online = "     "
            else:
                online = "ERROR"
        else:
            online = " "
        stay_num, rate_num = stay_rate(play, like, star)
        stay = str(stay_num)
        rate = "{:.2f} %".format(rate_num * 100)
        # pretty = pretty + flag + online + "\t" + play + "\t" + stay + "\t" +  rate + "\t" + release_time + "  " + bv_id + " " + title + "\n" 
        pretty = pretty + flag + online + "\t" + play + "\t" + stay + "\t" +  rate + "\t" + release_time + "  " + title + "\n" 
        # if flag != " ":
        #     pretty = pretty + "\t\t\t\t" + title + "\n"
    pretty = pretty + "Total => " + str(total_online) + "\t"
    if total_online > best_online:
        best_online = total_online
        best_moment = ticktock.to_datetime_string()
    if best_moment != None:
        pretty = pretty + "Best => " + str(best_online) + "\t" + best_moment + "\t"
    pretty = pretty + "\n"
    logger.debug(pretty)
        # print(online, "\t",  play, "\t", star, "\t", release_time, "\t", title)


def fetch_user(user_id, limit = None):
    # return all videos(bv_id) in this user
    user_url = "https://space.bilibili.com/" + user_id + "/video"
    driver.get(user_url)

    # print("fetch_user")
    # print(driver.title)

    time.sleep(2)

    video_els = driver.find_elements(By.CLASS_NAME, "small-item")
    video_id_list = []
    for video_el in video_els:
        video_id = video_el.get_attribute('data-aid')
        video_id_list.append(video_id)
    if limit != None:
        video_id_list = video_id_list[:limit]
    return video_id_list

def get_data(bv_id):
    video_url = "https://www.bilibili.com/video/" + bv_id
    driver.get(video_url)
    time.sleep(1)

    first_result = wait.until(ExpC.presence_of_element_located((By.CLASS_NAME, "bpx-player-sending-bar")))
    time.sleep(2)
    try:
        online_el = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[1]/div[2]/div[2]/div/div/div[1]/div[2]/div/div[1]/div[1]/b")
        online_str = online_el.text
        play_el = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[1]/div[1]/div/div/span[1]")
        play_str = play_el.text
        like_el = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[1]/div[3]/div[1]/span[1]/span")
        like_str = like_el.text
        star_el = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[1]/div[3]/div[1]/span[3]/span")
        star_str = star_el.text
        time_el = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[1]/div[1]/div/div/span[3]/span/span")
        time_str = time_el.text
        title_el = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[1]/div[1]/h1")
        title_str = title_el.text
        title_str = title_str[:30]
    except:
        return "","","","","",""

    # time.sleep(1)
    if like_str == "点赞":
        like_str = "0"
    if star_str == "收藏":
        star_str = "0"

    return online_str, play_str, like_str, star_str, time_str, title_str

def stay_rate(play_str, like_str, star_str):
    play_num = pretty_num(play_str)
    like_num = pretty_num(like_str)
    star_num = pretty_num(star_str)
    stay_num = like_num + star_num
    rate_num = stay_num / play_num

    return stay_num , rate_num

def pretty_num(origin_str):
    if not origin_str.isdigit():
        tmp_str = origin_str[:-1]
        output_num = int(float(tmp_str) * 10000)
    else:
        output_num = int(origin_str)
    return output_num


def lumos(cmd):
    # print(cmd)
    # res = 0
    print("CMD ➜ " + cmd)
    res = os.system(cmd)
    return res




if __name__ == '__main__':
    # login()
    # comment("BV1XS4y1s7HF")

    # login()
    while True:
        launch()
        time.sleep(10)
    # for item in range(1000):
    #     print("=====================================")
    #     launch()
