from threading import Thread
import requests
from time import sleep
from os import mkdir, rmdir, listdir, system, environ
from os.path import isdir, isfile, getsize
from json import dumps, loads

import signal

from youtube_dl.utils import DownloadError

import tracker

from youtube_dl import YoutubeDL

from shutil import make_archive, rmtree

from queue import Queue

from gc import collect

from discovery import getmetadata
from export import subprrun

batchcontent = []

def batchfunc():
    while len(batchcontent) < 500:
        batchcontent.append(tracker.request_item_from_tracker())

def submitfunc(submitqueue):
    while not submitqueue.empty():
        itype, ival = submitqueue.get()
        tracker.add_item_to_tracker(itype, ival)

WORKER_VERSION  = 1
SERVER_BASE_URL = "http://localhost:5000"

langs = ['ab', 'aa', 'af', 'sq', 'ase', 'am', 'ar', 'arc', 'hy', 'as', 'ay', 'az', 'bn', 'ba', 'eu', 'be', 'bh', 'bi', 'bs', 'br', 
    'bg', 'yue', 'yue-HK', 'ca', 'chr', 'zh-CN', 'zh-HK', 'zh-Hans', 'zh-SG', 'zh-TW', 'zh-Hant', 'cho', 'co', 'hr', 'cs', 'da', 'nl', 
    'nl-BE', 'nl-NL', 'dz', 'en', 'en-CA', 'en-IN', 'en-IE', 'en-GB', 'en-US', 'eo', 'et', 'fo', 'fj', 'fil', 'fi', 'fr', 'fr-BE', 
    'fr-CA', 'fr-FR', 'fr-CH', 'ff', 'gl', 'ka', 'de', 'de-AT', 'de-DE', 'de-CH', 'el', 'kl', 'gn', 'gu', 'ht', 'hak', 'hak-TW', 'ha', 
    'iw', 'hi', 'hi-Latn', 'ho', 'hu', 'is', 'ig', 'id', 'ia', 'ie', 'iu', 'ik', 'ga', 'it', 'ja', 'jv', 'kn', 'ks', 'kk', 'km', 'rw', 
    'tlh', 'ko', 'ku', 'ky', 'lo', 'la', 'lv', 'ln', 'lt', 'lb', 'mk', 'mg', 'ms', 'ml', 'mt', 'mni', 'mi', 'mr', 'mas', 'nan', 
    'nan-TW', 'lus', 'mo', 'mn', 'my', 'na', 'nv', 'ne', 'no', 'oc', 'or', 'om', 'ps', 'fa', 'fa-AF', 'fa-IR', 'pl', 'pt', 'pt-BR', 
    'pt-PT', 'pa', 'qu', 'ro', 'rm', 'rn', 'ru', 'ru-Latn', 'sm', 'sg', 'sa', 'sc', 'gd', 'sr', 'sr-Cyrl', 'sr-Latn', 'sh', 'sdp', 'sn', 
    'scn', 'sd', 'si', 'sk', 'sl', 'so', 'st', 'es', 'es-419', 'es-MX', 'es-ES', 'es-US', 'su', 'sw', 'ss', 'sv', 'tl', 'tg', 'ta', 
    'tt', 'te', 'th', 'bo', 'ti', 'tpi', 'to', 'ts', 'tn', 'tr', 'tk', 'tw', 'uk', 'ur', 'uz', 'vi', 'vo', 'vor', 'cy', 'fy', 'wo', 
    'xh', 'yi', 'yo', 'zu']

#useful Queue example: https://stackoverflow.com/a/54658363
jobs = Queue()

ccenabledl = []

recvids  = set()
recchans = set()
recmixes = set()
recplayl = set()

#HSID, SSID, SID cookies required
if "HSID" in environ.keys() and "SSID" in environ.keys() and "SID" in environ.keys():
    cookies = {"HSID": environ["HSID"], "SSID": environ["SSID"], "SID": environ["SID"]}
elif isfile("config.json"):
    cookies = loads(open("config.json").read())
else:
    print("HSID, SSID, and SID cookies from youtube.com are required. Specify in config.json or as environment variables.")
    assert False
if not (cookies["HSID"] and cookies["SSID"] and cookies["SID"]):
    print("HSID, SSID, and SID cookies from youtube.com are required. Specify in config.json or as environment variables.")
    assert False

mysession = requests.session()
mysession.headers.update({"cookie": "HSID="+cookies["HSID"]+"; SSID="+cookies["SSID"]+"; SID="+cookies["SID"], "Accept-Language": "en-US",})

open("cookies.txt", "w").write("""# HTTP Cookie File
.youtube.com	TRUE	/	FALSE	1663793455	SID	[SID]
.youtube.com	TRUE	/	FALSE	1663793455	HSID	[HSID]
.youtube.com	TRUE	/	TRUE	1663793455	SSID	[SSID]""".replace("[SID]", cookies["SID"]).replace("[HSID]", cookies["HSID"]).replace("[SSID]", cookies["SSID"]))

del cookies

#Graceful Shutdown
class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self,signum, frame):
        self.kill_now = True

gkiller = GracefulKiller()

def prrun():
    while not jobs.empty():
        global recvids
        global recchans
        global recmixes
        global recplayl
        global ccenabledl

        item = jobs.get()

        print("Video ID:", str(item).strip())
        while True:
            try:
                info = getmetadata(str(item).strip())
                break
            except BaseException as e:
                print(e)
                print("Error in retrieving information, waiting 30 seconds")
                #raise
                sleep(30)

        ydl = YoutubeDL({"extract_flat": "in_playlist", "simulate": True, "skip_download": True, "quiet": True, "cookiefile": "cookies.txt", "source_address": "0.0.0.0", "call_home": False})
        for chaninfo in set(info[3]):
            if chaninfo not in recchans:
                while True:
                    try:
                        y = ydl.extract_info("https://www.youtube.com/channel/"+chaninfo, download=False)
                        recchans.add(chaninfo)
                        break
                    except:
                        sleep(30)
                sleep(5) #prevent error 429
                for itemyv in y["entries"]:
                    recvids.add(itemyv["id"])

        for playlinfo in set(info[5]):
            if playlinfo not in recplayl:
                while True:
                    try:
                        y = ydl.extract_info("https://www.youtube.com/playlist?list="+playlinfo, download=False)
                        recplayl.add(playlinfo)
                        break
                    except:
                        sleep(30)
                sleep(5) #prevent error 429
                for itemyvp in y["entries"]:
                    recvids.add(itemyvp["id"])

        # Add any discovered videos
        recvids.update(info[2])
        recchans.update(info[3])
        recmixes.update(info[4])
        recplayl.update(info[5])

        if info[0] or info[1]: # ccenabled or creditdata
            if not isdir("out/"+str(item).strip()):
                mkdir("out/"+str(item).strip())

        if info[1]: # creditdata
            open("out/"+str(item).strip()+"/"+str(item).strip()+"_published_credits.json", "w").write(dumps(info[1]))

        if info[0]: #ccenabled
            ccenabledl.append(item)
        jobs.task_done()

    return True

while not gkiller.kill_now:
    collect() #cleanup

    try:
        mkdir("out")
    except:
        pass

    batchcontent.clear()

    # Get a batch ID
    batchthreads = []

    for r in range(50):
        batchrunthread = Thread(target=batchfunc)
        batchrunthread.start()
        batchthreads.append(batchrunthread)
        del batchrunthread

    for xc in batchthreads:
        xc.join() #bug (occurred once: the script ended before the last thread finished)
        batchthreads.remove(xc)
        del xc



    #for ir in range(501):
    #    batchcontent.append(tracker.request_item_from_tracker())

    for desit in batchcontent:
        if desit:
            if desit.split(":", 1)[0] == "video":
                jobs.put(desit.split(":", 1)[1])
            else:
                print("Ignoring item for now", desit)
        else:
            print("Ignoring item for now", desit)

    threads = []

    for i in range(50):
        runthread = Thread(target=prrun)
        runthread.start()
        threads.append(runthread)
        del runthread

    for x in threads:
        x.join()
        threads.remove(x)
        del x

    print("Sending discoveries to tracker...")

    submitjobs = Queue()
    #don't send channels and playlists as those have already been converted for video IDs
    #IDK how to handle mixes so send them for now
    print(len(recvids))
    for itemvid in recvids:
        submitjobs.put((tracker.ItemType.Video, itemvid))

    print(len(recmixes))
    for itemmix in recmixes:
        submitjobs.put((tracker.ItemType.MixPlaylist, itemmix))

    #open("out/discoveries.json", "w").write(dumps({"recvids": sorted(recvids), "recchans": sorted(recchans), "recmixes": sorted(recmixes), "recplayl": sorted(recplayl)}))
    #clear
    recvids.clear()
    # recchans.clear()
    recmixes.clear()
    # recplayl.clear()

    submitthreads = []

    for r in range(50):
        submitrunthread = Thread(target=submitfunc, args=(submitjobs,))
        submitrunthread.start()
        submitthreads.append(submitrunthread)
        del submitrunthread

    for xb in submitthreads:
        xb.join() #bug (occurred once: the script ended before the last thread finished)
        submitthreads.remove(xb)
        del xb

    sleep(1)


    subtjobs = Queue()
    while ccenabledl:
        langcontent = langs.copy()
        intvid = ccenabledl.pop(0)

        while langcontent:
            subtjobs.put((langcontent.pop(0), intvid, "default"))
        del intvid
        del langcontent

    subthreads = []

    for r in range(50):
        subrunthread = Thread(target=subprrun, args=(subtjobs,mysession))
        subrunthread.start()
        subthreads.append(subrunthread)
        del subrunthread

    for xa in subthreads:
        xa.join() #bug (occurred once: the script ended before the last thread finished)
        subthreads.remove(xa)
        del xa

    sleep(1) #wait a second to hopefully allow the other threads to finish

    for fol in listdir("out"): #remove extra folders
        try:
            if isdir("out/"+fol):
                rmdir("out/"+fol)
        except:
            pass

    #https://stackoverflow.com/a/11968881

    # TODO: put the data somewhere...
    # TODO: put the discoveries somewhere...

    for fol in listdir("out"):
        if isdir("out/"+fol):
            make_archive("out/"+fol, "zip", "out/"+fol) #check this

    targetloc = None
    while not targetloc:
        targetloc = tracker.request_upload_target()
        if targetloc:
            break
        else:
            print("Waiting 5 minutes...")
            sleep(300)

    for zipf in listdir("out"):
        if isfile(zipf) in zipf.endswith(".zip"):
            if targetloc.startswith("rsync"):
                system("rsync out/"+zipf+" "+targetloc)
            elif targetloc.startswith("http"):
                upzipf = open("out/"+zipf, "rb")
                requests.post(targetloc, data=upzipf)
                upzipf.close()
            #upload it!

    # Report the batch as complete
    for itemb in batchcontent:
        if isfile("out/"+itemb.split(":", 1)[1]+".zip"):
            size = getsize("out/"+itemb.split(":", 1)[1]+".zip")
        else:
            size = 0
        tracker.mark_item_as_done(itemb, size)

    # clear the output directory
    rmtree("out")