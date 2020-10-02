from requests import session
from json import loads
from urllib.parse import unquote

def getinitialdata(html: str):
    for line in html.splitlines():
        if line.strip().startswith('window["ytInitialData"] = '):
            return loads(line.split('window["ytInitialData"] = ', 1)[1].strip()[:-1])
    return {}

mysession = session()
#extract latest version automatically
try:
    lver = getinitialdata(mysession.get("https://www.youtube.com/").text)["responseContext"]["serviceTrackingParams"][2]["params"][2]["value"]
except:
    lver = "2.20201002.02.01"
mysession.headers.update({"x-youtube-client-name": "1", "x-youtube-client-version": lver, "Accept-Language": "en-US"})

def fullyexpand(inputdict: dict):
    lastrequestj = inputdict
    while "continuations" in lastrequestj.keys():
        lastrequest = mysession.get("https://www.youtube.com/browse_ajax?continuation="+unquote(lastrequestj["continuations"][0]["nextContinuationData"]["continuation"]))
        lastrequestj = lastrequest.json()[1]["response"]["continuationContents"]["gridContinuation"]
        inputdict["items"].extend(lastrequestj["items"])

    return inputdict
