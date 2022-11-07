
import urllib.request
import time
import json
import os
from tqdm import tqdm
from alive_progress import alive_bar, alive_it

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ExpC

import requests
from bs4 import BeautifulSoup

# This example requires Selenium WebDriver 3.13 or newe
options = Options()
# options.add_argument("-headless")  # headless
# options.page_load_strategy = 'eager'
driver = webdriver.Firefox(executable_path="geckodriver", options=options)
wait = WebDriverWait(driver, 10)


MAIN_PATH = ""

def login():
    driver.maximize_window()
    driver.get("https://www.douyin.com")

    driver.title  # => "Google"
    print(driver.title)
    print("login\n")

    time.sleep(20)


def fetch_videos(user_mixin):
    global MAIN_PATH
    for item in user_mixin:
        user_href = item["user_href"]
        # last_id = item["last_id"]
        skip_flag = item["skip_flag"]
        # skip_list = item["skip_list"]
        sub_path = item["path"]
        path = MAIN_PATH + sub_path

        # if "]" in last_id:
        #     last_id = last_id.rsplit("]", 1)[1]

        if skip_flag == True:
            continue

        driver.get(user_href)
        time.sleep(1)
        print(driver.title)

        count_old = 0
        for scrollTimes in range(10000):
            # fetch all nodes. Break if no new one
            # video_els = driver.find_elements(By.XPATH, "/html/body/div[1]/div/div[2]/div/div/div[4]/div[1]/div[2]/ul/li[6]/a")
            video_els = driver.find_elements(By.CLASS_NAME, "ECMy_Zdt")
            if len(video_els) == 0:
                video_els = driver.find_elements(By.CLASS_NAME, "Eie04v01")
            count_new = len(video_els)
            if count_new == count_old:
                break
            else:
                count_old = count_new

            # 执行向下滚动操作
            time.sleep(2)
            js_down = "window.scrollTo(0,1000000)"
            driver.execute_script(js_down)
            time.sleep(1)  # for flash

        video_els = driver.find_elements(By.CLASS_NAME, "ECMy_Zdt")
        if len(video_els) == 0:
            video_els = driver.find_elements(By.CLASS_NAME, "Eie04v01")

        local_list = fetch_local(path)

        video_list = []
        for video_el in video_els:
            try:
                video_href = video_el.find_element(By.XPATH, "./a").get_attribute(
                    "href"
                )
                video_id = video_href.rsplit("/", 1)[1]
                if video_id not in local_list:
                    print(video_id)
                    video_list.append(video_id)
                else:
                    pass
                    # print(video_id, " => continue")
            except:
                print("error", user_href)
                pass
        for video_id in alive_it(video_list):
            download_by_dlpanda(video_id, path)

    # data = video_list
    # with open("download.json", "w", encoding="utf-8") as f:
    #     json.dump(data, f)

def fetch_local(path):
    video_id_list = []
    file_list = os.listdir(path)
    for file_item in file_list:
        if "]" in file_item and "." in file_item:
            tmp_name = file_item.rsplit("]", 1)[1]
            video_id = tmp_name.rsplit(".", 1)[0]
            video_id_list.append(video_id)

    # print(video_id_list)
    return video_id_list


def download_videos():
    data = None
    with open("download.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    video_list = data
    for video_id in alive_it(video_list):
        download_by_dlpanda(video_id)
        # bar()

    # for video_link in video_link_list:
    #     cmd = "wget " + video_link
    #     os.system(cmd)


def get_mixin():
    # get user href from file
    global MAIN_PATH
    data = None
    with open("download_info.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    user_mixin = data["detail"]
    online_flag = data["online"]
    MAIN_PATH = data["main_path"]
    if online_flag is True:
        return user_mixin
    else:
        return


def download_by_dlpanda(video_id, path = "download"):
    # driver.switch_to.new_window('tab')
    video_href = "https://www.douyin.com/video/" + video_id
    encode_href = urllib.request.quote(video_href)
    pre_dlpanda_href = "https://dlpanda.com/en?url="
    page_href = pre_dlpanda_href + encode_href
    # print(href)
    # try:
    #     driver.get(page_href)
    #     print("here")
    #     time.sleep(2)  # for flash
    #     driver.execute_script('window.stop()')
    #     print("ready")
    #     download_button = driver.find_element(
    #         By.XPATH, "/html/body/main/section[1]/div/div/div[2]/div[2]/div/div[2]/a"
    #     )
    #     print("done")
    # except:
    #     print(page_href)
    #     return
    # href_attr = download_button.get_attribute("href")
    # download_attr = download_button.get_attribute("download")
    try:
        r = requests.get(page_href)
        soup = BeautifulSoup(r.text, "lxml")
        href_attr = soup.find("a", "primary-solid-btn")['href']
        download_attr = soup.find("a", "primary-solid-btn")['download']
    except:
        print(page_href)
        return


    real_href = "https://dlpanda.com" + href_attr
    target_name = download_attr.split("]", 1)[1]  # remove [DLpanda]
    # cmd = "wget " + href_attr + " -q -O " + "\"downloads/" + target_name + "\""
    cmd = "curl -s -o " + '"' + path + '/' + target_name + '" ' + real_href
    # print(cmd)
    lumos(cmd)

    # return download_button.get_attribute("href")

    # click() is not fine
    # driver.execute_script("arguments[0].click()", download_button)
    # cmd = "wget " + download_button.href
    # os.system(cmd)


def lumos(cmd):
    # res = 0
    # print("CMD ➜ " + cmd)
    res = os.system(cmd)
    return res


if __name__ == "__main__":

    user_mixin = get_mixin()

    login()
    fetch_videos(user_mixin)
    # if user_mixin is not None or not os.path.exists("download.json"):
    #     login()
    #     fetch_videos(user_mixin)

    # download_videos()

    driver.quit()
