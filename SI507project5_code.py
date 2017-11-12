## import statements
import requests
from requests_oauthlib import OAuth2Session
import webbrowser
import json
import logging, sys
import datetime
import csv
from secret_data import app_id, app_secret

# for EventBrite oAuth2
APP_ID = app_id
APP_SECRET = app_secret
AUTHORIZATION_BASE_URL = "https://www.eventbrite.com/oauth/authorize"
TOKEN_URL = "https://www.eventbrite.com/oauth/token"
REDIRECT_URI = 'https://www.programsinformationpeople.org/runestone/oauth'

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

## CACHING SETUP

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
CACHE_FNAME = 'cache_file.json'
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
EXPIRE_IN_DAYS = 1

# -----------------------------------------------------------------------------
# Load cache file
# -----------------------------------------------------------------------------
try:
    with open(CACHE_FNAME, 'r') as cache_file:
        cache_json = cache_file.read()
        CACHE_DICTION = json.loads(cache_json)
except:
    CACHE_DICTION = {}

def clear_cache():
    CACHE_DICTION.clear()

def has_cache_expired(timestamp_str):
    """Check if cache timestamp is over expire_in_days old"""
    # gives current datetime
    now = datetime.datetime.now()

    # datetime.strptime converts a formatted string into datetime object
    cache_timestamp = datetime.datetime.strptime(timestamp_str, DATETIME_FORMAT)

    # subtracting two datetime objects gives you a timedelta object
    delta = now - cache_timestamp
    delta_in_days = delta.days

    # now that we have days as integers, we can just use comparison
    # and decide if cache has expired or not
    if delta_in_days <= EXPIRE_IN_DAYS:
        return False
    else:
        return True

def get_from_cache(unique_ident):
    """If URL exists in cache and has not expired, return the html, else return None"""
    if unique_ident in CACHE_DICTION:
        unique_ident_dict = CACHE_DICTION[unique_ident]

        if has_cache_expired(unique_ident_dict['timestamp']):
            # also remove old copy from cache
            del CACHE_DICTION[unique_ident]
            html = None
        else:
            resp = CACHE_DICTION[unique_ident]['resp']
    else:
        resp = None
    return resp

def set_in_cache(unique_ident, resp):
    """Add URL and html to the cache dictionary, and save the whole dictionary to a file as json"""
    CACHE_DICTION[unique_ident] = {
        'resp': resp,
        'timestamp': datetime.datetime.now().strftime(DATETIME_FORMAT),
    }

    with open(CACHE_FNAME, 'w') as cache_file:
        cache_json = json.dumps(CACHE_DICTION)
        cache_file.write(cache_json)

## ADDITIONAL CODE for program should go here...
## Perhaps authentication setup, functions to get and process data, a class definition... etc.

class EventBriteFinder(object):
    def __init__(self):
        init_info = self.__start_session()
        self.session = init_info[0]
        self.token = init_info[1]["access_token"]

        if (self.session is None) or (self.token is None):
            print("EventBrite Session not properly setup. Session: {} Token: {}".format(self.session, self.token))

    def __start_session(self):
        initial_session = None
        # 0 - get token from cache
        try:
            token = self.__get_saved_token()
        except FileNotFoundError:
            token = None

        if token:
            initial_session = OAuth2Session(APP_ID, token=token)

        else:
            # 1 - session
            initial_session = OAuth2Session(APP_ID, redirect_uri=REDIRECT_URI)

            # 2 - authorization
            authorization_url, state = initial_session.authorization_url(AUTHORIZATION_BASE_URL)
            print('Opening browser to {} for authorization'.format(authorization_url))
            webbrowser.open(authorization_url)

            # 3 - token
            #redirect_response = input('Paste the full redirect URL here: ')
            token = initial_session.fetch_token(TOKEN_URL, client_secret=APP_SECRET,
                                                authorization_response=authorization_url)

            # 4 - save token
            self.__save_token(token)

        logging.debug("Session: {} Token: {}".format(initial_session, token))
        return [initial_session, token]

    def __get_saved_token(self):
        with open('token.json', 'r') as f:
            token_json = f.read()
            token_dict = json.loads(token_json)

            return token_dict

    def __save_token(self, token_dict):
        with open('token.json', 'w') as f:
            token_json = json.dumps(token_dict)
            f.write(token_json)

    def __params_unique_combination(self, baseurl, params_d, private_keys=["token"]):
        alphabetized_keys = sorted(params_d.keys())
        res = []
        for k in alphabetized_keys:
            if k not in private_keys:
                res.append("{}-{}".format(k, params_d[k]))
        return baseurl + "_".join(res)

    def make_request(self, baseurl, params=None):
        # we use 'global' to tell python that we will be modifying this global variable
        if not params:
            params = {}
        params["token"] = self.token

        unique_ident = self.__params_unique_combination(baseurl, params)
        if unique_ident not in CACHE_DICTION:
            logging.debug("unique_ident: {} Not in Cache, request it".format(unique_ident))
            resp = self.session.get(baseurl, params=params)
            resp_text = json.loads(resp.text)
            set_in_cache(unique_ident, resp_text)

        return CACHE_DICTION[unique_ident]

    def write_data_to_csv(self, file_name, data_list, data_header):
        with open(file_name, 'w') as csv_file:
            wr = csv.writer(csv_file)
            wr.writerow(data_header)
            logging.debug("data_list: {} length: {}".format(data_list, len(data_list)))
            wr.writerows(data_list)

## Make sure to run your code and write CSV files by the end of the program.


if __name__ == '__main__':
    baseurl = "https://www.eventbriteapi.com/v3"

    # data1
    endpt1 = baseurl+"/events/search/"
    date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=60)
    logging.debug("date: {} type: {}".format(date, type(date)))
    params1 = {
        "location.address": "500 S State St, Ann Arbor, MI 48109",
        "location.within": str(150)+"mi",
        "start_date.range_end": date.isoformat()
    }
    logging.debug("params1: {}".format(params1))

    # data2
    # initialize to setup a session using OAuth2
    event_brite_finder = EventBriteFinder()
    ev_results1 = event_brite_finder.make_request(endpt1, params1)
    logging.debug("Response: {}".format(len(ev_results1['resp'])))
    events = ev_results1['resp']['events']

    # Write data to CSV
    name = "None"
    org_id = "None"
    start = "None"
    header1 = ["Name", "Org ID", "Start Date"]
    data1_list = []
    for event in events:
        name = event["name"]["text"]
        org_id = event["organizer_id"]
        start = event["start"]["local"]
        data1_list.append([name, org_id, start])
    event_brite_finder.write_data_to_csv("Events_Around_AnnArbor.csv", data1_list, header1)


    # for each event find organizer name and SNS information
    header2 = ["Org ID", "Name", "Twitter", "Facebook"]
    data2_list = []
    for event in events:
        ev_org_id = "None"
        ev_org_id = event['organizer_id']
        # logging.debug("ev_org_id: {}".format(ev_org_id))
        endpt2 = baseurl+"/organizers/{}/".format(ev_org_id)
        # request data
        ev_results2 = event_brite_finder.make_request(endpt2)
        org_info = ev_results2['resp']
        org_name = "None"
        org_twitter = "None"
        org_facebook = "None"
        if 'name' in org_info:
            org_name = org_info['name']
        if 'twitter' in org_info:
            org_twitter = org_info['twitter']
        if 'facebook' in org_info:
            org_facebook = org_info['facebook']
        if org_name is None:
            org_name = "None"
        logging.debug("Name: {} twitter: {} facebook: {}".format(org_name, org_twitter, org_facebook))
        data2_list.append([ev_org_id, org_name, org_twitter, org_facebook])

    # Write data to CSV
    event_brite_finder.write_data_to_csv("Organization_Info.csv", data2_list, header2)



