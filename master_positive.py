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
DIST = None
CURL_cmd = None

FILE_list = []
CONFIG_list = []


def load():
    global SRC
    global DIST
    global CURL_cmd
    global CONFIG_list
    data = None
    with open("info.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
        SRC = data["src"]
        DIST = data["dist"]
        CURL_cmd = data["curlCmd"]
        CONFIG_list = data["infoArr"]


def launch():
    global SRC
    global FILE_list
    global CONFIG_list
    ls_list = os.listdir(SRC)
    for filename in ls_list:
        if "." not in filename:
            continue
        (basename, extname) = filename.rsplit('.',1) # basename.mkv in the end
        if extname == "mkv":
            FILE_list.append(filename)
    ic(FILE_list)
    for item in FILE_list:
        # default
        filename = item
        alias = ""
        param = "-c:v copy -c:a copy"
        for index_item in CONFIG_list:
            if item == index_item["file"]:
                filename = index_item["file"]
                alias = index_item["alias"]
                param = index_item["param"]

        (basename, extname)= filename.rsplit('.',1)
        filefullname = basename + "." + extname
        if alias != "":
            filefullname = basename + " " + alias + "." + extname
        filepath = SRC + "\\" + filename
        outputpath = DIST + "\\" + filefullname
        hashpath = outputpath + ".md5"

        filesafe = " \"" + filepath + "\" "
        outputsafe = " \"" + outputpath + "\" "

        ffmpeg_cmd = "ffmpeg -i" + filesafe + param  + outputsafe
        # msg("CMD ➜ " + ffmpeg_cmd)
        lumos(ffmpeg_cmd)

        createhash(outputpath)
        filesync(outputpath)
        filesync(hashpath)


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

if __name__ == '__main__':
    load()
    # precheck()
    print("Source PATH: \t" + SRC)
    print("Output PATH: \t" + DIST)
    print("Info FTP: \t" + CURL_cmd)
    # ic("Source PATH: \t" + SRC)
    # ic("Output PATH: \t" + DIST)
    # ic("Info FTP: \t" + CURL_cmd)
    launch()
