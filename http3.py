import asyncio
from typing import cast
from urllib.parse import urlparse
from aioquic.h3.connection import H3_ALPN
from aioquic.asyncio.client import connect
from aioquic.quic.configuration import QuicConfiguration
from http3_base import HttpClient, prepare_response, perform_http_request
from urllib.parse import urlparse

class HTTP3Response:
    def __init__(self, input) -> None:
        headers, content, url, redirect = input
        self.content = content
        try:
            self.text = content.decode()
        except:
            print("Text decoding error")
            self.text = ""
        self.headers = {}
        for k, v in headers.items():
            self.headers[k.decode()] = v.decode()
        try:
            self.status_code = int(headers[b":status"])
            self.url = url
        except:
            print("Status code not included as header, defaulting to 200")
            self.status_code = 200
        self.ok = self.status_code < 400

async def main(address, headers={}):
    parsed = urlparse(address)

    configuration = QuicConfiguration(
            is_client=True, alpn_protocols=H3_ALPN
        )

    async with connect(parsed.netloc, port=443, configuration=configuration, create_protocol=HttpClient) as client:
        client = cast(HttpClient, client)

        redirect = False
        while True:
            events = await perform_http_request(client=client, url=address, headers=headers)

            oheaders, ocontent = prepare_response(events)

            statuscode = int(oheaders[b":status"])
            if statuscode >= 300 and statuscode < 400 and b"location" in oheaders.keys():
                redirect = True
                origurl = address
                parsedorig = urlparse(origurl)
                address = oheaders[b"location"].decode()
                parsednew = urlparse(address)
                if not parsednew.scheme and not parsednew.netloc:
                    address = parsedorig.scheme + "://" + parsedorig.netloc + address
            else:
                break

        return HTTP3Response((oheaders, ocontent, address, redirect))

def get(url, headers={}, params={}):
    plist = []
    for item in params:
        k, v = item
        plist.append(str(k)+"="+str(v))
    if plist:
        pstring = "?"+"&".join(plist)
    else:
        pstring = ""
    url = url+pstring
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(main(url, headers=headers))