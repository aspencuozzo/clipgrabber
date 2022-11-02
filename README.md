# clipgrabber
clipgrabber is a TUI (text user interface) tool written in Python that allows you to batch retrieve links to clips made of a Twitch channel and send them to a text file.

![Screenshot](https://i.imgur.com/t7M21nw.png)

**Note:** clipgrabber is in alpha — there are features to be added, and likely bugs to be fixed. Please create an issue on the repository for any feature requests or bugs found.

## Requirements
- Python 3.10 or later
- python-dateutil 2.8.2 or later
- rich 12.6.0 or later

## Usage
`python3 -m pip install -r requirements.txt`\
`python3 clipgrabber.py`

The tool will guide you through the clip retreival process step-by-step. Please make sure you have [created a Developer Application on Twitch here](https://dev.twitch.tv/console/apps) and have its client ID and client secret ready, as the tool needs it to authenticate with the Twitch API.
