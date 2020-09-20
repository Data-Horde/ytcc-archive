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


from bs4 import BeautifulSoup
from datetime import timedelta

from json import dumps

import requests

def subprrun(jobs, headers):
    while not jobs.empty():
        langcode, vid = jobs.get()
        print(langcode, vid)
        pparams = (
            ("v", vid),
            ("lang", langcode),
            ("action_mde_edit_form", 1),
            ("bl", "vmp"),
            ("ui", "hd"),
            ("tab", "captions"),
            ("o", "U")
        )

        page = requests.get("https://www.youtube.com/timedtext_editor", headers=headers, params=pparams)

        assert not "accounts.google.com" in page.url, "Please supply authentication cookie information in config.json. See README.md for more information."

        soup = BeautifulSoup(page.text, features="html5lib")
        del page

        divs = soup.find_all("div", class_="timed-event-line")

        myfs = open("out/"+vid+"/"+vid+"_"+langcode+".sbv", "w", encoding="utf-8")
        while divs:
            item = divs.pop(0)
            text = item.find("textarea").text
            startms = int(item.find("input", class_="event-start-time")["data-start-ms"])
            endms = int(item.find("input", class_="event-end-time")["data-end-ms"])

            myfs.write(timedelta_to_sbv_timestamp(timedelta(milliseconds=startms)) + "," + timedelta_to_sbv_timestamp(timedelta(milliseconds=endms)) + "\n" + text + "\n")
            
            del item
            del text
            del startms
            del endms
            if divs:
                myfs.write("\n")
        del divs
        myfs.close()
        del myfs

        if soup.find("li", id="captions-editor-nav-metadata")["data-state"] != "locked":
            metadata = {}

            try:
                metadata["title"] = soup.find("input", id="metadata-title")["value"]
            except KeyError:
                metadata["title"] = ""
            metadata["description"] = soup.find("textarea", id="metadata-description").text

            open("out/"+vid+"/"+vid+"_"+langcode+".json", "w", encoding="utf-8").write(dumps(metadata))
            del metadata

        del soup
        del langcode
        del vid
        del pparams

        jobs.task_done()

    return True