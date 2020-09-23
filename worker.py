from threading import Thread
import requests
from time import sleep
from os import mkdir, rmdir, listdir, system, environ
from os.path import isdir, isfile, getsize
from json import dumps, loads

import signal

import tracker

from youtube_dl import YoutubeDL

from shutil import make_archive, rmtree

from queue import Queue

from gc import collect

from discovery import getmetadata
from export import subprrun

batchcontent = []

HEROKU = False
if isfile("../Procfile"):
    HEROKU = True

def batchfunc():
    ydl = YoutubeDL({"extract_flat": "in_playlist", "simulate": True, "skip_download": True, "quiet": True, "cookiefile": "cookies.txt", "source_address": "0.0.0.0", "call_home": False})
    
    if not HEROKU:
        desqsize = 51
    elif HEROKU:
        desqsize = 251
    
    while jobs.qsize() < desqsize:
        desit = tracker.request_item_from_tracker()
        if desit:
            if desit.split(":", 1)[0] == "video":
                jobs.put(desit.split(":", 1)[1])
            elif desit.split(":", 1)[0] == "channel":
                y = ydl.extract_info("https://www.youtube.com/channel/"+desit.split(":", 1)[1], download=False)
                for itemyv in y["entries"]:
                    tracker.add_item_to_tracker(tracker.ItemType.Video, itemyv["id"])
            elif desit.split(":", 1)[0] == "playlist":
                y = ydl.extract_info("https://www.youtube.com/playlist?list="+desit.split(":", 1)[1], download=False)
                for itemyvp in y["entries"]:
                    tracker.add_item_to_tracker(tracker.ItemType.Video, itemyvp["id"])
            else:
                print("Ignoring item for now", desit)
        else:
            print("Ignoring item for now", desit)
        
        batchcontent.append(desit.split(":", 1)[1])

def submitfunc(submitqueue):
    while not submitqueue.empty():
        itype, ival = submitqueue.get()
        tracker.add_item_to_tracker(itype, ival)

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

validationtest = mysession.get("https://www.youtube.com/timedtext_editor?action_mde_edit_form=1&v=1iNTtHUwvq4&lang=en&bl=vmp&ui=hd&ref=player&tab=captions&o=U")

assert not "accounts.google.com" in validationtest.url, "Please ensure you have correctly specified account cookies."
assert """<button class="yt-uix-button yt-uix-button-size-default yt-uix-button-default yt-uix-button-has-icon" type="button" onclick=";return false;" id="yt-picker-language-button" data-button-action="yt.www.picker.load" data-button-menu-id="arrow-display" data-picker-key="language" data-picker-position="footer" data-button-toggle="true"><span class="yt-uix-button-icon-wrapper"><span class="yt-uix-button-icon yt-uix-button-icon-footer-language yt-sprite"></span></span><span class="yt-uix-button-content">  <span class="yt-picker-button-label">
Language:
  </span>
  English
</span><span class="yt-uix-button-arrow yt-sprite"></span></button>""" in validationtest.text, "Please make sure your YouTube and Google account language is set to English (United States)"

del validationtest

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
                info = getmetadata(mysession, str(item).strip())
                break
            except BaseException as e:
                print(e)
                print("Error in retrieving information, waiting 30 seconds")
                sleep(30)

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

    try:
        mkdir("directory")
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
        xc.join()
        batchthreads.remove(xc)
        del xc

    sleep(1) # prevent the script from continuing before the last thread finishes

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

    # IDK how to handle mixes so just send them for now
    print("Videos:", len(recvids))
    for itemvid in recvids:
        submitjobs.put((tracker.ItemType.Video, itemvid))

    print("Channels:", len(recchans))
    for itemchan in recchans:
        submitjobs.put((tracker.ItemType.Channel, itemchan))

    print("Mix Playlists:", len(recmixes))
    for itemmix in recmixes:
        submitjobs.put((tracker.ItemType.MixPlaylist, itemmix))

    print("Playlists:", len(recplayl))
    for itemplayl in recplayl:
        submitjobs.put((tracker.ItemType.Playlist, itemplayl))

    # open("out/discoveries.json", "w").write(dumps({"recvids": sorted(recvids), "recchans": sorted(recchans), "recmixes": sorted(recmixes), "recplayl": sorted(recplayl)}))
    
    # clear lists
    recvids.clear()
    recchans.clear()
    recmixes.clear()
    recplayl.clear()

    submitthreads = []

    for r in range(50):
        submitrunthread = Thread(target=submitfunc, args=(submitjobs,))
        submitrunthread.start()
        submitthreads.append(submitrunthread)
        del submitrunthread

    for xb in submitthreads:
        xb.join()
        submitthreads.remove(xb)
        del xb

    sleep(1) # prevent the script from continuing before the last thread finishes


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
        xa.join()
        subthreads.remove(xa)
        del xa

    sleep(30) # wait 30 seconds to hopefully allow the other threads to finish

    for fol in listdir("out"): #remove empty folders
        try:
            if isdir("out/"+fol):
                rmdir("out/"+fol)
        except:
            pass

    #https://stackoverflow.com/a/11968881


    for fol in listdir("out"):
        if isdir("out/"+fol):
            make_archive("directory/"+fol, "zip", "out/"+fol)

    targetloc = None
    while not targetloc:
        targetloc = tracker.request_upload_target()
        if targetloc:
            break
        else:
            print("Waiting 5 minutes...")
            sleep(300)

    if targetloc.startswith("rsync"):
        system("rsync -rltv --timeout=300 --contimeout=300 --progress --bwlimit 0 --recursive --partial --partial-dir .rsync-tmp --min-size 1 --no-compress --compress-level 0 --files-from=- directory/ "+targetloc)
    elif targetloc.startswith("http"):
        for filzip in listdir("directory"):
            if filzip.endswith(".zip"):
                system("curl -F "+filzip+"=@directory/"+filzip+" "+targetloc)

    # Report the batch as complete
    for itemb in batchcontent:
        if isfile("directory/"+itemb.split(":", 1)[1]+".zip"):
            size = getsize("directory/"+itemb.split(":", 1)[1]+".zip")
        else:
            size = 0
        tracker.mark_item_as_done(itemb, size)

    # clear the output directories
    rmtree("out")
    rmtree("directory")