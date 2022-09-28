"""
master
watch MKV file, then upload to ftp server

need curl, alternative ftp or rsync

"""

import os
import json
import hashlib



SRC_audio = "inputAudio"
SRC_video = "inputVideo"
DIST = "output"

FILE_list = None

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

def launch():
    if not os.path.exists(SRC_audio):
        raise
    if not os.path.exists(SRC_video):
        raise
    FILE_list = os.listdir(SRC_video)
    for file_video in FILE_list:
        mainname = file_video.rsplit('.',1)[0] # remove mp4 in the end
        file_audio = mainname + ".m4a"
        file_output = mainname + ".mp4"
        print(SRC_audio + "/" + file_audio)
        if not os.path.exists(SRC_audio + "/" + file_audio):
            print("Audio is missing!!")
            break
        audiosafe = " \"" + SRC_audio + "/" + file_audio + "\" "
        videosafe = " \"" + SRC_video + "/" + file_video + "\" "
        outputsafe = " \"" + DIST + "/" + file_output + "\" "
        param = " -c:v copy -c:a copy "

        ffmpeg_cmd = "ffmpeg -i " + audiosafe +" -i " + videosafe + param  + outputsafe
        lumos(ffmpeg_cmd)


def lumos(cmd):
    # print(cmd)
    # res = 0
    print("CMD ➜ " + cmd)
    res = os.system(cmd)
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
    launch()
