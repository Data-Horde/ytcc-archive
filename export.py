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

import requests

# https://docs.python.org/3/library/html.parser.html
from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.captions = []
        self.title = ""
        self.description = ""


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
        if tag == "input" and self.check_attr(attrs, "class", "yt-uix-form-input-text event-time-field event-start-time") and not ' data-segment-id="" ' in self.get_starttag_text():
            self.captions.append({"startTime": int(self.get_attr(attrs, "data-start-ms")), "text": ""})
        elif tag == "input" and self.check_attr(attrs, "class", "yt-uix-form-input-text event-time-field event-end-time") and not ' data-segment-id="" ' in self.get_starttag_text():
            self.captions[len(self.captions)-1]["endTime"] = int(self.get_attr(attrs, "data-end-ms"))
        elif tag == "input" and self.check_attr(attrs, "id", "metadata-title"):
            self.title = self.get_attr(attrs, "value")

    def handle_data(self, data):
        if self.get_starttag_text() and self.get_starttag_text().startswith("<textarea "):
            if 'name="serve_text"' in self.get_starttag_text() and not 'data-segment-id=""' in self.get_starttag_text():
                self.captions[len(self.captions)-1]["text"] += data
            elif 'id="metadata-description"' in self.get_starttag_text():
                self.description += data

def subprrun(jobs, headers):
    while not jobs.empty():
        langcode, vid = jobs.get()
        vid = vid.strip()
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

        inttext = page.text
        del page

        if 'id="reject-captions-button"' in inttext or 'id="reject-metadata-button"' in inttext: #quick way of checking if this page is worth parsing
            parser = MyHTMLParser()
            parser.feed(inttext)

            captiontext = False
            for item in parser.captions:
                if item["text"][:-9]:
                    captiontext = True

            if captiontext:
                myfs = open("out/"+vid+"/"+vid+"_"+langcode+".sbv", "w", encoding="utf-8")
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

            if parser.title or parser.description[:-16]:
                metadata = {}
                metadata["title"] = parser.title
                if metadata["title"] == False:
                    metadata["title"] = ""
                metadata["description"] = parser.description[:-16]
                open("out/"+vid+"/"+vid+"_"+langcode+".json", "w", encoding="utf-8").write(dumps(metadata))
                del metadata

        del inttext

        del langcode
        del vid
        del pparams

        jobs.task_done()

    return True