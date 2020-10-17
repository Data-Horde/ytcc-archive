from json import loads
from urllib.parse import unquote
from time import sleep

import requests

def getinitialdata(html: str):
    for line in html.splitlines():
        if line.strip().startswith('window["ytInitialData"] = '):
            return loads(line.split('window["ytInitialData"] = ', 1)[1].strip()[:-1])
    return {}

def getapikey(html: str):
    return html.split('"INNERTUBE_API_KEY":"', 1)[-1].split('"', 1)[0]

#extract latest version automatically
def getlver(initialdata: dict):
    try:
        return initialdata["responseContext"]["serviceTrackingParams"][2]["params"][2]["value"]
    except:
        return "2.20201002.02.01"

def fullyexpand(inputdict: dict, mysession: requests.session, continuationheaders: dict):
    lastrequestj = inputdict
    while "continuations" in lastrequestj.keys():
        while True:
            lastrequest = mysession.get("https://www.youtube.com/browse_ajax?continuation="+unquote(lastrequestj["continuations"][0]["nextContinuationData"]["continuation"]), headers=continuationheaders)
            if lastrequest.status_code == 200:
                break
            else:
                print("Non-200 API status code, waiting 30 seconds before retrying...")
                sleep(30)
        lastrequestj = lastrequest.json()[1]["response"]["continuationContents"]["gridContinuation"]
        inputdict["items"].extend(lastrequestj["items"])

    return inputdict