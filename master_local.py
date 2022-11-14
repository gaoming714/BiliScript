"""
master
watch MKV file, then upload to ftp server

need curl, alternative ftp or rsync

"""

import os
import json
import hashlib
from icecream import ic
from loguru import logger


SRC = None
CACHE = None
CURL_cmd = None
FFmpeg = "ffmpeg"

FILE_list = []
MODIFY_list = []
CONFIG_list = []



def load():
    global SRC
    global CACHE
    global CURL_cmd
    global CONFIG_list
    global MODIFY_list
    data = None
    with open("master_info.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
        SRC = data["src"]
        CACHE = data["cache"]
        CURL_cmd = data["curlCmd"]
        CONFIG_list = data["infoArr"]
    for item in CONFIG_list:
        MODIFY_list.append(item["file"])


def launch():
    global SRC
    global FILE_list
    global CONFIG_list
    ls_list = os.listdir(SRC)
    for filename in ls_list:
        if "." not in filename:
            continue
        (basename, extname) = filename.rsplit('.',1) # basename.mkv in the end
        if extname in ["mkv","mp4","MP4"]:
            FILE_list.append((filename,basename,extname))
    ic(FILE_list)

    ffmpeg_list = []
    for (filename, basename, extname) in FILE_list:
        # default
        outputname = basename + ".mp4"
        param = "-crf 17 -c:a copy"
        if filename in MODIFY_list:
            # skip modity
            continue
        filepath = SRC + "\\" + filename
        cachepath = CACHE + "\\" + outputname
        hashpath = cachepath + ".md5"

        filesafe = " \"" + filepath + "\" "
        cachesafe = " \"" + cachepath + "\" "

        ffmpeg_cmd = FFmpeg + " -i" + filesafe + param  + cachesafe
        ffmpeg_list.append(ffmpeg_cmd)


    for info_item in CONFIG_list:
        if info_item['file'] not in ls_list:
            print("skip => ", info_item['file'])
            continue

        filename = info_item['file']
        alias = info_item['alias']
        param = info_item['param']
        (basename, extname) = filename.rsplit('.',1)

        if alias == "":
            outputname = basename + ".mp4"
        else:
            outputname = basename + " " + alias  + ".mp4"
        if param == "":
            param = "-crf 17 -c:a copy"
        filepath = SRC + "\\" + filename
        cachepath = CACHE + "\\" + outputname
        hashpath = cachepath + ".md5"

        filesafe = " \"" + filepath + "\" "
        cachesafe = " \"" + cachepath + "\" "

        ffmpeg_cmd = FFmpeg + " -i" + filesafe + param  + cachesafe
        ffmpeg_list.append(ffmpeg_cmd)


    ic(ffmpeg_list)
    for item_cmd in ffmpeg_list:
        lumos(item_cmd)

        # createhash(cachepath)
        # filesync(cachepath)
        # filesync(hashpath)




def createhash(filepath):
    hashhex = None
    filesize = os.path.getsize(filepath)
    if filesize > 10*1024*1024*1024:
        hashhex = "infinite"
    else:
        with open(filepath, 'rb') as f:
            data = f.read()
            hasher = hashlib.md5()
            hasher.update(data)
            hashhex = hasher.hexdigest()

    hashpath = filepath + ".md5"
    with open(hashpath, 'w', encoding='utf-8') as f:
        f.write(hashhex)

def lumos(cmd):
    # print(cmd)
    # res = 0
    pre = "\n🧪   "
    logger.debug(pre + cmd)
    res = os.system(cmd)
    return res

def filesync(filepath):
    upload_cmd = CURL_cmd + "\"" + filepath + "\""
    # for windows, curl need download
    # if os.path.exists('curl.exe'):
    #     windows_curl = ".\\curl ftp://192.168.3.200/ftp/input/ -u \"anonymous:\" -T "
    #     upload_cmd = windows_curl + "\"" + filepath + "\""
    ic(upload_cmd) # debug
    res = os.system(upload_cmd)
    return res

def precheck():
    global FILE_list
    global SRC
    for item in FILE_list:
        filename = item["file"]
        filepath = SRC + "\\" + filename
        if not os.path.exists(filepath):
            raise Exception("Missing " + filepath)
    print("==== Precheck is OK ====")

def pretty_ffmpeg():
    global FFmpeg
    try:
        if os.system("ffmpeg-bar -h") == 0:
            FFmpeg = "ffmpeg-bar"
    except:
        pass


if __name__ == '__main__':
    load()
    pretty_ffmpeg()
    # precheck()
    print("Source PATH: \t" + SRC)
    print("Output PATH: \t" + CACHE)
    print("Info FTP: \t" + CURL_cmd)
    # ic("Source PATH: \t" + SRC)
    # ic("Output PATH: \t" + CACHE)
    # ic("Info FTP: \t" + CURL_cmd)
    launch()
