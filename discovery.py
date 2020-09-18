import requests
from json import loads

def getmetadata(vid):
    params = (
        ("v", vid),
    )
    wpage = requests.get("https://www.youtube.com/watch", params=params)

    wptext = wpage.text

    initplay = None
    initdata = None

    recvids  = set()
    recchans = set()
    recmixes = set()
    recplayl = set()

    for line in wptext.splitlines():
        if line.strip().startswith('window["ytInitialPlayerResponse"] = '):
            initplay = loads(line.split('window["ytInitialPlayerResponse"] = ', 1)[1].strip()[:-1])

            if initplay["playabilityStatus"]["status"] == "ERROR":
                print(vid, "unavailable")
                return False, recvids, recchans, recmixes, recplayl
            
            if "endscreen" in initplay.keys():
                for el in initplay["endscreen"]["endscreenRenderer"]:

                    elint = el["endscreenElementRenderer"]

                    if elint["style"] == "VIDEO":
                        recvids.add(elint["endpoint"]["watchEndpoint"]["videoId"])

                    elif elint["style"] == "CHANNEL":
                        recchans.add(elint["endpoint"]["browseEndpoint"]["browseId"])

                    elif elint["style"] == "PLAYLIST":
                        recvids.add(elint["endpoint"]["watchEndpoint"]["videoId"])
                        recplayl.add(elint["endpoint"]["watchEndpint"]["playlistId"])

            if "captions" in initplay.keys():
                ccenabled = "contribute" in initplay["captions"]["playerCaptionsRenderer"]
            else:
                ccenabled = False # if captions information is not present, community contributions are not enabled

            recchans.add(initplay["videoDetails"]["channelId"])
        elif line.strip().startswith('window["ytInitialData"] = '):
            initdata = loads(line.split('window["ytInitialData"] = ', 1)[1].strip()[:-1])
            if "contents" in initdata.keys(): #prevent exception
                for recmd in initdata["contents"]["twoColumnWatchNextResults"]["secondaryResults"]["secondaryResults"]["results"]:
                    #auto is like the others
                    if "compactAutoplayRenderer" in recmd.keys():
                        recmd = recmd["compactAutoplayRenderer"]["contents"][0]

                    if "compactVideoRenderer" in recmd.keys():
                        recvids.add(recmd["compactVideoRenderer"]["videoId"])
                        recchans.add(recmd["compactVideoRenderer"]["channelId"])

                    elif "compactPlaylistRenderer" in recmd.keys():
                        recplayl.add(recmd["compactPlaylistRenderer"]["playlistId"])
                        recvids.add(recmd["compactPlaylistRenderer"]["navigationEndpoint"]["watchEndpoint"]["videoId"])
                        recchans.add(recmd["compactPlaylistRenderer"]["shortBylineText"]["navigationEndpoint"]["browseEndpoint"]["browseId"])

                    elif "compactRadioRenderer" in recmd.keys(): #mix playlist
                        recmixes.add(recmd["compactRadioRenderer"]["playlistId"])
                    # todo: find out if channels can be suggested
        
        if initplay and initdata:
            break

    return ccenabled, recvids, recchans, recmixes, recplayl

if __name__ == "__main__":
    from sys import argv
    vidl = argv
    vidl.pop(0)
    for video in vidl:
        print(getmetadata(video))