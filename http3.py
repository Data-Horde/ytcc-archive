import asyncio
from typing import cast
from urllib.parse import urlparse
from aioquic.h3.connection import H3_ALPN
from aioquic.asyncio.client import connect
from aioquic.quic.configuration import QuicConfiguration
from http3_base import HttpClient, prepare_response, perform_http_request

class HTTP3Response:
    def __init__(self, input) -> None:
        headers, content = input
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

        events = await perform_http_request(client=client, url=address, headers=headers)

        return HTTP3Response(prepare_response(events))

def get(url, headers={}, params={}):
    plist = []
    for item in params:
        #print(item)
        k, v = item
        plist.append(str(k)+"="+str(v))
    if plist:
        pstring = "?"+"&".join(plist)
    else:
        pstring = ""
    #print(url+pstring)
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(main(url+pstring, headers=headers))