from requests import session
from youtube_util import getinitialdata, fullyexpand, getapikey, getlver
from time import sleep

mysession = session()
#extract latest version automatically
homepage = mysession.get("https://www.youtube.com/").text

API_KEY = getapikey(homepage)

params = (
    ('key', API_KEY),
)

API_VERSION = getlver(getinitialdata(homepage))

continuationheaders = {"x-youtube-client-name": "1", "x-youtube-client-version": API_VERSION, "Accept-Language": "en-US"}

del homepage

def process_channel(channelid: str):
    playlists = set()
    shelfres  = set()
    channellist = set()

    # PLAYLISTS
    data = {"context":{"client":{"hl":"en","gl":"US","clientName":"WEB","clientVersion":API_VERSION}},"browseId":channelid,"params":"EglwbGF5bGlzdHM%3D"}
    while True:
        initdata = mysession.post("https://www.youtube.com/youtubei/v1/browse", params=params, json=data)
        if initdata.status_code == 200:
            initdata = initdata.json()
            break
        else:
            print("Non-200 API status code, waiting 30 seconds before retrying...")
            sleep(30)


    CHANNELS_ID = 0
    PLAYLISTS_ID = 0

    current = 0
    for tab in initdata["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]:
        if "tabRenderer" in tab.keys():
            if tab["tabRenderer"]["endpoint"]["commandMetadata"]["webCommandMetadata"]["url"].rsplit("/", 1)[-1] == "playlists":
                PLAYLISTS_ID = current
            elif tab["tabRenderer"]["endpoint"]["commandMetadata"]["webCommandMetadata"]["url"].rsplit("/", 1)[-1] == "channels":
                CHANNELS_ID = current
        current += 1

    del current

    shelflist = initdata["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][PLAYLISTS_ID]["tabRenderer"]["content"]["sectionListRenderer"]["contents"]

    for item in shelflist:
        itemint = item["itemSectionRenderer"]["contents"][0]
        if "shelfRenderer" in itemint.keys():
            shelfres.add(itemint["shelfRenderer"]["title"]["runs"][0]["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"])
        elif "gridRenderer" in itemint.keys():
            playlistsint = fullyexpand(itemint["gridRenderer"], mysession, continuationheaders)["items"]

            for playlist in playlistsint:
                playlists.add(playlist["gridPlaylistRenderer"]["playlistId"])
                if "shortBylineText" in playlist["gridPlaylistRenderer"].keys():
                    channellist.add(playlist["gridPlaylistRenderer"]["shortBylineText"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["browseId"])

    for item in shelfres:
        shelfiteminitdata = getinitialdata(mysession.get("https://www.youtube.com/"+str(item)).text)
        playlistsint = fullyexpand(shelfiteminitdata["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][PLAYLISTS_ID]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0]["gridRenderer"], mysession, continuationheaders)["items"]

        for playlist in playlistsint:
            playlists.add(playlist["gridPlaylistRenderer"]["playlistId"])
            if "shortBylineText" in playlist["gridPlaylistRenderer"].keys():
                channellist.add(playlist["gridPlaylistRenderer"]["shortBylineText"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["browseId"])

    # CHANNELS
    cshelfres = set()

    # PLAYLISTS
    data = {"context":{"client":{"hl":"en","gl":"US","clientName":"WEB","clientVersion":API_VERSION}},"browseId":channelid,"params":"EghjaGFubmVscw%3D%3D"}
    while True:
        initdata = mysession.post("https://www.youtube.com/youtubei/v1/browse", params=params, json=data).json()
        if initdata.status_code == 200:
            initdata = initdata.json()
            break
        else:
            print("Non-200 API status code, waiting 30 seconds before retrying...")
            sleep(30)
            
    shelflist = initdata["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][CHANNELS_ID]["tabRenderer"]["content"]["sectionListRenderer"]["contents"]

    for item in shelflist:
        itemint = item["itemSectionRenderer"]["contents"][0]
        if "shelfRenderer" in itemint.keys():
            cshelfres.add(itemint["shelfRenderer"]["title"]["runs"][0]["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"]["url"])
        elif "gridRenderer" in itemint.keys():
            chanlistint = fullyexpand(itemint["gridRenderer"], mysession, continuationheaders)["items"]

            for channel in chanlistint:
                channellist.add(channel["gridChannelRenderer"]["channelId"])

    for item in cshelfres:
        shelfiteminitdata = getinitialdata(mysession.get("https://www.youtube.com/"+str(item)).text)
        chanlistint = fullyexpand(shelfiteminitdata["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][CHANNELS_ID]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"][0]["gridRenderer"], mysession, continuationheaders)["items"]

        for channel in chanlistint:
            channellist.add(channel["gridChannelRenderer"]["channelId"])

    return {"playlists": playlists, "channels": channellist}

if __name__ == "__main__":
    from sys import argv
    chanl = argv
    chanl.pop(0)
    for channel in chanl:
        print(process_channel(channel))

# SAMPLES:
# UCqj7Cz7revf5maW9g5pgNcg lots of playlists
# UCRwczJ_nk1t9IGHyHfHbXRQ Nathaniel Bandy - created playlists only, featured channels only
# UCo8bcnLyZH8tBIH9V1mLgqQ the odd 1 is out - shelf, way too many subscriptions
# UCfXIV2vThxEF8Hq2OE17AeQ no playlists or channels featured

# UCJqV2-l0jqAa7uYN8IGJW7w TONS OF SUBSCRIPTIONS, no featured channels

# UC_1nZUpPS6jFv5Pn3f85CaA TONS OF SUBSCRIPTIONS, some featured channels

# UCJOh5FKisc0hUlEeWFBlD-w no subscriptions, plenty of featured channels

# UC7fjJERoGTs_eOKk-nn7RMw fair number of featured channels