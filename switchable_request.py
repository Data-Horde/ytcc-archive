import http3
def get(url: str, params: tuple = (), backend="requests", mysession=None, http3headers: dict ={}):
    if backend == "requests":
        return mysession.get(url, params=params)
    elif backend == "http3":
        #print(http3headers)
        return http3.get(url, headers=http3headers, params=params)