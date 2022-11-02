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

    for (filename, basename, extname) in FILE_list:
        # default
        outputname = basename + ".mp4"
        alias = ""
        param = "-crf 17 -c:a copy"
        if filename in MODIFY_list:
            continue

        if alias != "":
            outputname = basename + " " + alias + "." + ".mp4"
        filepath = SRC + "\\" + filename
        cachepath = CACHE + "\\" + outputname
        hashpath = cachepath + ".md5"

        filesafe = " \"" + filepath + "\" "
        cachesafe = " \"" + cachepath + "\" "

        ffmpeg_cmd = "ffmpeg -i" + filesafe + param  + cachesafe
        # msg("CMD ➜ " + ffmpeg_cmd)
        lumos(ffmpeg_cmd)

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
    msg("CMD => " + cmd)
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

def msg(content):
    # onli str
    pretty = "\n" + content + "\n"
    logger.debug(pretty)


if __name__ == '__main__':
    load()
    # precheck()
    print("Source PATH: \t" + SRC)
    print("Output PATH: \t" + CACHE)
    print("Info FTP: \t" + CURL_cmd)
    # ic("Source PATH: \t" + SRC)
    # ic("Output PATH: \t" + CACHE)
    # ic("Info FTP: \t" + CURL_cmd)
    launch()
