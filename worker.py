import requests
from time import sleep
from os import mkdir
from json import dumps
import threading

from shutil import make_archive, rmtree

from discovery import getmetadata
from export import getsubs

WORKER_VERSION  = 1
SERVER_BASE_URL = "http://localhost:5000"

class batchthread(threading.Thread):
    def run(self):
        item = self.getName()
        global recvids
        global recchans
        global recmixes
        global recplayl

        print("Video ID:", str(item).strip())
        while True:
            try:
                info = getmetadata(str(item).strip())
                break
            except BaseException as e:
                print(e)
                print("Error in retrieving information, waiting 10 minutes")
                sleep(600)

        # Add any discovered videos
        recvids.update(info[2])
        recchans.update(info[3])
        recmixes.update(info[4])
        recplayl.update(info[5])

        if info[0] or info[1]: # ccenabled or creditdata
            mkdir("out/"+str(item).strip())

        if info[1]: # creditdata
            open("out/"+str(item).strip()+"/"+str(item).strip()+"_published_credits.json", "w").write(dumps(info[1]))

        if info[0]: #ccenabled
            while True:
                gsres = False
                try:
                    gsres = getsubs(str(item).strip())
                except BaseException as e:
                    print(e)
                if gsres:
                    break
                else:
                    print("Error in retrieving subtitles, waiting 10 minutes")
                    sleep(600)

        return True


# Get a worker ID
while True:
    params = (
        ("worker_version", WORKER_VERSION),
    )
    idrequest = requests.get(SERVER_BASE_URL+"/worker/getID", params=params)

    if idrequest.status_code == 200:
        WORKER_ID = idrequest.text
        break
    else:
        print("Error in retrieving ID, will attempt again in 10 minutes")
        sleep(600)

while True:
    try:
        mkdir("out")
    except:
        pass

    recvids  = set()
    recchans = set()
    recmixes = set()
    recplayl = set()

    # Get a batch ID
    while True:
        params = (
            ("id", WORKER_ID),
            ("worker_version", WORKER_VERSION),
        )
        batchrequest = requests.get(SERVER_BASE_URL+"/worker/getBatch", params=params)

        if batchrequest.status_code == 200:
            batchinfo = batchrequest.json()
            break
        else:
            print("Error in retrieving batch assignment, will attempt again in 10 minutes")
            sleep(600)

    print("Received batch ID:", batchinfo["batchID"], "Content:", batchinfo["content"])

    # Process the batch
    batchcontent = requests.get(batchinfo["content"]).text.split("\n")


    threads = []
    for item in batchcontent:
        runthread = batchthread(name = item)
        runthread.start()
        threads.append(runthread)

    for x in threads:
        x.join()

    #https://stackoverflow.com/a/11968881

    # TODO: put the data somewhere...
    # TODO: put the discoveries somewhere...
    open("out/discoveries.json", "w").write(dumps({"recvids": sorted(recvids), "recchans": sorted(recchans), "recmixes": sorted(recmixes), "recplayl": sorted(recplayl)}))

    make_archive("out.zip", "zip", "out") #check this

    # while True:
    #     try:
    #         uploadr = requests.post("https://transfersh.com/"+str(batchinfo["batchID"])+".zip", data=open("out.zip"))
    #         if uploadr.status_code == 200:
    #             resulturl = uploadr.text
    #             break
    #     except BaseException as e:
    #         print(e)
    #         print("Encountered error in uploading results... retrying in 10 minutes")
    #         sleep(600)

    # Report the batch as complete (I can't think of a fail condition except for a worker exiting...)
    # TODO: handle worker exit
    while True:
        params = (
            ("id", WORKER_ID),
            ("worker_version", WORKER_VERSION),
            ("batchID", batchinfo["batchID"]),
            ("randomKey", batchinfo["randomKey"]),
            ("status", "c"),
            #("resulturl", resulturl),
        )
        statusrequest = requests.get(SERVER_BASE_URL+"/worker/updateStatus", params=params)

        if statusrequest.status_code == 200 and statusrequest.text == "Success":
            break
        else:
            print("Error in reporting success, will attempt again in 10 minutes")
            sleep(600)

    # TODO: clear the output directory
    rmtree("out")