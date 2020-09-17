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


import requests
from bs4 import BeautifulSoup
from datetime import timedelta

from os import mkdir

from json import loads, dumps


#HSID, SSID, SID cookies required
cookies = loads(open("config.json").read())
headers = {
    "cookie": "HSID="+cookies["HSID"]+"; SSID="+cookies["SSID"]+"; SID="+cookies["SID"],
}

def getsubs(vid):
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

    mkdir(vid)

    for langcode in langs:
        pparams = (
            ("v", vid),
            ("lang", langcode),
            ("action_mde_edit_form", 1),
            ("bl", "vmp"),
            ("ui", "hd"),
            ("tab", "captions"),
            ("o", "U")
        )

        page = requests.get("https://www.youtube.com/timedtext_editor", params=pparams, headers=headers)

        assert not "accounts.google.com" in page.url, "Please supply authentication cookie information in config.json. See README.md for more information."

        soup = BeautifulSoup(page.text, features="html5lib")

        divs = soup.find_all("div", class_="timed-event-line")

        outtext = ""

        for item in divs:
            text = item.find("textarea").text
            startms = int(item.find("input", class_="event-start-time")["data-start-ms"])
            endms = int(item.find("input", class_="event-end-time")["data-end-ms"])

            outtext += timedelta_to_sbv_timestamp(timedelta(milliseconds=startms)) + "," + timedelta_to_sbv_timestamp(timedelta(milliseconds=endms)) + "\n" + text + "\n\n"

        open(vid+"/"+vid+"_"+langcode+".sbv", "w", encoding="utf-8").write(outtext[:-1])

        if soup.find("li", id="captions-editor-nav-metadata")["data-state"] != "locked":
            metadata = {}

            metadata["title"] = soup.find("input", id="metadata-title")["value"]
            metadata["description"] = soup.find("textarea", id="metadata-description").text

            open(vid+"/"+vid+"_"+langcode+".json", "w", encoding="utf-8").write(dumps(metadata))

if __name__ == "__main__":
    from sys import argv
    vidl = argv
    vidl.pop(0)
    for video in vidl:
        getsubs(video)
