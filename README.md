# YouTube Community Contributed Captions Exporter
Export YouTube community-contributed captioning drafts to SBV files.

## Setup
Install the requirements in the requirements.txt file (`pip install -r requirements.txt`). Because the captioning editor is only available to logged-in users, you must specify the values of three session cookies for any Google account (`HSID`, `SSID`, and `SID`). You can get these cookie values by opening the developer tools on any youtube.com webpage, going to the "Application" (Chrome) or "Storage" (Firefox) tab, selecting "Cookies", and copying the required values.

## Usage
Simply run `python3 ytcc-exporter.py` followed by a list of space-separated YouTube video IDs, and all community-contributed captioning drafts in all languages will be exported.