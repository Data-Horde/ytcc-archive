from threading import Thread
import requests
from time import sleep
from os import mkdir, rmdir, listdir, system, environ
from os.path import isdir, isfile, getsize
from json import dumps, loads

import signal

import tracker

from youtube_dl import YoutubeDL

from shutil import rmtree, which

from queue import Queue

from gc import collect

from discovery import getmetadata
from export import subprrun

#useful Queue example: https://stackoverflow.com/a/54658363
jobs = Queue()

try:
    mkdir("out")
except:
    pass

try:
    mkdir("directory")
except:
    pass

HEROKU = False
if isfile("../Procfile"):
    HEROKU = True

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

assert which("zip") and which("rsync") and which("curl"), "Please ensure the zip, rsync, and curl commands are installed on your system."

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
allheaders = {"cookie": "HSID="+cookies["HSID"]+"; SSID="+cookies["SSID"]+"; SID="+cookies["SID"], "Accept-Language": "en-US",}
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

    def exit_gracefully(self, signum, frame):
        print("Graceful exit process initiated, no longer accepting new tasks but finishing existing ones...")
        self.kill_now = True

gkiller = GracefulKiller()

#microtasks
def threadrunner():
    jobs = Queue()
    ydl = YoutubeDL({"extract_flat": "in_playlist", "simulate": True, "skip_download": True, "quiet": True, "cookiefile": "cookies.txt", "source_address": "0.0.0.0", "call_home": False})
    while True:
        if not jobs.empty():
            task, vid, args = jobs.get()
            if task == "submitdiscovery":
                tracker.add_item_to_tracker(args, vid)
            elif task == "discovery":
                while True:
                    try:
                        info = getmetadata(mysession, str(vid).strip(), allheaders)
                        break
                    except BaseException as e:
                        print(e)
                        print("Error in retrieving information, waiting 30 seconds and trying again")
                        #raise
                        sleep(30)
                if info[0] or info[1]: # ccenabled or creditdata
                    if not isdir("out/"+str(vid).strip()):
                        mkdir("out/"+str(vid).strip())
                if info[1]:
                    open("out/"+str(vid).strip()+"/"+str(vid).strip()+"_published_credits.json", "w").write(dumps(info[1]))

                if info[0]:
                    for langcode in langs:
                        jobs.put(("subtitles", vid, langcode))

                    for langcode in langs:
                        jobs.put(("subtitles-forceedit-metadata", vid, langcode))

                    for langcode in langs:
                        jobs.put(("subtitles-forceedit-captions", vid, langcode))

                jobs.put(("complete", None, "video:"+vid))

                for videodisc in info[2]:
                    jobs.put(("submitdiscovery", videodisc, tracker.ItemType.Video))
                for channeldisc in info[3]:
                    jobs.put(("submitdiscovery", channeldisc, tracker.ItemType.Channel))
                for mixdisc in info[4]:
                    jobs.put(("submitdiscovery", mixdisc, tracker.ItemType.MixPlaylist))
                for playldisc in info[5]:
                    jobs.put(("submitdiscovery", playldisc, tracker.ItemType.Playlist))

            elif task == "subtitles":
                subprrun(mysession, args, vid, "default", needforcemetadata, needforcecaptions, allheaders)
            elif task == "subtitles-forceedit-captions":
                subprrun(mysession, args, vid, "forceedit-captions", needforcemetadata, needforcecaptions, allheaders)
            elif task == "subtitles-forceedit-metadata":
                subprrun(mysession, args, vid, "forceedit-metadata", needforcemetadata, needforcecaptions, allheaders)
            elif task == "channel":
                try:
                    y = ydl.extract_info("https://www.youtube.com/channel/"+desit.split(":", 1)[1], download=False)
                    for itemyv in y["entries"]:
                        jobs.put(("submitdiscovery", itemyv["id"], tracker.ItemType.Video))
                    jobs.put(("complete", None, "channel:"+args))
                except:
                    print("YouTube-DL error, ignoring but not marking as complete...", "https://www.youtube.com/channel/"+desit.split(":", 1)[1])
            elif task == "playlist":
                try:
                    y = ydl.extract_info("https://www.youtube.com/playlist?list="+desit.split(":", 1)[1], download=False)
                    for itemyvp in y["entries"]:
                        jobs.put(("submitdiscovery", itemyvp["id"], tracker.ItemType.Video))
                    jobs.put(("complete", None, "playlist:"+args))
                except:
                    print("YouTube-DL error, ignoring but not marking as complete...", "https://www.youtube.com/playlist?list="+desit.split(":", 1)[1])
            elif task == "complete":
                size = 0
                if ":" in args:
                    if args.split(":", 1)[0] == "video":
                        #check if dir is empty, make zip if needed
                        if isdir("out/"+args.split(":", 1)[1]):
                            if not listdir("out/"+args.split(":", 1)[1]):
                                rmdir("out/"+args.split(":", 1)[1])
                            else:
                                #zip it up
                                if not isdir("directory/"+args.split(":", 1)[1]):
                                    mkdir("directory/"+args.split(":", 1)[1])

                                while not isfile("directory/"+args.split(":", 1)[1]+"/"+args.split(":", 1)[1]+".zip"):
                                    print("Attempting to zip item...")
                                    system("zip -9 -r -j directory/"+args.split(":", 1)[1]+"/"+args.split(":", 1)[1]+".zip out/"+args.split(":", 1)[1])

                                #get a target
                                targetloc = None
                                while not targetloc:
                                    targetloc = tracker.request_upload_target()
                                    if targetloc:
                                        break
                                    else:
                                        print("Waiting 5 minutes...")
                                        sleep(300)

                                if targetloc.startswith("rsync"):
                                    system("rsync -rltv --timeout=300 --contimeout=300 --progress --bwlimit 0 --recursive --partial --partial-dir .rsync-tmp --min-size 1 --no-compress --compress-level 0 directory/"+args.split(":", 1)[1]+"/ "+targetloc)
                                elif targetloc.startswith("http"):
                                    system("curl -F "+args.split(":", 1)[1]+".zip=@directory/"+args.split(":", 1)[1]+"/"+args.split(":", 1)[1]+".zip "+targetloc)


                                size = getsize("directory/"+args.split(":", 1)[1]+"/"+args.split(":", 1)[1]+".zip")
                                #cleanup
                                try:
                                    del langcnt[args.split(":", 1)[1]]
                                    rmtree("directory/"+args.split(":", 1)[1]+"/")
                                    rmdir("directory/"+args.split(":", 1)[1]+"/")
                                    rmtree("out/"+args.split(":", 1)[1]+"/")
                                    rmdir("out/"+args.split(":", 1)[1]+"/")
                                except:
                                    pass
                tracker.mark_item_as_done(args, size)
            jobs.task_done()
        else:
            if not gkiller.kill_now:
                # get a new task from tracker
                collect() #cleanup
                desit = tracker.request_item_from_tracker()
                print("New task:", desit)

                if desit:
                    if desit.split(":", 1)[0] == "video":
                        needforcemetadata = {'ab': None, 'aa': None, 'af': None, 'sq': None, 'ase': None, 'am': None, 'ar': None, 'arc': None, 'hy': None, 'as': None, 'ay': None, 'az': None, 'bn': None, 'ba': None, 'eu': None, 'be': None, 'bh': None, 'bi': None, 'bs': None, 'br': None, 
                            'bg': None, 'yue': None, 'yue-HK': None, 'ca': None, 'chr': None, 'zh-CN': None, 'zh-HK': None, 'zh-Hans': None, 'zh-SG': None, 'zh-TW': None, 'zh-Hant': None, 'cho': None, 'co': None, 'hr': None, 'cs': None, 'da': None, 'nl': None, 
                            'nl-BE': None, 'nl-NL': None, 'dz': None, 'en': None, 'en-CA': None, 'en-IN': None, 'en-IE': None, 'en-GB': None, 'en-US': None, 'eo': None, 'et': None, 'fo': None, 'fj': None, 'fil': None, 'fi': None, 'fr': None, 'fr-BE': None, 
                            'fr-CA': None, 'fr-FR': None, 'fr-CH': None, 'ff': None, 'gl': None, 'ka': None, 'de': None, 'de-AT': None, 'de-DE': None, 'de-CH': None, 'el': None, 'kl': None, 'gn': None, 'gu': None, 'ht': None, 'hak': None, 'hak-TW': None, 'ha': None, 
                            'iw': None, 'hi': None, 'hi-Latn': None, 'ho': None, 'hu': None, 'is': None, 'ig': None, 'id': None, 'ia': None, 'ie': None, 'iu': None, 'ik': None, 'ga': None, 'it': None, 'ja': None, 'jv': None, 'kn': None, 'ks': None, 'kk': None, 'km': None, 'rw': None, 
                            'tlh': None, 'ko': None, 'ku': None, 'ky': None, 'lo': None, 'la': None, 'lv': None, 'ln': None, 'lt': None, 'lb': None, 'mk': None, 'mg': None, 'ms': None, 'ml': None, 'mt': None, 'mni': None, 'mi': None, 'mr': None, 'mas': None, 'nan': None, 
                            'nan-TW': None, 'lus': None, 'mo': None, 'mn': None, 'my': None, 'na': None, 'nv': None, 'ne': None, 'no': None, 'oc': None, 'or': None, 'om': None, 'ps': None, 'fa': None, 'fa-AF': None, 'fa-IR': None, 'pl': None, 'pt': None, 'pt-BR': None, 
                            'pt-PT': None, 'pa': None, 'qu': None, 'ro': None, 'rm': None, 'rn': None, 'ru': None, 'ru-Latn': None, 'sm': None, 'sg': None, 'sa': None, 'sc': None, 'gd': None, 'sr': None, 'sr-Cyrl': None, 'sr-Latn': None, 'sh': None, 'sdp': None, 'sn': None, 
                            'scn': None, 'sd': None, 'si': None, 'sk': None, 'sl': None, 'so': None, 'st': None, 'es': None, 'es-419': None, 'es-MX': None, 'es-ES': None, 'es-US': None, 'su': None, 'sw': None, 'ss': None, 'sv': None, 'tl': None, 'tg': None, 'ta': None, 
                            'tt': None, 'te': None, 'th': None, 'bo': None, 'ti': None, 'tpi': None, 'to': None, 'ts': None, 'tn': None, 'tr': None, 'tk': None, 'tw': None, 'uk': None, 'ur': None, 'uz': None, 'vi': None, 'vo': None, 'vor': None, 'cy': None, 'fy': None, 'wo': None, 
                            'xh': None, 'yi': None, 'yo': None, 'zu': None}
                        needforcecaptions = {'ab': None, 'aa': None, 'af': None, 'sq': None, 'ase': None, 'am': None, 'ar': None, 'arc': None, 'hy': None, 'as': None, 'ay': None, 'az': None, 'bn': None, 'ba': None, 'eu': None, 'be': None, 'bh': None, 'bi': None, 'bs': None, 'br': None, 
                            'bg': None, 'yue': None, 'yue-HK': None, 'ca': None, 'chr': None, 'zh-CN': None, 'zh-HK': None, 'zh-Hans': None, 'zh-SG': None, 'zh-TW': None, 'zh-Hant': None, 'cho': None, 'co': None, 'hr': None, 'cs': None, 'da': None, 'nl': None, 
                            'nl-BE': None, 'nl-NL': None, 'dz': None, 'en': None, 'en-CA': None, 'en-IN': None, 'en-IE': None, 'en-GB': None, 'en-US': None, 'eo': None, 'et': None, 'fo': None, 'fj': None, 'fil': None, 'fi': None, 'fr': None, 'fr-BE': None, 
                            'fr-CA': None, 'fr-FR': None, 'fr-CH': None, 'ff': None, 'gl': None, 'ka': None, 'de': None, 'de-AT': None, 'de-DE': None, 'de-CH': None, 'el': None, 'kl': None, 'gn': None, 'gu': None, 'ht': None, 'hak': None, 'hak-TW': None, 'ha': None, 
                            'iw': None, 'hi': None, 'hi-Latn': None, 'ho': None, 'hu': None, 'is': None, 'ig': None, 'id': None, 'ia': None, 'ie': None, 'iu': None, 'ik': None, 'ga': None, 'it': None, 'ja': None, 'jv': None, 'kn': None, 'ks': None, 'kk': None, 'km': None, 'rw': None, 
                            'tlh': None, 'ko': None, 'ku': None, 'ky': None, 'lo': None, 'la': None, 'lv': None, 'ln': None, 'lt': None, 'lb': None, 'mk': None, 'mg': None, 'ms': None, 'ml': None, 'mt': None, 'mni': None, 'mi': None, 'mr': None, 'mas': None, 'nan': None, 
                            'nan-TW': None, 'lus': None, 'mo': None, 'mn': None, 'my': None, 'na': None, 'nv': None, 'ne': None, 'no': None, 'oc': None, 'or': None, 'om': None, 'ps': None, 'fa': None, 'fa-AF': None, 'fa-IR': None, 'pl': None, 'pt': None, 'pt-BR': None, 
                            'pt-PT': None, 'pa': None, 'qu': None, 'ro': None, 'rm': None, 'rn': None, 'ru': None, 'ru-Latn': None, 'sm': None, 'sg': None, 'sa': None, 'sc': None, 'gd': None, 'sr': None, 'sr-Cyrl': None, 'sr-Latn': None, 'sh': None, 'sdp': None, 'sn': None, 
                            'scn': None, 'sd': None, 'si': None, 'sk': None, 'sl': None, 'so': None, 'st': None, 'es': None, 'es-419': None, 'es-MX': None, 'es-ES': None, 'es-US': None, 'su': None, 'sw': None, 'ss': None, 'sv': None, 'tl': None, 'tg': None, 'ta': None, 
                            'tt': None, 'te': None, 'th': None, 'bo': None, 'ti': None, 'tpi': None, 'to': None, 'ts': None, 'tn': None, 'tr': None, 'tk': None, 'tw': None, 'uk': None, 'ur': None, 'uz': None, 'vi': None, 'vo': None, 'vor': None, 'cy': None, 'fy': None, 'wo': None, 
                            'xh': None, 'yi': None, 'yo': None, 'zu': None}
                        jobs.put(("discovery", desit.split(":", 1)[1], None))
                    elif desit.split(":", 1)[0] == "channel":
                        jobs.put(("channel", None, desit.split(":", 1)[1]))
                    elif desit.split(":", 1)[0] == "playlist":
                        jobs.put(("playlist", None, desit.split(":", 1)[1]))
                    else:
                        print("Ignoring item for now", desit)
                else:
                    print("Ignoring item for now", desit)
            else:
                break
    

threads = []

THREADCNT = 50
if HEROKU:
    THREADCNT = 20
#now create the rest of the threads
for i in range(THREADCNT):
    runthread = Thread(target=threadrunner)
    runthread.start()
    threads.append(runthread)
    del runthread

#https://stackoverflow.com/a/11968881
for x in threads:
    x.join()
    threads.remove(x)
    del x

print("Exiting...")