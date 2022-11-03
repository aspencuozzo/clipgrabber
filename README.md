# clipgrabber
clipgrabber is a TUI (text user interface) tool written in Python that allows you to batch retrieve links to clips made of a Twitch channel and send them to a text file.

![Screenshot](https://i.imgur.com/LsAO513.png)

## Requirements
- Python 3.10 or later
- python-dateutil 2.8.2 or later
- rich 12.6.0 or later

## Usage
`python3 -m pip install -r requirements.txt`\
`python3 clipgrabber.py`

The tool will guide you through the clip retreival process step-by-step. Please make sure you have [created a Developer Application on Twitch here](https://dev.twitch.tv/console/apps) and have its client ID and client secret ready, as the tool needs it to authenticate with the Twitch API.

### Timeframe options
`today`, `this week`, `this month`, `this year`, `lifetime`, `custom range`, any ISO-8601 formatted date (YYYY, YYYY-MM, or YYYY-MM-DD)\
`custom range` lets you specify two ISO-8601 formatted dates to search between.

**Note:** clipgrabber searches for the dates the *clips* were created, not the dates of the source streams. Twitch does not expose that info in the API - it is possible to get it from the `video_id` returned, but this happens only if a clip's source VOD is still available. VODs are stored for a maximum of two months (60 days for partners, Turbo and Prime users; 14 days for affiliates; 7 days for others), so this would probably not be a very useful filter to add.

### Easier authentication
I have added a feature where the tool will autoload your credentials if you have them saved in a `credentials.json` file located in the same place you are running the tool from. There is an example file in the repository with the specific formatting you must use. (If you use the example file directly, make sure to rename it to simply `credentials.json`.)

Please keep in mind that this is obviously not secure, as if an attacker were to ever get into your computer they could easily steal your client secret. Unlike oauth tokens, client secrets do not expire. Use this feature at your own risk.