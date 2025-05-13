
import requests
import datetime
import multiprocessing
import pwd
import os
import traceback
from msal import PublicClientApplication
from msal import SerializableTokenCache
from nydus.common.MCAccount import MCAccount
from nydus.common import validity
from nydus.common.AccessToken import AccessToken
from nydus.common.MCAccount import MCAccount
from nydus.common.AccountAuthTokens import AccountAuthTokens

# Data for the subprocess that does
# MSAL interactive auth
HOME_KEY = "HOME"
DBUS_KEY = "DBUS_SESSION_BUS_ADDRESS"
DBUS_VALUE = "unix:path=/run/user/{}/bus"
CHUNK_SIZE = 1024
SEND_DONE = "LASTCHUNKSENT"


# Utilities for authenticating to endpoints over the internet;
# Microsoft, Xbox, and Minecraft
# Used in getting and updating access tokens

SCOPES_NEEDED = ["XboxLive.signin"]

# Many of these constants are part of how the responses from various
# authentication endpoints are expected to be strutured.
# Usually if an expected key is missing, an error will be thrown and
# the program will move on to attempting the next account's authentication.
AUTHORITY_URL = "https://login.microsoftonline.com/consumers"

AUTH_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

MSAL_TOKEN_KEY = "access_token"
MSAL_ERROR_KEYS = ("error", "error_description", "correlation_id")
MSAL_EXPIRES_KEY = "expires_in"

XBL_URL = "https://user.auth.xboxlive.com/user/authenticate"
# Xbox expiry given as a timestamp
XB_EXPIRY_KEY = "NotAfter"
XB_TOKEN_KEY = "Token"

XSTS_URL = "https://xsts.auth.xboxlive.com/xsts/authorize"

MC_AUTH_URL = "https://api.minecraftservices.com/authentication/login_with_xbox"
MC_TOKEN_KEY = "access_token"
# Minecraft expiry given as seconds from now
MC_EXPIRES_KEY = "expires_in"

MC_PROFILE_URL = "https://api.minecraftservices.com/minecraft/profile"
MC_USERNAME_KEY = "name"
MC_UUID_KEY = "id"

# This structure defines how to find the xboxlive hash
# in the json returned from xboxlive authentication.
# Each tuple is either (key, dict) or (index, list)
# This tells you that the json object you're currently
# looking at is expected to be either
# 1) a dictionary and you should extract whatever is under the specified key
# or 2) a list and you should extract whatever is at the specified index
# Keep doing this recursively until you reach the end of the 'PARTS' tuple
# and you should have the hash.
XB_HASH_STEPS = (("DisplayClaims", dict), ("xui", dict), (0, list), ("uhs", dict))


"""
Xbox timestamps are mostly easy to parse with datetime, but end in
decimal fractions of a second and the letter Z. The
decimal fractions of a second may be 6 or 7 digits long, so can't
easily be parsed with datetime.
This function handles that.
ts: nonempty string representing a timestamp as pulled from the json
in response to an xbox auth request.
It should be in the form
%Y-%m-%dT%H%:%M:%S.%QZ
(the -, T, :, ., and Z are literal)
all the %X entries in this format are as in the datetime module, with
the exception of %Q. In Xbox timestamps, that part of the time
is fractions of a second, but may have either 6 digits or 7.
To make it compatible with datetime, we simply ignore the 7th
digit if present.
Returns a datetime representing the same time.
"""
def parse_xbox_timestamp(ts):
    if not validity.is_valid_xbox_timestamp(ts):
        raise ValueError("Object given to parse_xbox_timestamp was not an Xbox timestamp. Should have been of the form {} but was given {}".format(validity.XB_EXPIRY_FORMAT, ts))

    parts = ts.split(validity.XB_EXPIRY_SEPARATER)
    # We know there will be 2 parts because the timestamp validity check passed
    seconds_part = parts[0]
    fractional_part = parts[1]
    
    # Only keep 6 digits of the fractional part
    fractional_part = fractional_part.rstrip(validity.XB_EXPIRY_SUFFIX)
    # We have to slice out the first 6 digits because
    # formatting doesn't restrict the number of digits to 6
    fractional_part = "{:06}".format(fractional_part)[:6]

    fixed_ts = "{}{}{}{}".format(seconds_part, validity.XB_EXPIRY_SEPARATER, fractional_part, validity.XB_EXPIRY_SUFFIX)
    xbox_datetime = datetime.datetime.strptime(fixed_ts, validity.XB_EXPIRY_FORMAT)
    return xbox_datetime


"""
Both XboxLive authentication and Xbox Security Services (XSTS)
have the same JSON structure with a hash in the same place
in the response to the posts we will be making.
This function extracts the hash from the json return structure
in both cases.
"""
def get_xbox_hash(xbjson):

    json_object = xbjson

    for stage in XB_HASH_STEPS:
        if len(stage) != 2:
            raise IndexError("Variable defining location of Xbox hash was incorectly structured: {}".format(XBL_HASH_STEPS))

        wanted_type = stage[1]

        if not isinstance(json_object, wanted_type):
            raise TypeError("Expect json object to be {} but was {}".format(wanted_type, type(json_object)))

        if wanted_type == dict:
            wanted_key = stage[0]

            if not wanted_key in json_object:
                raise KeyError("Json object did not have expected key {}. It was {}".format(wanted_key, json_object))
            
            json_object = json_object[wanted_key]

        elif wanted_type == list:
            wanted_idx = stage[0]

            if len(json_object) - 1 < wanted_idx:
                raise IndexError("Json object did not have expected index {}. It was {}".format(wanted_idx, json_object))

            json_object = json_object[wanted_idx]

        else:
            raise TypeError("Variable defining location of Xbox hash must have each stage be either a list or dictionary. Was {}".format(XBL_HASH_STEPS))

    if not isinstance(json_object, str):
        raise ValueError("No string found at expected location of Xbox hash. Instead got {}".format(json_object))

    return json_object


"""
access_token: an AccessToken object obtained through MSAL. The caller
    needs to make sure it's valid and unexpired.
Returns an AccessToken object containing a token, expiry time, and a hash
for Xbox Live.
"""
def get_tok_xboxlive(access_token):
    if not isinstance(access_token, AccessToken):
        raise ValueError("An AccessToken class must be provided to get_tok_xboxlive. Instead, was given a {}".format(type(access_token)))

    if not validity.is_valid_msal_token(access_token.get_token()):
        raise ValueError("A valid MSAL token is needed to get an xboxlive token. Instead, was given {}".format(access_token.get_token()))


    xboxlive_props = {
        "Properties": {
            "AuthMethod": "RPS",
            "SiteName": "user.auth.xboxlive.com",
            "RpsTicket": "d={}".format(access_token.get_token())
        },
        "RelyingParty": "http://auth.xboxlive.com",
        "TokenType": "JWT"
    }

    xboxlive_resp = requests.post(XBL_URL, json=xboxlive_props, headers=AUTH_HEADERS)
    xbljson = xboxlive_resp.json()

    if XB_TOKEN_KEY in xbljson:
        xbltok = xbljson[XB_TOKEN_KEY]
    else:
        raise KeyError("Expected XboxLive authentication response to contain {}. Instead we could not get the token, and the response was {}".format(XB_TOKEN_KEY, xbljson))

    xblhash = get_xbox_hash(xbljson)
    
    if XB_EXPIRY_KEY in xbljson:
        xblexpiry = parse_xbox_timestamp(xbljson[XB_EXPIRY_KEY])
    else:
        raise KeyError("Expected XboxLive authentication response to contain {}. Instead we could not get the timestamp, and the response was {}".format(XB_EXPIRY_KEY, xbljson))

    xbl_at = AccessToken(xbltok, xblexpiry, tokhash=xblhash)
    return xbl_at


"""
access_token: an AccessToken object obtained through auth to XboxLive. The caller
    needs to make sure it's valid and unexpired.
Returns an AccessToken object containing a token, expiry time, and a hash
for XSTS.
"""
def get_tok_xsts(access_token):
    if not isinstance(access_token, AccessToken):
        raise ValueError("An AccessToken class must be provided to get_tok_xsts. Instead, was given a {}".format(type(access_token)))

    if not validity.is_valid_xboxlive_token(access_token.get_token()):
        raise ValueError("A valid XboxLive token is needed to get an XSTS token. Instead, was given {}".format(access_token.get_token()))


    xsts_props = {
        "Properties": {
            "SandboxId": "RETAIL",
            "UserTokens": [
                access_token.get_token()
            ]
        },
        "RelyingParty": "rp://api.minecraftservices.com/",
        "TokenType": "JWT"
    }

    xsts_resp = requests.post(XSTS_URL, json=xsts_props, headers=AUTH_HEADERS)
    xstsjson = xsts_resp.json()

    if XB_TOKEN_KEY in xstsjson:
        xststok = xstsjson[XB_TOKEN_KEY]
    else:
        raise KeyError("Expected XSTS authentication response to contain {}. Instead we could not get the token, and the response was {}".format(XB_TOKEN_KEY, xstsjson))

    xstshash = get_xbox_hash(xstsjson)
    
    if XB_EXPIRY_KEY in xstsjson:
        xstsexpiry = parse_xbox_timestamp(xstsjson[XB_EXPIRY_KEY])
    else:
        raise KeyError("Expected XSTS authentication response to contain {}. Instead we could not get the timestamp, and the response was {}".format(XB_EXPIRY_KEY, xstsjson))

    xsts_at = AccessToken(xststok, xstsexpiry, tokhash=xstshash)
    return xsts_at


"""
access_token: an AccessToken object obtained through auth to XSTS. The caller
    needs to make sure it's valid and unexpired.
Returns an AccessToken object containing a token and expiry time for Minecraft.
"""
def get_tok_minecraft(access_token):
    if not isinstance(access_token, AccessToken):
        raise ValueError("An AccessToken class must be provided to get_tok_minecraft. Instead, was given a {}".format(type(access_token)))

    if not validity.is_valid_xsts_token(access_token.get_token()):
        raise ValueError("A valid XSTS token is needed to get a Minecraft token. Instead, was given {}".format(access_token.get_token()))

    minecraft_props = {
        "identityToken": "XBL3.0 x={};{}".format(access_token.get_hash(), access_token.get_token())
    }

    minecraft_resp = requests.post(MC_AUTH_URL,
            json=minecraft_props, headers=AUTH_HEADERS)
    mc_json = minecraft_resp.json()

    if MC_TOKEN_KEY in mc_json:
        mc_access_tok = mc_json[MC_TOKEN_KEY]
    else:
        raise KeyError("Key {} was missing from Minecraft authentication response. Response was {}".format(MC_TOKEN_KEY, mc_json))

    if MC_EXPIRES_KEY in mc_json:
        mc_expiry_offset = mc_json[MC_EXPIRES_KEY]
    else:
        raise KeyError("Key {} was missing from Minecraft authentication response. Response was {}".format(MC_EXPIRES_KEY, mc_json))

    if isinstance(mc_expiry_offset, int) or validity.is_integer(mc_expiry_offset):
        expiry_dt = datetime.datetime.now() + datetime.timedelta(seconds = int(mc_expiry_offset))
    else:
        raise ValueError("Value of {} from Minecraft authentication response should be an integer representing seconds. Instead, was {}".format(MC_EXPIRES_KEY, mc_expiry_offset))

    mc_at = AccessToken(mc_access_tok, expiry_dt)
    return mc_at


"""
access_token: an AccessToken object containing a token obtained
through auth to Minecraft.
This function returns an MCAccount containing the username, uuid,
and token from access_token. These are needed for Minecraft launch.
"""
def get_minecraft_details(access_token):
    if not isinstance(access_token, AccessToken):
        raise ValueError("An AccessToken class must be provided to get_minecraft_details. Instead, was given a {}".format(type(access_token)))

    if not validity.is_valid_minecraft_token(access_token.get_token()):
        raise ValueError("A valid Minecraft token is needed to get Minecraft user details. Instead, was given {}".format(access_token.get_token()))

    profile_headers = AUTH_HEADERS.copy()
    profile_headers["Authorization"] = "Bearer {}".format(access_token.get_token())

    profile_resp = requests.get(MC_PROFILE_URL, headers=profile_headers)

    profile_json = profile_resp.json()

    mc_username = profile_json.get(MC_USERNAME_KEY)

    mc_uuid = profile_json.get(MC_UUID_KEY)

    if mc_username == None:
        raise KeyError("Key {} was missing from Minecraft profile response. Response was {}".format(MC_USERNAME_KEY, profile_json))

    if mc_uuid == None:
        raise KeyError("Key {} was missing from Minecraft profile response. Response was {}".format(MC_UUID_KEY, profile_json))

    return MCAccount(mc_username, mc_uuid, access_token.get_token())

"""
queue: a multiprocessing.Queue shared with the master process that spawned us
usernames: a list of strings; Microsoft account usernames to authenticate
app: an MSALPublicClientApplication which will be used to authenticate
    the Microsoft account
browser_uid: integer, uid of an account on the local system which
    will be used to do the interactive authentication (open a browser)
Function which handles invoking MSAL PublicClientApplication's
interactive token acquisition. Needs to be a separate function
because it has to run as a subprocess so it can downgrade
to a non-root user to open a browser, without affecting
the main process's root status.
"""
def msal_interactive_subproc(queue, username_list, app, browser_uid):

    pwdentry = pwd.getpwuid(browser_uid)
    home = pwdentry.pw_dir
    
    # Downgrade from root
    os.environ[DBUS_KEY] = DBUS_VALUE.format(browser_uid)
    os.environ[HOME_KEY] = home
    os.setuid(browser_uid)

    for username in username_list:
        # Auth
        result = app.acquire_token_interactive(scopes=SCOPES_NEEDED, login_hint=username)

    # Send the token cache containing the hopefully authd
    # account back to the main process
    cache = app.token_cache
    serial_cache = cache.serialize()

    # The cache for all the accounts is likely too
    # big for a single queue.put()

    chunks = len(serial_cache) // CHUNK_SIZE + 1

    for i in range(chunks):
        chunk = serial_cache[i*CHUNK_SIZE:(i+1)*CHUNK_SIZE]
        queue.put(chunk)

    queue.put(SEND_DONE)
    queue.close()


def msal_interactive_auth(username_list, app, cfg):
    # acquire_token_interactive doesn't work when run as root; it needs a browser.
    # we create a subprocess which can change its uid and environment independent
    # of the main process, then do the interactive auth using a browser as a
    # different user.
    queue = multiprocessing.Queue()
    p = multiprocessing.Process(
        target=msal_interactive_subproc,
        args=(queue, username_list, app, cfg.get_browser_uid())
    )
    p.start()
    
    new_cache = None
    while True:

        chunk = queue.get()

        if chunk == SEND_DONE:
            # We have everything from the subprocess
            break
        
        if new_cache == None:
            new_cache = chunk
        else:
            new_cache += chunk

    p.join()
    queue.close()

    # Get the token cache from the copy of the app
    # held by the subprocess and with it overwrite the
    # token cache for the app held by the main process
    app.token_cache.deserialize(new_cache)



"""
username: string, a Microsoft account username (email address)
app: an MSAL PublicClientApplication which will be used to authenticate the Microsoft account
cfg: a nydus ServerConfig or CliConfig instance
interactive_allowed: boolean. If True, this function may trigger a browser window to
    be opened so the Microsoft account can be authenticated manually. If False,
    this won't be done, but in that case the token can only be successfully obtained
    if MSAL already has the account authenticated.
This function acquires an MSAL token used for later authentication to Xbox and Minecraft.
It returns an AccessToken object containing that token.
"""
def get_tok_msal(username, app):
    if not validity.is_valid_microsoft_username(username):
        raise ValueError("Must pass a valid Microsoft username (email address) to get_tok_msal. Was given {}".format(username))

    if not isinstance(app, PublicClientApplication):
        raise ValueError("Must pass an MSAL PublicClientApplication to get_tok_msal. Got a {}".format(type(app)))

    accounts = app.get_accounts()
    
    result = None

    # Try to get the token from the existing cache
    if accounts:
        # Using .get so we'll receive None if the key is absent
        # Using .lower to ignore capitalisation inconsistencies
        found = [acc for acc in accounts if acc.get("username").lower() == username.lower()]

        if found:
            result = app.acquire_token_silent(SCOPES_NEEDED, account=found[0])

    if not result:
        raise ValueError("Could not authenticate account through MSAL: {}. Consider using interactive authentication, e.g. through Nydus Cli".format(username))
    if not MSAL_TOKEN_KEY in result:
        error_msg = ""
        error_msg = ", ".join([result[key] for key in MSAL_ERROR_KEYS if key in result])
        raise KeyError("No key {} in MSAL auth response for account {}. Error details: {}".format(MSAL_TOKEN_KEY, username, error_msg))

    token = result[MSAL_TOKEN_KEY]

    if MSAL_EXPIRES_KEY in result:
        expiry_offset = result[MSAL_EXPIRES_KEY]
    else:
        raise KeyError("Key {} was missing from MSAL authentication response. Response was {}".format(MSAL_EXPIRES_KEY, result))

    if isinstance(expiry_offset, int) or validity.is_integer(expiry_offset):
        expiry_dt = datetime.datetime.now() + datetime.timedelta(seconds = int(expiry_offset))
    else:
        raise ValueError("Value of {} from MSAL authentication response should be an integer representing seconds. Instead, was {}".format(MSAL_EXPIRES_KEY, expiry_offset))

    return AccessToken(token, expiry_dt)

"""
username: string, a Microsoft account username (email address)
app: an MSAL PublicClientApplication which will be used to authenticate the Microsoft account
cfg: a nydus ServerConfig or CliConfig instance
interactive_allowed: boolean. If True, this function may trigger a browser window to
    be opened so the Microsoft account can be authenticated manually. If False,
    this won't be done, but in that case the token can only be successfully obtained
    if MSAL already has the account authenticated.
Performs the whole authentication stream for Minecraft, beginning with the Microsoft
username and MSAL client given, proceeding through tokens for MSAL, Xbox Live, XSTS,
and Minecraft.
If successful, returns an AccountAuthTokens instance containing all data and tokens
about the account authenticated.
"""
def auth_stream(username, app):
    msal_at = get_tok_msal(username, app)
    xbl_at = get_tok_xboxlive(msal_at)
    xsts_at = get_tok_xsts(xbl_at)
    minecraft_at = get_tok_minecraft(xsts_at)
    acc = get_minecraft_details(minecraft_at)
    aat = AccountAuthTokens(username, msal_at, xbl_at, xsts_at, minecraft_at, acc)
    return aat


"""
username_list: a list of strings, each string being a Microsoft account username (email address)
app: an MSAL PublicClientApplication which will be used to authenticate the Microsoft
accounts in the given list.
cfg: a nydus ServerConfig or CliConfig instance
interactive_allowed: boolean. If True, this function may trigger browser windows
    opening so the Microsoft accounts can be authenticated manually. If False,
    no interactive authentication will be attempted, but in that case the authentication
    will only be done successfully for accounts already authenticated to MSAL.
Given a list of strings with each string representing a microsoft username,
this function attempts to complete the full authentication stream for
each user in turn.
Returns a dictionary. The keys of the dictionary are username strings. The value
for each username is either an AccountAuthTokens instance if the authentication
was successful, or None if it failed.
This function catches exceptions thrown by authentication procedures;
if attempting to authenticate an account causes an exception that authentication
will be considered failed, and the next account in the list will be attempted.
"""
def auth_all(username_list, app, cfg, interactive_allowed=True):
    assert isinstance(username_list, list), "Must pass a list of usernames to auth_all. Instead, a {} was passed.".format(type(username_list))
    for username in username_list:
        assert isinstance(username, str), "Expected a list of strings in the username list given to auth_all. Instead, found '{}' of type {}".format(username, type(username))

    assert isinstance(app, PublicClientApplication), "Must pass an MSAL PublicClientApplication to auth_all. Instead, a {} was passed.".format(type(app))

    print("Beginning authentication of accounts")

    auth_results = {}
    
    # If interactive MSAL authentication is allowed,
    # we have to do it at the same time for everyone,
    # so we do that first.

    if interactive_allowed:
        msal_interactive_auth(username_list, app, cfg)

    for username in username_list:
        try:
            tokens = auth_stream(username, app)
        except Exception:
            # Authentication failed somehow

            error_msg = traceback.format_exc()
            print("Failed to auth user {} with the following error:".format(username))
            print(error_msg)
            print()
            tokens = None
        auth_results[username] = tokens

    return auth_results


"""
client_id: string, an ID for a Microsoft client for MSAL to use
Creates a new MSAL PublicClientApplication using the provided client
ID and the default authority URL. This function should only
be called once; save the app and reuse it for the rest of your program's life
(including passing it to other functions such as auth_stream and get_tok_msal)
since this will allow you to take advantage of already
authenticated users that the app remembers, reducing the number
of times you need to manually re-authenticate.
Returns an MSAL PublicClientApplication.
"""
def create_msal_app(client_id):
    if not validity.is_valid_msal_cid(client_id):
        raise ValueError("Must provide a valid client ID to create_msal_app. Was given {}".format(client_id))

    app = PublicClientApplication(
        client_id,
        authority = AUTHORITY_URL,
        token_cache=SerializableTokenCache()
    )

    return app
