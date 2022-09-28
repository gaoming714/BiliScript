"""
master 
watch MKV file, then upload to ftp server

need curl, alternative ftp or rsync

"""

import os
from watchfiles import Change, watch
import hashlib
from loguru import logger

SRC = 'Input'
DIST = 'Output'
CMD_ffmepg = 'ffmpeg -i '
CMD_param = '-crf 17 -c:a copy'

def launch():
    print("Watching....")
    for changes in watch(SRC, watch_filter=only_added):
        # print(changes)
        print("Stack online => " + str(len(changes)))
        for change in changes:
            action = change[0]
            hashpath = change[1]
            filepath = hashpath.rsplit('.',1)[0] # remove md5 in the end
            # added = 1
            # modified = 2
            # deleted = 3
            if action == 1 and os.path.exists(filepath) and os.path.exists(hashpath):
                msg("File Path => " + filepath)
                if checkhash(filepath, hashpath):
                    # msg("Hash is same => " + filepath)
                    res = compress(filepath)
                    if res == 0:
                        msg("Compress is Finished => " + filepath)
                else:
                    critical("Hash is not same => " + filepath)
                    with open(DIST+"\\error.txt", 'a', encoding='utf-8') as f:
                        f.write(filepath)
                        f.write("\n")
        print("Watching....")


def only_added(change: Change, path: str) -> bool:
    extensions = ('.md5')
    return path.endswith(extensions)

def checkhash(filepath, hashpath):
    # msg("Check Hash")
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
    with open(hashpath, 'r', encoding='utf-8') as f:
        origin_md5 = f.read()
    print("origin_md5  => " + origin_md5)
    print("current_md5 => " + hashhex)
    return hashhex == origin_md5



def compress(filepath):
    filename = os.path.split(filepath)[1]
    filename_main = filename.rsplit('.',1)[0] # remove mkv in the end
    file_output = filename_main + ".mp4"
    compress_cmd = CMD_ffmepg + " \"" + filepath + "\" " + CMD_param + " \"" + DIST + "\\" + file_output + "\" "
    # for windows, ffmpeg need to add in folder
    if os.path.exists('ffmpeg.exe'):
        compress_cmd = ".\\" + compress_cmd
    msg("CMD => " + compress_cmd)
    return os.system(compress_cmd)


def msg(content):
    # onli str
    pretty = "\n" + content
    logger.debug(pretty)

def critical(content):
    # onli str
    pretty = "\n" + content
    logger.critical(pretty)


if __name__ == '__main__':
    print("Source PATH: \t" + SRC)
    print("Output PATH: \t" + DIST)
    print("Info ffmpeg: \t" + CMD_param)
    launch()
