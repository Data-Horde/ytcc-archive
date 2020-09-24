# YouTube Community Contributions Archiving Worker
Export YouTube community-contributed captioning to SBV files. Export YouTube community-contributed titles and descriptions to JSON. Export published caption credits to JSON.

## Setup
Ensure that `python` 3.8.5, `zip`, `curl`, and `rsync` are installed on your system. Install the Python module requirements in the requirements.txt file (`pip install -r requirements.txt`). Because the captioning editor is only available to logged-in users, you must specify the values of three session cookies for any Google account (`HSID`, `SSID`, and `SID`). You can get these cookie values by opening the developer tools on any youtube.com webpage, going to the "Application" (Chrome) or "Storage" (Firefox) tab, selecting "Cookies", and copying the required values. These values can be specified in the `config.json` file or as environment variables (`SSID`, `SID`, `HSID`). The `TRACKER_USERNAME` can also be specified in `config.json` or as an environment variable. This is the name that is used for the [dashboard](https://tracker.archiveteam.org/ext-yt-communitycontribs/).

## Primary Usage
### Archiving Worker:
After completing the above setup steps, simply run `python3 worker.py`.

### Heroku
A wrapper repo for free and easy deployment and environment configuration, as well automatic updates every 24-27.6 hours is available. Deploy up to 5 instances of it to a free Heroku account (total max runtime 550 hours) with no need for credit card verification by clicking the button below.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/Data-Horde/ytcc-archive-heroku)

## Bonus Features
### Export Captions and Titles/Descriptions Manually
Simply run `python3 ytcc-exporter.py` followed by a list of space-separated YouTube video IDs, and all community-contributed captioning and titles/descriptions in all languages will be exported.

### Discover Videos Manually
Simply run `python3 discovery.py` followed by a list of space-separated YouTube video IDs and a list of discovered video, channel and playlist IDs will be printed, as well as whether caption contributions are enabled.
