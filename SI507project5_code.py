## import statements
import requests
from requests_oauthlib import OAuth2Session
import webbrowser
import json
import logging, sys
import datetime
#from secret_data import app_id, app_secret

# for EventBrite oAuth2
APP_ID = "3LVEN2GBJZD45CRZA3"
APP_SECRET = "YB2G7QMYSKO5ADERKKNJCYYTNOMA6NJLGSY6LWEYAIMEBWW3QG"
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

        logging.debug("Response: {}".format(len(CACHE_DICTION[unique_ident])))
        return CACHE_DICTION[unique_ident]

## Make sure to run your code and write CSV files by the end of the program.


if __name__ == '__main__':
    baseurl = "https://www.eventbriteapi.com/v3"

    # data1
    endpt1 = baseurl+"/events/search/"
    date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=60)
    logging.debug("date: {} type: {}".format(date, type(date)))
    params1 = {
        "location.address" : "500 S State St, Ann Arbor, MI 48109",
        "location.within": str(150)+"mi",
        "start_date.range_end": date.isoformat()
    }
    logging.debug("params1: {}".format(params1))

    # data2
    
    # initialize to setup a session using OAuth2
    event_brite_finder = EventBriteFinder()
    event_brite_finder.make_request(endpt1, params1)
