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

from json import loads


#HSID, SSID, SID cookies required
cookies = loads(open("config.json").read())
headers = {
    "cookie": "HSID="+cookies["HSID"]+"; SSID="+cookies["SSID"]+"; SID="+cookies["SID"],
}

def getsubs(vid, lang="all"):
    if lang == "all":
        lparams = (
            ("v", vid),
            ("ref", "player"),
            ("o", "U"),
        )

        langpage = requests.get("https://www.youtube.com/timedtext_video", params=lparams, headers=headers)

        assert not "accounts.google.com" in langpage.url, "Please supply authentication cookie information in config.json. See README.md for more information."

        langs = []
        langsoup = BeautifulSoup(langpage.text, features="html5lib")

        if "create_channel" in langpage.url:
            print(vid, "not found.")
        elif langsoup.find_all("div", {"class": "not-accepting-caption-submissions"}):
            print(vid, "has disabled community-contributed captioning.")
            langs = []
        else:
            langdivs = langsoup.find("ul", class_="yt-uix-languagepicker-language-list").find_all("li", class_="yt-uix-languagepicker-menu-item")

            for item in langdivs:
                langs.append(item["data-value"])

            print(vid, "has the following languages available", ", ".join(langs)+".")
    else:
        langs = [lang]

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

        soup = BeautifulSoup(page.text, features="html5lib")

        divs = soup.find_all("div", class_="timed-event-line")

        outtext = ""

        for item in divs:
            text = item.find("textarea").text
            startms = int(item.find("input", class_="event-start-time")["data-start-ms"])
            endms = int(item.find("input", class_="event-end-time")["data-end-ms"])

            outtext += timedelta_to_sbv_timestamp(timedelta(milliseconds=startms)) + "," + timedelta_to_sbv_timestamp(timedelta(milliseconds=endms)) + "\n" + text + "\n\n"

        open(vid+"_"+langcode+".sbv", "w", encoding="utf-8").write(outtext[:-1])

if __name__ == "__main__":
    from sys import argv
    vidl = argv
    vidl.pop(0)
    for video in vidl:
        getsubs(video)