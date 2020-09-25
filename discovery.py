from time import sleep
from typing import Dict
from json import loads

from switchable_request import get

backend = "requests"
failcnt = 0

langcodes = {"Afar": "aa", "Abkhazian": "ab", "Afrikaans": "af", "Akan": "ak", "all": "all", "Amharic": "am", "Aragonese": "an", "Arabic": "ar", "Aramaic": "arc", "Algerian Arabic": "arq", "Assamese": "as", "American Sign Language": "ase", "Asturian": "ast", "Avaric": "av", "Aymara": "ay", "Azerbaijani": "az", "Bashkir": "ba", "Belarusian": "be", "Bulgarian": "bg", "Bihari": "bh", "Bislama": "bi", "Bangla": "bn", "Tibetan": "bo", "Breton": "br", "Bosnian": "bs", "Catalan": "ca", "Cebuano": "ceb", "Choctaw": "cho", "Cherokee": "chr", "Corsican": "co", "Czech": "cs", "Church Slavic": "cu", "Welsh": "cy", "Danish": "da", "Danish (Denmark)": "da-DK", "German": "de", "German (Austria)": "de-AT", "German (Switzerland)": "de-CH", "German (Germany)": "de-DE", "Divehi": "dv", "Dzongkha": "dz", "Ewe": "ee", "Greek": "el", "English": "en", "English (United Arab Emirates)": "en-AE", "English (Canada)": "en-CA", "English (United Kingdom)": "en-GB", "English (Ireland)": "en-IE", "English (India)": "en-IN", "English (United States)": "en-US", "Esperanto": "eo", "Spanish": "es", "Spanish (Latin America)": "es-419", "Spanish (Argentina)": "es-AR", "Spanish (Chile)": "es-CL", "Spanish (Colombia)": "es-CO", "Spanish (Costa Rica)": "es-CR", "Spanish (Spain)": "es-ES", "Spanish (Mexico)": "es-MX", "Spanish (Nicaragua)": "es-NI", "Spanish (United States)": "es-US", "Estonian": "et", "Basque": "eu", "Persian": "fa", "Persian (Afghanistan)": "fa-AF", "Persian (Iran)": "fa-IR", "Fulah": "ff", "Finnish": "fi", "Filipino": "fil", "Fijian": "fj", "Faroese": "fo", "French": "fr", "French (Belgium)": "fr-BE", "French (Canada)": "fr-CA", "French (Switzerland)": "fr-CH", "French (France)": "fr-FR", "Western Frisian": "fy", "Irish": "ga", "Scottish Gaelic": "gd", "Galician": "gl", "Guarani": "gn", "Swiss German": "gsw", "Gujarati": "gu", "Hausa": "ha", "Hakka Chinese": "hak", "Hakka Chinese (Taiwan)": "hak-TW", "Hindi": "hi-Latn", "Hmong": "hmn", "Croatian": "hr", "Haitian Creole": "ht", "Hungarian": "hu", "Armenian": "hy", "Interlingua": "ia", "Indonesian": "id", "Interlingue": "ie", "Igbo": "ig", "Sichuan Yi": "ii", "Inupiaq": "ik", "Icelandic": "is", "Italian": "it", "Italian (Italy)": "it-IT", "Inuktitut": "iu", "Hebrew": "iw", "Japanese": "ja", "Javanese": "jv", "Georgian": "ka", "Kazakh": "kk", "Kalaallisut": "kl", "Khmer": "km", "Kannada": "kn", "Korean": "ko", "Korean (South Korea)": "ko-KR", "Kanuri": "kr", "Kashmiri": "ks", "Kurdish": "ku", "Kyrgyz": "ky", "Latin": "la", "Luxembourgish": "lb", "Lingala": "ln", "Lao": "lo", "Lithuanian": "lt", "Mizo": "lus", "Latvian": "lv", "Masai": "mas", "Malagasy": "mg", "Maori": "mi", "Miscellaneous languages": "mis", "Macedonian": "mk", "Malayalam": "ml", "Mongolian": "mn", "Manipuri": "mni", "Moldavian": "mo", "Marathi": "mr", "Malay": "ms", "Maltese": "mt", "Burmese": "my", "Nauru": "na", "Min Nan Chinese": "nan", "Min Nan Chinese (Taiwan)": "nan-TW", "Nepali": "ne", "Dutch": "nl", "Dutch (Belgium)": "nl-BE", "Dutch (Netherlands)": "nl-NL", "Norwegian Nynorsk": "nn", "Norwegian": "no", "not": "not", "Navajo": "nv", "Occitan": "oc", "Oromo": "om", "Odia": "or", "Punjabi": "pa", "Polish": "pl", "Polish (Poland)": "pl-PL", "Pashto": "ps", "Portuguese": "pt", "Portuguese (Brazil)": "pt-BR", "Portuguese (Portugal)": "pt-PT", "Quechua": "qu", "Romansh": "rm", "Rundi": "rn", "Romanian": "ro", "Romanian (Moldova)": "ro-MD", "Russian": "ru-Latn", "Russian (Russia)": "ru-RU", "Kinyarwanda": "rw", "Sanskrit": "sa", "Sardinian": "sc", "Sicilian": "scn", "Scots": "sco", "Sindhi": "sd", "Sherdukpen": "sdp", "Northern Sami": "se", "Sango": "sg", "Serbo-Croatian": "sh", "Sinhala": "si", "Slovak": "sk", "Slovenian": "sl", "Samoan": "sm", "Shona": "sn", "Somali": "so", "Albanian": "sq", "Serbian": "sr", "Serbian (Cyrillic)": "sr-Cyrl", "Serbian (Latin)": "sr-Latn", "Swati": "ss", "Southern Sotho": "st", "Sundanese": "su", "Swedish": "sv", "Swahili": "sw", "Tamil": "ta", "Telugu": "te", "Tajik": "tg", "Thai": "th", "Tigrinya": "ti", "Turkmen": "tk", "Tagalog": "tl", "Klingon": "tlh", "Tswana": "tn", "Tongan": "to", "Turkish": "tr", "Turkish (Turkey)": "tr-TR", "Tsonga": "ts", "Tatar": "tt", "Twi": "tw", "Ukrainian": "uk", "Urdu": "ur", "Uzbek": "uz", "Vietnamese": "vi", "Volap\\xFCk": "vo", "Wolof": "wo", "Xhosa": "xh", "Yiddish": "yi", "Yoruba": "yo", "Cantonese": "yue", "Cantonese (Hong Kong)": "yue-HK", "Chinese": "zh", "Chinese (China)": "zh-CN", "Chinese (Hong Kong)": "zh-HK", "Chinese (Simplified)": "zh-Hans", "Chinese (Simplified, China)": "zh-Hans-CN", "Chinese (Simplified, Singapore)": "zh-Hans-SG", "Chinese (Traditional)": "zh-Hant", "Chinese (Traditional, Hong Kong)": "zh-Hant-HK", "Chinese (Traditional, Taiwan)": "zh-Hant-TW", "Chinese (Singapore)": "zh-SG", "Chinese (Taiwan)": "zh-TW", "Zulu": "zu", "Hiri Motu": "ho", "Tok Pisin": "tpi", "Voro": "vor"}

def getmetadata(mysession, vid, allheaders):
    global backend
    global failcnt
    params = (
        ("v", vid),
    )

    while True:
        wpage = get("https://www.youtube.com/watch", params=params, mysession=mysession, backend=backend, http3headers=allheaders)

        if not """</div><div id="content" class="  content-alignment" role="main"><p class='largeText'>Sorry for the interruption. We have been receiving a large volume of requests from your network.</p>

<p>To continue with your YouTube experience, please fill out the form below.</p>""" in wpage.text and not wpage.status_code == 429 and 'window["ytInitialPlayerResponse"] = ' in wpage.text and 'window["ytInitialData"] = ' in wpage.text:
            break
        else:
            if backend == "requests" and failcnt > 30:
                backend = "http3"
                print("Captcha detected, switching discovery to HTTP3/QUIC")
            elif backend == "http3" and failcnt < 30:
                failcnt += 1
                print("Captcha detected, waiting 30 seconds... ", 30-failcnt, "attempts left until switching discovery to HTTP3/QUIC.")
                sleep(30)
            else:
                print("Captcha detected, waiting 30 seconds")
                sleep(30)

    wptext = wpage.text

    initplay = None
    initdata = None

    recvids  = set()
    recchans = set()
    recmixes = set()
    recplayl = set()

    ccenabled = False #default values
    creditdata = {}

    for line in wptext.splitlines():
        if line.strip().startswith('window["ytInitialPlayerResponse"] = '):
            initplay = loads(line.split('window["ytInitialPlayerResponse"] = ', 1)[1].strip()[:-1])

            if initplay["playabilityStatus"]["status"] == "ERROR":
                print(vid, "unavailable")
                return False, {}, recvids, recchans, recmixes, recplayl
            
            if "endscreen" in initplay.keys():
                if "endscreenRenderer" in initplay["endscreen"].keys():
                    for el in initplay["endscreen"]["endscreenRenderer"]:

                        if type(el) == Dict:
                            elint = el["endscreenElementRenderer"]

                            if "endscreenElementRenderer" in el.keys():
                                if elint["style"] == "VIDEO":
                                    recvids.add(elint["endpoint"]["watchEndpoint"]["videoId"])

                                elif elint["style"] == "CHANNEL":
                                    try:
                                        recchans.add(elint["endpoint"]["browseEndpoint"]["browseId"])
                                    except:
                                        print("Channel endscreen error")
                                        raise

                                elif elint["style"] == "PLAYLIST":
                                    recvids.add(elint["endpoint"]["watchEndpoint"]["videoId"])
                                    recplayl.add(elint["endpoint"]["watchEndpint"]["playlistId"])

            if "captions" in initplay.keys():
                ccenabled = "contribute" in initplay["captions"]["playerCaptionsRenderer"]
            else:
                ccenabled = False # if captions information is not present, community contributions are not enabled

            if "videoDetails" in initplay.keys():
                if "channelId" in initplay["videoDetails"].keys():
                    recchans.add(initplay["videoDetails"]["channelId"])
        elif line.strip().startswith('window["ytInitialData"] = '):
            initdata = loads(line.split('window["ytInitialData"] = ', 1)[1].strip()[:-1])
            if "contents" in initdata.keys(): #prevent exception
                try:
                    if "results" in initdata["contents"]["twoColumnWatchNextResults"]["secondaryResults"]["secondaryResults"].keys():
                        for recmd in initdata["contents"]["twoColumnWatchNextResults"]["secondaryResults"]["secondaryResults"]["results"]:
                            #auto is like the others
                            if "compactAutoplayRenderer" in recmd.keys():
                                recmd = recmd["compactAutoplayRenderer"]["contents"][0]

                            if "compactVideoRenderer" in recmd.keys():
                                recvids.add(recmd["compactVideoRenderer"]["videoId"])
                                try:
                                    recchans.add(recmd["compactVideoRenderer"]["channelId"])
                                except KeyError as e:
                                    try:
                                        recchans.add(recmd["compactVideoRenderer"]["longBylineText"]["runs"][0]["navigationEndpoint"]["browseEndpoint"]["browseId"])
                                    except KeyError as e:
                                        print("Channel extract error")
                                    #raise
                                    #print("Unable to extract channel:")
                                    #print(recmd["compactVideoRenderer"])

                            elif "compactPlaylistRenderer" in recmd.keys():
                                recplayl.add(recmd["compactPlaylistRenderer"]["playlistId"])
                                if "navigationEndpoint" in recmd["compactPlaylistRenderer"].keys():
                                    recvids.add(recmd["compactPlaylistRenderer"]["navigationEndpoint"]["watchEndpoint"]["videoId"])
                                if "navigationEndpoint" in recmd["compactPlaylistRenderer"]["shortBylineText"].keys():
                                    recchans.add(recmd["compactPlaylistRenderer"]["shortBylineText"]["navigationEndpoint"]["browseEndpoint"]["browseId"])

                            elif "compactRadioRenderer" in recmd.keys(): #mix playlist
                                recmixes.add(recmd["compactRadioRenderer"]["playlistId"])
                            # todo: find out if channels can be suggested
                except BaseException as e:
                    print(e)
                    print("Exception in discovery, continuing anyway")

            creditdata = {}
            try:
                mdinfo = initdata["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][1]["videoSecondaryInfoRenderer"]["metadataRowContainer"]["metadataRowContainerRenderer"]["rows"]
                for item in mdinfo:
                    if item["metadataRowRenderer"]["title"]["simpleText"].startswith("Caption author"): #the request to /watch needs to be in English for this to work
                        try:
                            desl = langcodes[item["metadataRowRenderer"]["title"]["simpleText"].split("(", 1)[1][:-1]]
                        except KeyError as e:
                            #print(e)
                            print("Language code conversion error, using language name")
                            desl = item["metadataRowRenderer"]["title"]["simpleText"].split("(", 1)[1][:-1]
                        creditdata[desl] = []
                        for itemint in item["metadataRowRenderer"]["contents"]:
                            creditdata[desl].append({"name": itemint["runs"][0]["text"], "channel": itemint["runs"][0]["navigationEndpoint"]["browseEndpoint"]["browseId"]})

            except KeyError as e:
                #print("Video does not have credits")
                pass
                #raise
                #print(e)
        
        if initplay and initdata:
            break

    return ccenabled, creditdata, recvids, recchans, recmixes, recplayl

if __name__ == "__main__":
    from sys import argv
    vidl = argv
    vidl.pop(0)
    for video in vidl:
        print(getmetadata(video))