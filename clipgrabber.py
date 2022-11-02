from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import requests
from rich import print
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

def interactive_tui():
    console.print("\nWelcome to clipgrabber! (v0.0.1)", style='#000080', highlight=False)
    user_info = auth_interactive()
    client_id = user_info[0]
    oauth_token = user_info[1]
    broadcaster_id = broadcaster_id_interactive(client_id, oauth_token)
    date_range = get_dates_interactive()
    grab_clips_interactive(client_id, oauth_token, broadcaster_id, date_range)

def auth_interactive():
    client_id = Prompt.ask("Enter your Twitch application Client ID")
    client_secret = Prompt.ask("Enter your Twitch application Client Secret (hidden for privacy)", password=True)
    oauth_token = client_creds_auth(client_id, client_secret)
    if oauth_token is None:
        console.print("Your Twitch credentials are invalid. Please try again.\n", style="red")
        auth_interactive()
    else:
        console.print("Authentication successful!\n", style="green")
        return client_id, oauth_token

def broadcaster_id_interactive(client_id, oauth_token):
    broadcaster_name = Prompt.ask("Enter the name of the channel you would like to grab clips of")
    broadcaster_id = get_broadcaster_id(client_id, oauth_token, broadcaster_name)
    if broadcaster_id is None:
        console.print("Twitch channel not found. Please try again.\n", style="red")
    else:
        return broadcaster_id

def get_dates_interactive():
    start_date = None
    end_date = None
    date_range_choices = ["today", "yesterday", "this week", "this month", "this year", "custom range"]
    date_range = Prompt.ask("How far back would you like to grab clips?", choices=date_range_choices)
    if date_range != "custom range":
        end_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        match date_range:
            case "today":
                start_date = date.today().strftime("%Y-%m-%dT%H:%M:%SZ")
            case "yesterday":
                start_date = (date.today() - relativedelta(days = 1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            case "this week":
                start_date = (date.today() - relativedelta(weeks = 1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            case "this month":
                start_date = (date.today() - relativedelta(months = 1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            case "this year":
                start_date = (date.today() - relativedelta(years = 1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        while start_date is None:
            try:
                input_start_date = Prompt.ask("Enter the starting date (YYYY-MM-DD)")
                parsed_start_date = parse(input_start_date, yearfirst=True)
                if (parsed_start_date > date.today()):
                    raise ValueError("Date is in the future")
                else:
                    start_date = input_start_date
            except ValueError:
                console.print("Invalid date. Please ensure it is formatted correctly.\n", style="red")
        while end_date is None:
            try:
                input_end_date = Prompt.ask("Enter the ending date (YYYY-MM-DD)")
                parsed_end_date = parse(input_end_date, yearfirst=True)
                if (parsed_end_date > date.today()):
                    raise ValueError("Date is in the future")
                elif (parsed_end_date > start_date):
                    raise ValueError("End date is later than start date")
                else:
                    end_date = input_end_date
            except ValueError:
                console.print("Invalid date. Please ensure it is formatted correctly.\n", style="red")
    return start_date, end_date

def grab_clips_interactive(client_id, oauth_token, broadcaster_id, date_range):
    output_file = None
    while output_file is None:
        fname = Prompt.ask("What would you like to name the file?", default="clips.txt")
        if not fname.endswith(".txt"):
            fname += ".txt"
        output_file = open_file(fname)
        if (output_file is None):
            console.print("Could not open/write to file. Please try again.\n", style="red")
        
    sort_choices = ["oldest", "newest"]
    sort_order = Prompt.ask("How would you like to sort the clips in the file?", choices=sort_choices, default="oldest")
    clips = grab_clips(client_id, oauth_token, broadcaster_id, date_range)
    clips = sort_clips(clips, sort_order)
    write_to_file(clips, output_file)
    console.print("All done! " + str(len(clips)) + " clips were retrieved and sent to " + output_file.name, style="green")
    console.line()

def client_creds_auth(client_id, client_secret):
    params = {'client_id': client_id, 'client_secret': client_secret, 'grant_type': 'client_credentials'}
    r = requests.post(url = "https://id.twitch.tv/oauth2/token", params = params)
    if r.status_code == 200:
        return r.json()['access_token']
    else:
        return None

def get_broadcaster_id(client_id, oauth_token, broadcaster_name):
    headers = {'Authorization': 'Bearer ' + oauth_token, 'Client-Id': client_id}
    params = {'login': broadcaster_name}
    r = requests.get(url = "https://api.twitch.tv/helix/users", params = params, headers = headers)
    if not r.json()['data']:
        return None
    else:
        return str(r.json()['data'][0]['id'])

def grab_clips(client_id, oauth_token, broadcaster_id, date_range):
    cursor = ""
    clips = []
    started_at = date_range[0]
    ended_at = date_range[1]

    params = {'broadcaster_id': broadcaster_id, 'first': 100, 'started_at': started_at, "ended_at": ended_at}
    if cursor: params['after'] = cursor
    headers = {'Authorization': 'Bearer ' + oauth_token, 'Client-Id': client_id}

    while cursor is not None:
        r = requests.get(url = "https://api.twitch.tv/helix/clips", params = params, headers = headers)
        # If no clips are found
        try:
            clips += r.json()['data']
        except KeyError:
            console.log("Info dump\nParams: " + str(params) + "\nResponse " + str(r.status_code))
            return clips
        # Once we reach the end of the clips
        try:
            cursor = r.json()['pagination']['cursor']
            params['after'] = cursor
        except KeyError:
            cursor = None
    
    return clips

def sort_clips(clips, order):
    match order:
        case "oldest":
            clips.sort(key = lambda clip: datetime.strptime(clip['created_at'], "%Y-%m-%dT%H:%M:%SZ"))
        case "newest":
            clips.sort(key = lambda clip: datetime.strptime(clip['created_at'], "%Y-%m-%dT%H:%M:%SZ"), reverse=True)
        case "unpopular":
            clips.reverse()
    return clips

def open_file(fname):
    try:
        file = open(fname, "w")
        return file
    except OSError:
        return None

def write_to_file(clips, file):
    for clip in clips:
        file.write(clip['url'] + '\n')
    file.close()

if __name__ == "__main__":
    interactive_tui()