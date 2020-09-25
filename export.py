# This function adapted from https://github.com/cdown/srt/blob/11089f1e021f2e074d04c33fc7ffc4b7b52e7045/srt.py, lines 69 and 189 (MIT License)
def timedelta_to_sbv_timestamp(timedelta_timestamp):
    r"""
    Convert a :py:class:`~datetime.timedelta` to an SRT timestamp.
    .. doctest::
        >>> import datetime
        >>> delta = datetime.timedelta(hours=1, minutes=23, seconds=4)
        >>> timedelta_to_sbv_timestamp(delta)
        '01:23:04,000'
    :param datetime.timedelta timedelta_timestamp: A datetime to convert to an
                                                   SBV timestamp
    :returns: The timestamp in SBV format
    :rtype: str
    """

    SECONDS_IN_HOUR = 3600
    SECONDS_IN_MINUTE = 60
    HOURS_IN_DAY = 24
    MICROSECONDS_IN_MILLISECOND = 1000

    hrs, secs_remainder = divmod(timedelta_timestamp.seconds, SECONDS_IN_HOUR)
    hrs += timedelta_timestamp.days * HOURS_IN_DAY
    mins, secs = divmod(secs_remainder, SECONDS_IN_MINUTE)
    msecs = timedelta_timestamp.microseconds // MICROSECONDS_IN_MILLISECOND
    return "%1d:%02d:%02d.%03d" % (hrs, mins, secs, msecs)


from datetime import timedelta

from json import dumps

from gc import collect

# import requests

from time import sleep

# https://docs.python.org/3/library/html.parser.html
from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.captions = []
        self.title = ""
        self.description = ""
        self.inittitle = ""
        self.initdescription = ""


    def check_attr(self, attrs, attr, value):
        for item in attrs:
            if item[0] == attr and item[1] == value:
                return True
        return False

    def get_attr(self, attrs, attr):
        for item in attrs:
            if item[0] == attr:
                return item[1]
        return False

    def handle_starttag(self, tag, attrs):
        if tag == "input" and self.check_attr(attrs, "class", "yt-uix-form-input-text event-time-field event-start-time"):
            self.captions.append({"startTime": int(self.get_attr(attrs, "data-start-ms")), "text": ""})
        elif tag == "input" and self.check_attr(attrs, "class", "yt-uix-form-input-text event-time-field event-end-time"):
            self.captions[len(self.captions)-1]["endTime"] = int(self.get_attr(attrs, "data-end-ms"))
        elif tag == "input" and self.check_attr(attrs, "id", "metadata-title"):
            self.title = self.get_attr(attrs, "value")
        elif tag == "textarea" and self.check_attr(attrs, "id", "metadata-description"):
            self.initdescription = self.get_attr(attrs, "data-original-description")

    def handle_data(self, data):
        if self.get_starttag_text() and self.get_starttag_text().startswith("<textarea "):
            if 'name="serve_text"' in self.get_starttag_text():
                self.captions[len(self.captions)-1]["text"] += data
            elif 'id="metadata-description"' in self.get_starttag_text():
                self.description += data
        elif self.get_starttag_text() and self.get_starttag_text().startswith('<div id="original-video-title"'):
            self.inittitle += data

def subprrun(mysession, langcode, vid, mode, needforcemetadata, needforcecaptions):
    if mode == "forceedit-metadata":
        while needforcemetadata[langcode] == None: #extra logic
            print("Awaiting forcemetadata")
            sleep(1)
        if needforcemetadata[langcode] == False:
            #print("forcemetadata not needed")
            return True #nothing needs to be done, otherwise, continue

    if mode == "forceedit-captions":
        while needforcecaptions[langcode] == None: #extra logic
            print("Awaiting forcecaptions")
            sleep(1)
        if needforcecaptions[langcode] == False:
            #print("forcecaptions not needed")
            return True #nothing needs to be done, otherwise, continue

    collect() #cleanup memory

    vid = vid.strip()
    print(langcode, vid)

    while True:
        try:
            if mode == "default":
                pparams = (
                    ("v", vid),
                    ("lang", langcode),
                    ("action_mde_edit_form", 1),
                    ("bl", "vmp"),
                    ("ui", "hd"),
                    ("tab", "captions"),
                    ("o", "U")
                )

                page = mysession.get("https://www.youtube.com/timedtext_editor", params=pparams)
            elif mode == "forceedit-metadata":
                pparams = (
                    ("v", vid),
                    ("lang", langcode),
                    ("action_mde_edit_form", 1),
                    ('forceedit', 'metadata'),
                    ('tab', 'metadata')
                )

                page = mysession.get("https://www.youtube.com/timedtext_editor", params=pparams)
            elif mode == "forceedit-captions":
                pparams = (
                    ("v", vid),
                    ("lang", langcode),
                    ("action_mde_edit_form", 1),
                    ("bl", "vmp"),
                    ("ui", "hd"),
                    ('forceedit', 'captions'),
                    ("tab", "captions"),
                    ("o", "U")
                )

                page = mysession.get("https://www.youtube.com/timedtext_editor", params=pparams)

            if not "accounts.google.com" in page.url and page.status_code != 429 and 'Subtitles/CC' in page.text and ('Title &amp; description' in page.text or 'Title and description' in page.text):
                break
            else:
                print("[Retrying in 30 seconds for rate limit or login failure] Please supply authentication cookie information in config.json or environment variables. See README.md for more information.")
                sleep(30)
        except:
            print("Error in request, retrying in 5 seconds...")
            sleep(5)

    inttext = page.text

    try:
        initlang = page.text.split("'metadataLanguage': \"", 1)[1].split('"', 1)[0]
    except:
        initlang = ""

    del page

    filestring = "_community_draft"
    
    if '<li id="captions-editor-nav-captions" role="tab" data-state="published" class="published">' in inttext:
        filestring = "_community_published"

    if mode == "forceedit-captions":
        filestring = "_community_draft"

    if 'title="The video owner already provided subtitles/CC"' in inttext:
        filestring = "_uploader_provided"

    if not "forceedit" in mode:
        if '&amp;forceedit=metadata&amp;tab=metadata">See latest</a>' in inttext:
            print("Need forcemetadata")
            needforcemetadata[langcode] = True
        else:
            needforcemetadata[langcode] = False

        if '<li id="captions-editor-nav-captions" role="tab" data-state="published" class="published">' in inttext:
            print("Need forcecaptions")
            needforcecaptions[langcode] = True
        else:
            needforcecaptions[langcode] = False

    if 'id="reject-captions-button"' in inttext or 'id="reject-metadata-button"' in inttext or 'data-state="published"' in inttext or 'title="The video owner already provided subtitles/CC"' in inttext: #quick way of checking if this page is worth parsing
        parser = MyHTMLParser()
        parser.feed(inttext)

        captiontext = False
        for item in parser.captions:
            if item["text"][:-9]:
                captiontext = True

        if captiontext and (mode == "default" or mode == "forceedit-captions"):
            myfs = open("out/"+vid+"/"+vid+"_"+langcode+filestring+".sbv", "w", encoding="utf-8")
            captions = parser.captions
            captions.pop(0) #get rid of the fake one
            while captions:
                item = captions.pop(0)

                myfs.write(timedelta_to_sbv_timestamp(timedelta(milliseconds=item["startTime"])) + "," + timedelta_to_sbv_timestamp(timedelta(milliseconds=item["endTime"])) + "\n" + item["text"][:-9] + "\n")
                
                del item
                if captions:
                    myfs.write("\n")
            del captions
            myfs.close()
            del myfs

        del captiontext

        if (parser.title or parser.description[:-16]) and (mode == "default" or mode == "forceedit-metadata"):
            metadata = {}
            metadata["title"] = parser.title
            if metadata["title"] == False:
                metadata["title"] = ""
            metadata["description"] = parser.description[:-16]

            filestring = "_community_draft"
            if '<li id="captions-editor-nav-metadata" role="tab" data-state="published" class="published">' in inttext:
                filestring = "_community_published"

            if mode == "forceedit-metadata":
                filestring = "_community_draft"
            open("out/"+vid+"/"+vid+"_"+langcode+filestring+".json", "w", encoding="utf-8").write(dumps(metadata))
            del metadata

        if (parser.inittitle[9:-17] or parser.initdescription) and (mode == "default" or mode == "forceedit-metadata" and initlang):
            metadata = {}
            metadata["title"] = parser.inittitle[9:-17]
            if metadata["title"] == False:
                metadata["title"] = ""
            metadata["description"] = parser.initdescription

            filestring = "_uploader_provided"
            open("out/"+vid+"/"+vid+"_"+initlang+filestring+".json", "w", encoding="utf-8").write(dumps(metadata))
            del metadata

    del inttext

    del langcode
    del vid
    del pparams

    return True

# if __name__ == "__main__":
#     from os import environ, mkdir
#     from os.path import isfile
#     from json import loads
#     #HSID, SSID, SID cookies required
#     if "HSID" in environ.keys() and "SSID" in environ.keys() and "SID" in environ.keys():
#         cookies = {"HSID": environ["HSID"], "SSID": environ["SSID"], "SID": environ["SID"]}
#     elif isfile("config.json"):
#         cookies = loads(open("config.json").read())
#     else:
#         print("HSID, SSID, and SID cookies from youtube.com are required. Specify in config.json or as environment variables.")
#         assert False
#     if not (cookies["HSID"] and cookies["SSID"] and cookies["SID"]):
#         print("HSID, SSID, and SID cookies from youtube.com are required. Specify in config.json or as environment variables.")
#         assert False

#     mysession = requests.session()
#     mysession.headers.update({"cookie": "HSID="+cookies["HSID"]+"; SSID="+cookies["SSID"]+"; SID="+cookies["SID"], "Accept-Language": "en-US",})
#     del cookies
#     from sys import argv
#     from queue import Queue
#     from threading import Thread
#     langs = ['ab', 'aa', 'af', 'sq', 'ase', 'am', 'ar', 'arc', 'hy', 'as', 'ay', 'az', 'bn', 'ba', 'eu', 'be', 'bh', 'bi', 'bs', 'br', 
#     'bg', 'yue', 'yue-HK', 'ca', 'chr', 'zh-CN', 'zh-HK', 'zh-Hans', 'zh-SG', 'zh-TW', 'zh-Hant', 'cho', 'co', 'hr', 'cs', 'da', 'nl', 
#     'nl-BE', 'nl-NL', 'dz', 'en', 'en-CA', 'en-IN', 'en-IE', 'en-GB', 'en-US', 'eo', 'et', 'fo', 'fj', 'fil', 'fi', 'fr', 'fr-BE', 
#     'fr-CA', 'fr-FR', 'fr-CH', 'ff', 'gl', 'ka', 'de', 'de-AT', 'de-DE', 'de-CH', 'el', 'kl', 'gn', 'gu', 'ht', 'hak', 'hak-TW', 'ha', 
#     'iw', 'hi', 'hi-Latn', 'ho', 'hu', 'is', 'ig', 'id', 'ia', 'ie', 'iu', 'ik', 'ga', 'it', 'ja', 'jv', 'kn', 'ks', 'kk', 'km', 'rw', 
#     'tlh', 'ko', 'ku', 'ky', 'lo', 'la', 'lv', 'ln', 'lt', 'lb', 'mk', 'mg', 'ms', 'ml', 'mt', 'mni', 'mi', 'mr', 'mas', 'nan', 
#     'nan-TW', 'lus', 'mo', 'mn', 'my', 'na', 'nv', 'ne', 'no', 'oc', 'or', 'om', 'ps', 'fa', 'fa-AF', 'fa-IR', 'pl', 'pt', 'pt-BR', 
#     'pt-PT', 'pa', 'qu', 'ro', 'rm', 'rn', 'ru', 'ru-Latn', 'sm', 'sg', 'sa', 'sc', 'gd', 'sr', 'sr-Cyrl', 'sr-Latn', 'sh', 'sdp', 'sn', 
#     'scn', 'sd', 'si', 'sk', 'sl', 'so', 'st', 'es', 'es-419', 'es-MX', 'es-ES', 'es-US', 'su', 'sw', 'ss', 'sv', 'tl', 'tg', 'ta', 
#     'tt', 'te', 'th', 'bo', 'ti', 'tpi', 'to', 'ts', 'tn', 'tr', 'tk', 'tw', 'uk', 'ur', 'uz', 'vi', 'vo', 'vor', 'cy', 'fy', 'wo', 
#     'xh', 'yi', 'yo', 'zu']
#     vidl = argv
#     vidl.pop(0)

#     try:
#         mkdir("out")
#     except:
#         pass

#     jobs = Queue()
#     for video in vidl:
#         try:
#             mkdir("out/"+video.strip())
#         except:
#             pass
#         for lang in langs:
#             jobs.put((lang, video, "default"))

#     subthreads = []

#     for r in range(50):
#         subrunthread = Thread(target=subprrun, args=(jobs,mysession))
#         subrunthread.start()
#         subthreads.append(subrunthread)
#         del subrunthread

#     for xa in subthreads:
#         xa.join() #bug (occurred once: the script ended before the last thread finished)
#         subthreads.remove(xa)
#         del xa