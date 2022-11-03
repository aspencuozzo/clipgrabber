from contextlib import suppress
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import isoparse
import json
import requests
from rich import print
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

# ----------- #
# Interactive #
# ----------- #

def interactive_tui():
    using_tool = True
    console.print("\nWelcome to clipgrabber! (v1.0.0)", style='bold #000080', highlight=False)
    user_info = auth_interactive()
    client_id = user_info[0]
    oauth_token = user_info[1]
    while (using_tool):
        broadcaster_id = broadcaster_id_interactive(client_id, oauth_token)
        date_range = get_dates_interactive()
        game_filter = game_filter_interactive(client_id, oauth_token)
        creator_filter = Prompt.ask("Filter by clip creator (leave blank to skip)")
        title_filter = Prompt.ask("Filter by text in title (leave blank to skip)")
        retrieve_clips_interactive(client_id, oauth_token, broadcaster_id, date_range, game_filter, creator_filter, title_filter)
        using_tool = Confirm.ask("Would you like to retrieve more clips?")

    console.print("Thank you for using clipgrabber!", style='bold #000080')

def auth_interactive():
    oauth_token = None
    client_id = None
    client_secret = None

    # First, try to load from credentials.json (if it exists)
    creds_file = open_file("credentials.json", "r")
    if creds_file is not None:
        credentials = json.load(creds_file)
        console.print("Loading from credentials.json")
        try:
            client_id = credentials['client_id']
            client_secret = credentials['client_secret']
            creds_file.close()
        except KeyError:
            console.print("credentials.json could not be read. Please make sure it is formatted correctly.\n", style="bold red")
            creds_file.close()
            creds_file = None

    while oauth_token is None:
        if creds_file is None:
            client_id = Prompt.ask("Enter your Twitch application Client ID")
            client_secret = Prompt.ask("Enter your Twitch application Client Secret (hidden for privacy)", password=True)
        oauth_token = client_creds_auth(client_id, client_secret)
        if oauth_token is None:
            console.print("Your Twitch credentials are invalid. Please try again.\n", style="bold red")
            if creds_file is not None: creds_file = None

    console.print("Authentication successful!\n", style="bold green")
    return client_id, oauth_token

def broadcaster_id_interactive(client_id, oauth_token):
    broadcaster_id = None
    while broadcaster_id is None:
        broadcaster_name = Prompt.ask("Enter the name of the channel you would like to retrieve clips of")
        broadcaster_id = get_broadcaster_id(client_id, oauth_token, broadcaster_name)
        if broadcaster_id is None:
            console.print("Twitch channel not found. Please try again.", style="red")
    return broadcaster_id

def get_dates_interactive():
    start_date = ''
    end_date = ''
    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    today_end = datetime.now().replace(hour=23, minute=59, second=59)
    default_options = ["today", "yesterday", "this week", "this month", "this year", "lifetime"]

    while not start_date and not end_date:
        date_range = Prompt.ask("What timeframe would you like to retrieve clips from? (see README for options)")

        # Custom date
        with suppress(Exception):
            start_date = isoparse(date_range)
            # This is kinda scuffed and there might be a better way to do this
            # Also for some reason isoparse processes YYYYMMDD but not YYYYMM, hence the length 8 case
            match len(date_range):
                # User input a year
                case 4: end_date = start_date + relativedelta(years = 1, seconds = -1)
                # User input a month
                case 7: end_date = start_date + relativedelta(months = 1, seconds = -1)
                # User input a day
                case 8, 10: end_date = start_date + relativedelta(days = 1, seconds = -1)
            break

         # Other default date options
        if date_range in default_options:
            end_date = today_end
            match date_range:
                case "today":
                    start_date = today_start
                case "yesterday":
                    start_date = today_start - relativedelta(days = 1)
                    end_date = today_start - relativedelta(seconds = -1)
                case "this week":
                    start_date = today_start - relativedelta(weeks = 1)
                case "this month":
                    start_date = today_start.replace(day = 1)
                case "this year":
                    start_date = today_start.replace(day = 1, month = 1)
                case "lifetime":
                    start_date = datetime(2016, 1, 1)

        # Custom date range
        elif date_range == "custom range":
            while not start_date:
                try:
                    input_start_date = Prompt.ask("Enter the starting date (YYYY-MM-DD)")
                    parsed_start_date = isoparse(input_start_date).replace(hour=0, minute=0, second=0)
                    if (parsed_start_date > today_end):
                        raise ValueError("Date cannot be in the future.")
                    else:
                        start_date = parsed_start_date
                except ValueError as error:
                    error_message = str(error)
                    if error_message != "Date cannot be in the future.":
                        error_message = "Please ensure it is formatted correctly."
                    console.print("Invalid date. " + error_message, style="red")
            while not end_date:
                try:
                    input_end_date = Prompt.ask("Enter the ending date (YYYY-MM-DD)")
                    parsed_end_date = isoparse(input_end_date).replace(hour=23, minute=59, second=59)
                    if (parsed_end_date < start_date):
                        raise ValueError("End date cannot be earlier than start date.")
                except ValueError as error:
                    error_message = str(error)
                    if error_message != "End date cannot be earlier than start date.":
                        error_message = "Please ensure it is formatted correctly."
                    console.print("Invalid date. " + error_message, style="red")

        # Invalid response
        else:  
            console.print("Invalid response. Please refer to the README for valid options.", style="red")

    start_date = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                    
    return start_date, end_date

def game_filter_interactive(client_id, oauth_token):
    game_filter = None
    while game_filter is None:
        game_filter = Prompt.ask("Filter by game (leave blank to skip)")
        if game_filter:
            game_filter = get_game_id(client_id, oauth_token, game_filter)
    return game_filter

def retrieve_clips_interactive(client_id, oauth_token, broadcaster_id, date_range, game_filter, creator_filter, title_filter):
    output_file = None

    sort_choices = ["oldest", "newest", "popular", "unpopular"]
    sort_order = Prompt.ask("How would you like to sort the clips in the file?", choices=sort_choices, default="popular")
    
    while output_file is None:
        fname = Prompt.ask("What would you like to name the file?", default="clips.txt")
        if not fname.endswith(".txt"):
            fname += ".txt"
        output_file = open_file(fname, "w")
        if (output_file is None):
            console.print("Could not open/write to file. Please try again.\n", style="red")

    with console.status("[bold blue]Retrieving clips"):
        clips = retrieve_clips(client_id, oauth_token, broadcaster_id, date_range)

    if game_filter or creator_filter:
        clips = filter_clips(clips, creator_filter, game_filter, title_filter)

    if clips is not None:
        clips = sort_clips(clips, sort_order)
        write_to_file(clips, output_file)

        if len(clips) == 1: total_clips_message = str(len(clips)) + " clip was"
        else: total_clips_message = str(len(clips)) + " clips were"
        console.print("All done! " + total_clips_message + " retrieved and sent to " + output_file.name, style="bold green")
        console.line()
    else:
        console.print("No clips were found with the specified filters.\n", style="bold red")

# ----------- #
#     API     #
# ----------- #     
 
# Obtain oauth token with client_id and client_secret
def client_creds_auth(client_id, client_secret):
    params = {'client_id': client_id, 'client_secret': client_secret, 'grant_type': 'client_credentials'}
    r = requests.post(url = "https://id.twitch.tv/oauth2/token", params = params)
    if r.status_code == 200:
        return r.json()['access_token']
    else:
        return None

# Get broadcaster_id from broadcaster_name
def get_broadcaster_id(client_id, oauth_token, broadcaster_name):
    headers = {'Authorization': 'Bearer ' + oauth_token, 'Client-Id': client_id}
    params = {'login': broadcaster_name}
    r = requests.get(url = "https://api.twitch.tv/helix/users", params = params, headers = headers)
    if not r.json()['data']:
        return None
    else:
        return str(r.json()['data'][0]['id'])

# Get game_id from game_name
def get_game_id(client_id, oauth_token, game_name):
    headers = {'Authorization': 'Bearer ' + oauth_token, 'Client-Id': client_id}
    params = {'name': game_name}
    r = requests.get(url = "https://api.twitch.tv/helix/games", params = params, headers = headers)
    if not (r.json()['data']):
        console.print("Game not found. Please enter the [bold]exact[/bold] title of the game.", style="red")
        return None
    else:
        returned_game = r.json()['data'][0]
        if game_name.casefold() != returned_game['name'].casefold():
            if not Confirm.ask("Is [bold]" + returned_game['name'] + "[/bold] the correct game?"):
                console.print("[red]Sorry about that. Make sure the game name is [bold]exactly[/bold] how it's spelled on Twitch.[/red]\n")
                return None
        return returned_game['id']

# Iterative function to retrieve all clips with specified filters
def retrieve_clips(client_id, oauth_token, broadcaster_id, date_range):
    cursor = ""
    clips = []
    started_at = date_range[0]
    ended_at = date_range[1]

    headers = {'Authorization': 'Bearer ' + oauth_token, 'Client-Id': client_id}
    params = {'broadcaster_id': broadcaster_id, 'first': 100, 'started_at': started_at, "ended_at": ended_at}
    if cursor: params['after'] = cursor

    while cursor is not None:
        r = requests.get(url = "https://api.twitch.tv/helix/clips", params = params, headers = headers)
        # If no clips are found
        try:
            clips += r.json()['data']
        except KeyError:
            return clips
        # Once we reach the end of the clips
        try:
            cursor = r.json()['pagination']['cursor']
            params['after'] = cursor
        except KeyError:
            cursor = None
    
    return clips

# Modify the clips list to match provided filters
def filter_clips(clips, creator_filter='', game_filter='', title_filter=''):
    for clip in clips[:]:
        if (creator_filter and clip['creator_name'].casefold() != creator_filter.casefold()
            or game_filter and clip['game_id'] != game_filter
            or title_filter and title_filter.casefold() not in clip['title'].casefold()):
            clips.remove(clip)
    return clips
        
# Sort clips by specified order before we write them to file
def sort_clips(clips, order):
    match order:
        case "oldest":
            clips.sort(key = lambda clip: datetime.strptime(clip['created_at'], "%Y-%m-%dT%H:%M:%SZ"))
        case "newest":
            clips.sort(key = lambda clip: datetime.strptime(clip['created_at'], "%Y-%m-%dT%H:%M:%SZ"), reverse=True)
        case "unpopular":
            clips.reverse()
    return clips

# Attempt to open file before `writing` to ensure we have permission
def open_file(fname, perms):
    try:
        file = open(fname, perms)
        return file
    except OSError:
        return None

# Write to specified file (only runs once we have confirmed permission)
def write_to_file(clips, file):
    for clip in clips:
        file.write(clip['url'] + '\n')
    file.close()

# ---------- #
#    Main    #
# ---------- #     
if __name__ == "__main__":
    interactive_tui()