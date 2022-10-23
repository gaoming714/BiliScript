from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import urllib.request
import time
import json
import os
from tqdm import tqdm
from alive_progress import alive_bar, alive_it

driver = webdriver.Firefox()


def login():
    driver.maximize_window()
    driver.get("https://www.douyin.com")

    driver.title  # => "Google"
    print(driver.title)
    print("login\n")

    time.sleep(20)


def fetch_videos(user_mixin):

    video_list = []
    for item in user_mixin:
        user_href = item["user_href"]
        last_id = item["last_id"]
        skip_flag = item["skip_flag"]
        skip_list = item["skip_list"]

        if "]" in last_id:
            last_id = last_id.rsplit("]", 1)[1]

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
            print(len(video_els))
            count_new = len(video_els)
            if count_new == count_old:
                break
            else:
                count_old = count_new

            # 执行向下滚动操作
            js_down = "window.scrollTo(0,1000000)"
            time.sleep(2)
            js_down = "window.scrollTo(0,1000000)"
            driver.execute_script(js_down)
            time.sleep(1)  # for flash

        # video_els = driver.find_elements(By.CLASS_NAME,"ECMy_Zdt")
        video_els = driver.find_elements(By.CLASS_NAME, "ECMy_Zdt")
        if len(video_els) == 0:
            video_els = driver.find_elements(By.CLASS_NAME, "Eie04v01")

        top_count = 0
        for video_el in video_els:
            try:
                video_href = video_el.find_element(By.XPATH, "./a").get_attribute(
                    "href"
                )
                video_id = video_href.rsplit("/", 1)[1]
                # if top_count >= 3:
                #     if last_id.isdigit():
                #         if int(video_id) <= int(last_id):
                #             print(video_id, " => break")
                #             break
                # else:
                #     top_count = top_count + 1
                #     if last_id.isdigit():
                #         if int(video_id) <= int(last_id):
                #             print(video_id, " => continue")
                #             continue
                if last_id.isdigit() and int(video_id) <= int(last_id):
                    if top_count >=3:
                        print(video_id," => break")
                        break
                    else:
                        print(video_id," => continue")
                        top_count += 1
                        continue
                    
                # video_href = video_el.get_attribute("href")
                # print(video_href)
                if video_id in skip_list:
                    print(video_id, " => skip")
                    continue
                print(video_id)
                video_list.append(video_id)
            except:
                print("error", user_href)
                pass

    data = video_list
    with open("download.json", "w", encoding="utf-8") as f:
        json.dump(data, f)


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
    data = None
    with open("download_info.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    user_mixin = data["detail"]
    online_flag = data["online"]
    if online_flag is True:
        return user_mixin
    else:
        return


def download_by_dlpanda(video_id):
    # driver.switch_to.new_window('tab')
    video_href = "https://www.douyin.com/video/" + video_id
    encode_href = urllib.request.quote(video_href)
    pre_dlpanda_href = "https://dlpanda.com/en?url="
    page_href = pre_dlpanda_href + encode_href
    # print(href)
    try:
        driver.get(page_href)
        time.sleep(4)  # for flash
        download_button = driver.find_element(
            By.XPATH, "/html/body/main/section[1]/div/div/div[2]/div[2]/div/div[2]/a"
        )
    except:
        print(page_href)
        return

    href_attr = download_button.get_attribute("href")
    download_attr = download_button.get_attribute("download")
    # real_href = "https://dlpanda" + href_attr
    target_name = download_attr.split("]", 1)[1]  # remove [DLpanda]
    # cmd = "wget " + href_attr + " -q -O " + "\"downloads/" + target_name + "\""
    cmd = "curl -s -o " + '"downloads/' + target_name + '" ' + href_attr
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

    if user_mixin is not None or not os.path.exists("download.json"):
        login()
        fetch_videos(user_mixin)

    download_videos()

    driver.quit()
