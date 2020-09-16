# YouTube Community Contributions Archiving Worker
Export YouTube community-contributed captioning drafts to SBV files. Export YouTube community-contributed titles and descriptions to JSON (coming soon).

## Setup
Install the requirements in the requirements.txt file (`pip install -r requirements.txt`). Because the captioning editor is only available to logged-in users, you must specify the values of three session cookies for any Google account (`HSID`, `SSID`, and `SID`). You can get these cookie values by opening the developer tools on any youtube.com webpage, going to the "Application" (Chrome) or "Storage" (Firefox) tab, selecting "Cookies", and copying the required values.

## Usage
### Export Captions
Simply run `python3 ytcc-exporter.py` followed by a list of space-separated YouTube video IDs, and all community-contributed captioning drafts in all languages will be exported.

### Discover videos
Simply run `python3 discovery.py` followed by a list of space-separated YouTube video IDs and a list of discovered video, channel and playlist IDs will be printed, as well as whether caption contributions are enabled.
