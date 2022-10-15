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

import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ExpC

import requests

SRC_audio = "inputAudio"
SRC_video = "inputVideo"
DIST = "output"

FILE_list = None

df = None



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
    ticktock = pendulum.now("Asia/Shanghai")
    # print(ticktock)
    print("=> ", ticktock.to_datetime_string())
    user_id = "30978137"
    video_list = fetch_user(user_id, limit = 30)
    ext_videos(video_list)   # add some special BV _ id
    # print(video_list)
    box = []

    for bv_id in alive_it(video_list):
        # online, play, like, coin, star, release_time, title = get_data(bv_id)
        # box.append([bv_id, online, play, like, coin, star, release_time, title])
        # bv_dict = get_data(bv_id)
        bv_dict = get_api(bv_id)
        if bv_dict == {}:
            print([bv_id," => skip"] )
            continue
        bv_dict["bv_id"] = bv_id
        box.append(bv_dict)
        # bar()
    cmd_print(box)
    # box is  [ { } , { } ]
    monitor(box)


def fetch_user(user_id, limit = None):
    # return all videos(bv_id) in this user
    user_url = "https://space.bilibili.com/" + user_id + "/video"
    driver.get(user_url)

    # print("fetch_user")
    # print(driver.title)

    time.sleep(5)

    video_els = driver.find_elements(By.CLASS_NAME, "small-item")
    video_id_list = []
    for video_el in video_els:
        video_id = video_el.get_attribute('data-aid')
        video_id_list.append(video_id)
    if limit != None:
        video_id_list = video_id_list[:limit]
    return video_id_list

def ext_videos(video_list):
    ext_list = ["BV1WT411K7Ti","BV1uT411P7Nq"]
    for id_item in ext_list:
        if id_item not in video_list:
            video_list.append(id_item)

def get_data(bv_id):
    video_url = "https://www.bilibili.com/video/" + bv_id
    driver.get(video_url)
    ticktock = pendulum.now("Asia/Shanghai")
    time.sleep(5)
    first_result = wait.until(ExpC.presence_of_element_located((By.CLASS_NAME, "bpx-player-sending-bar")))
    time.sleep(1)
    try:
        online_el = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[1]/div[2]/div[2]/div/div/div[1]/div[2]/div/div[1]/div[1]/b")
        online_str = online_el.text
        play_el = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[1]/div[1]/div/div/span[1]")
        play_str = play_el.text
        like_el = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[1]/div[3]/div[1]/span[1]/span")
        like_str = like_el.text
        coin_el = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[1]/div[3]/div[1]/span[2]/span")
        coin_str = coin_el.text
        star_el = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[1]/div[3]/div[1]/span[3]/span")
        star_str = star_el.text
        rtime_el = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[1]/div[1]/div/div/span[3]/span/span")
        rtime_str = rtime_el.text
        title_el = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[1]/div[1]/h1")
        title_str = title_el.text
        title_str = title_str[:30]
    except:
        return {}
    if "-" == online_str:
        print("selenium warning 1")
        return {}
    if "" in [online_str, play_str, like_str, coin_str, star_str]:
        print("selenium warning 2")
        return {}
    # time.sleep(1)
    online =  pretty_num(online_str)
    play = pretty_num(play_str)
    like = pretty_num(like_str)
    coin = pretty_num(coin_str) 
    star = pretty_num(star_str)

    stay, rate = stay_rate(play, like, coin, star)
    rtime = pendulum.parse(rtime_str, tz="Asia/Shanghai")

    output_dict = { "online": online - 1,
                    "play": play,
                    "like": like,
                    "coin": coin, 
                    "star": star, 
                    "stay": stay,
                    "rate": rate,
                    "rtime": rtime.to_datetime_string(),     # to datetime str
                    "mtime": ticktock.to_datetime_string(),  # to datetime str
                    "title": title_str}
    return output_dict

def get_api(bv_id):
    ticktock = pendulum.now("Asia/Shanghai")

    cid_url = "https://api.bilibili.com/x/player/pagelist"
    payload = {"bvid": bv_id}
    r = requests.get(cid_url,params=payload)
    if r.status_code != 200:
        return
    res = r.json()
    c_id = res["data"][0]["cid"]

    online_url = "http://api.bilibili.com/x/player/online/total"
    payload = {"bvid": bv_id, "cid": c_id}
    r = requests.get(online_url,params=payload)
    if r.status_code != 200:
        return
    res = r.json()
    online_str = res["data"]["total"]
    online =  pretty_num(online_str)

    view_url = "http://api.bilibili.com/x/web-interface/view"
    payload = {"bvid": bv_id}
    r = requests.get(view_url,params=payload)
    if r.status_code != 200:
        return
    res = r.json()
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
    evaluation_str  = res["data"]["stat"]["evaluation"]
    # print(online)
    # print(his_rank)
    # print(now_rank)
    # print(evaluation_str)
    stay, rate = stay_rate(play, like, coin, star)

    output_dict = { "online": online - 1,
                    "play": play,
                    "like": like,
                    "coin": coin, 
                    "star": star, 
                    "stay": stay,
                    "rate": rate,
                    "rtime": rtime.to_datetime_string(),     # to datetime str
                    "mtime": ticktock.to_datetime_string(),  # to datetime str
                    "title": title_str}
    return output_dict


def stay_rate(play_num, like_num, coin_num, star_num):
    if play_num == 0:
        return 0, 0

    if play_num < 50:
        stay_num = 0
        rate_num = 0
    else:
        stay_num = like_num + star_num + coin_num * 5
        rate_num = stay_num / play_num

    return stay_num , rate_num

def pretty_num(origin_str):
    if origin_str in [" ","  ","-","点赞","投币","收藏"]:
        output_num = 0  
    elif not origin_str.isdigit():
        tmp_str = origin_str[:-1]
        output_num = int(float(tmp_str) * 10000)
    else:
        output_num = int(origin_str)
    return output_num

def cmd_print(box_list):
    pretty = "Current Dashboard Data \n"
    offline = []
    for item in box_list:
        # bv_id, online, play, like, coin, star, release_time, title  = item
        bv_id = item["bv_id"]
        online = item["online"]
        play = item["play"]
        like = item["like"]
        coin = item["coin"]
        star = item["star"]
        stay = item["stay"]
        rate = item["rate"]
        rtime = item["rtime"]
        mtime = item["mtime"]
        title = item["title"]

        time_diff = (pendulum.parse(mtime) - pendulum.parse(rtime)).in_hours()

        if online > 999:
            online_str = "^"+ str(online)
        elif online > 99:
            online_str = "$ "   + str(online)
        elif online > 50:
            online_str = "@  "  + str(online)
        elif online > 24:
            online_str = "&  "  + str(online)
        elif online > 9:
            online_str = "+  "  + str(online)
        elif online > 0:
            online_str = "    " + str(online)
        elif online == 0:
            online_str = "    "
            # total_online += online_num
            if time_diff > 24:
                offline.append([bv_id, play])
                continue
        else:
            print("warning => " , online_str)
            online_str = "ERROR"


        # rate = "{:.2f} %".format(rate_num * 100)
        # pretty = pretty + flag + online + "\t" + play + "\t" + stay + "\t" +  rate + "\t" + release_time + "  " + bv_id + " " + title + "\n" 
        pretty = pretty + " " + online_str + "\t" + str(play) + "\t" + str(stay) + "\t"  + \
                 str(rtime) + "  " + bv_id + "  " +  title + "\n" 
    # print offline
    logger.debug(offline)
    #print online
    logger.debug(pretty)

def monitor(box_list):
    global df
    if box_list == []:
        return
    if type(df) == type(None):
        df = pd.DataFrame(box_list)
        df = df[["bv_id","title","rtime","mtime","online","play","like","stay"]]
        df["rtime"] = pd.to_datetime(df["rtime"])
        df["mtime"] = pd.to_datetime(df["mtime"])

    else:
        box_df = pd.DataFrame(box_list)
        box_df = box_df[["bv_id","title","rtime","mtime","online","play","like","stay"]]
        box_df["rtime"] = pd.to_datetime(box_df["rtime"])
        box_df["mtime"] = pd.to_datetime(box_df["mtime"])
        df = pd.concat([df,box_df], ignore_index = True)

    # print(df.set_index("bv_id")["title"].to_dict())

    # title_dict = df.set_index("bv_id")["title"].to_dict()
    # print(title_dict)

    # df = pd.concat([df, box_df],ignore_index = True)
    # print(df)
    # tmp = df[df["bv_id"] == "BV1WT411K7Ti"]
    # print(df.groupby(['bv_id']).resample("H")["online"].mean())

    a_se = df.set_index(df["mtime"]).groupby(['bv_id',"rtime"]).resample("H")["online"].mean().round(2)
    b_se = df.set_index(df["mtime"]).groupby(['bv_id',"rtime"]).resample("H")["play"].last()
    c_se = df.set_index(df["mtime"]).groupby(['bv_id',"rtime"]).resample("H")["stay"].last()
    m_df = pd.concat([a_se,b_se,c_se], axis=1)
    # m_df = l_df[(l_df["online"] >= 5) | (l_df["play"] >= 10000)]
    m_df = m_df[(m_df["online"] >= 5)]
    n_df = m_df.sort_values(by=['rtime','mtime'], ascending=False)
    print(n_df)

    # a_se = df.set_index(df["mtime"]).groupby(['bv_id',"rtime"])["online"].last().round(2)
    # b_se = df.set_index(df["mtime"]).groupby(['bv_id',"rtime"])["play"].last()
    # c_se = df.set_index(df["mtime"]).groupby(['bv_id',"rtime"])["stay"].last()
    # m_df = pd.concat([a_se,b_se,c_se], axis=1)
    # # m_df = l_df[(l_df["online"] >= 5) | (l_df["play"] >= 10000)]
    # m_df = m_df[(m_df["play"] >= 10000)]
    # n_df = m_df.sort_values(by=['rtime'], ascending=False)
    # print(n_df)




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
        time.sleep(60)
    # for item in range(1000):
    #     print("=====================================")
    #     launch()
