
from nydus.common import netauth
from nydus.common.Config import Config
from nydus.common.allocater import AllocEngine
from nydus.common.SSHLogins import SSHLogins
from nydus.common import validity
from msal import PublicClientApplication
import threading

# Tools used by both Nydus Server and Nydus Cli
# in the process of interacting with Allocations

# 30 minutes in seconds
CLEANUP_PERIOD = 30 * 60
CLEANUP_DT = datetime.timedelta(seconds=CLEANUP_PERIOD)


"""
cfg: the ServerConfig instance for use on this server
app: the MSAL PublicClientApplication this server will use in authentication
Gets Microsoft usernames out of the accounts file, attempts to authenticate them,
(interactively; the user needs to manully log accounts in when the server starts)
creates the allocation db file using the accounts which authd successfully.
The Config instance passed must specificall have accounts_file and alloc_file,
which are both stored by ServerConfig and by CliConfig.
Returns nothing
"""
def initialise_accounts(cfg, app):

    if not isinstance(cfg, Config):
        raise TypeError("Must pass a Nydus Config instance to initialise_accounts. Got a {}".format(type(cfg)))

    if not isinstance(app, PublicClientApplication):
        raise TypeError("Must pass an MSAL PublicClientApplication to initialise_accounts. Got a {}".format(type(app)))

    username_list = read_accounts_file(cfg.get_accounts_file())
    auth_dict = netauth.auth_all(username_list, app, interactive_allowed=True)
    authed_aats = [aat for aat in auth_dict.values() if aat != None]
    failed_aats = [aat for aat in auth_dict.values() if aat == None]
    print("From {} requested Microsoft accounts, the following {} were authenticated.".format(len(username_list), len(authed_aats)))
    for aat in authed_aats:
        print(aat.get_microsoft_username())

    print("The following {} failed authentication.".format(len(failed_aats)))
    for aat in failed_aats:
        print(aat.get_microsoft_username())

    # This is the one instance where no locking is required
    # before running the AllocEngine, because no threads
    # will be spawned until the main server loop is reached.
    alloc_engine = AllocEngine(cfg.get_alloc_file())

    # Create a whole new alloc db only if nothing is already
    # in the file.
    # Otherwise proceed with the file's contents.
    if alloc_engine.num_total_accounts() == 0:
        alloc_engine.create_db(authed_aats)


"""
Takes in path to file which should have the list of Microsoft accounts
we want to use inside it. Each line of the file should be one Microsoft
account username, and should contain no whitespace.
Returns a list of strings, each string being one of the usernames.
"""
def read_accounts_file(path):
    ms_usernames = []
    with open(path, "r") as f:
        for line in f:
            line = line.rstrip("\n")
            if len(line.split()) != 1:
                raise ValueError("Each line of the accounts file should be a single Microsoft username, but found a line containing whitespace. The file: {}. The line: {}".format(path, line))

            if not validity.is_valid_microsoft_username(line):
                raise ValueError("This line in the accounts file was not a valid Microsoft username: {}".format(line))
            ms_usernames.append(line)
    return ms_usernames


"""
The master cleanup function.
Nydus Server runs this every RENEWAL_PERIOD and Nydus Cli
can run it whenever desired.
It renews all authentication tokens which are close to expiring.
It releases all Minecraft account allocations which have passed the
allocation timeout.
For accounts which are still allocated, it checks for whether those client
IPs are still allocated and those system users are still logged in. If not,
the relevant Minecraft account is released.
"""
def cleanup(cfg, app, thread_lock=None):

    if not isinstance(cfg, Config):
        raise TypeError("Must pass a Nydus Config instance to initialise_accounts. Got a {}".format(type(cfg)))

    if not isinstance(app, PublicClientApplication):
        raise TypeError("Must pass an MSAL PublicClientApplication to initialise_accounts. Got a {}".format(type(app)))

    if thread_lock != None and not isinstance(thread_lock, threading.Lock):
        raise TypeError("Must pass a threading.Lock or None to function cleanup. Got a {}".format(type(thread_lock)))

    # TODO
    # Does this lock up the allocations for too long?
    # Do we need to split this into multiple
    # separate operations with separate claim/release
    # on the lock?

    if thread_lock:
        with thread_lock:
            cleanup_helper(cfg, app)
    else:
        cleanup_helper(cfg, app)

"""
Only intended to be called from inside cleanup
Used to simplify the code on whether to use a lock or not.
"""
def cleanup_helper(cfg, app):
    alloc_engine = AllocEngine(cfg.get_alloc_file())

    renew_tokens(cfg, app, alloc_engine)
    alloc_engine.release_expired()
    release_unused_accounts(cfg)

"""
Looks for access tokens in the alloc db which are close to expiring,
and renews them.
"""
def renew_tokens(cfg, app, alloc_engine):
    all_accounts = alloc_engine.get_accounts()
    for acc in all_accounts:

        # We try/except everything here because if one
        # authentication fails we still want to try renewing
        # everything else

        if acc.msal_needs_renewal(CLEANUP_DT):
            ms_username = acc.get_ms_username()
            try:
                msal_tok = netauth.get_tok_msal(ms_username, app, interactive_allowed=False)
                acc.update_msal_token(msal_tok)
            except Exception:
                pass

        if acc.xboxlive_needs_renewal(CLEANUP_DT):
            msal_tok = acc.get_msal_at()
            try:
                xboxlive_tok = netauth.get_tok_xboxlive(msal_tok)
                acc.update_xboxlive_token(xboxlive_tok)
            except Exception:
                pass

        if acc.xsts_needs_renewal(CLEANUP_DT):
            xboxlive_tok = acc.get_xboxlive_at()
            try:
                xsts_tok = netauth.get_tok_xsts(xboxlive_tok)
                acc.update_xsts_token(xsts_tok)
            except Exception:
                pass

        if acc.minecraft_needs_renewal(CLEANUP_DT):
            xsts_tok = acc.get_xsts_at()
            try:
                minecraft_tok = netauth.get_tok_minecraft(xsts_tok)
                acc.update_minecraft_token(minecraft_tok)

                # The minecraft access token is also in MCAccount
                # so we need to update that too
                mc_username = acc.get_mc_username()
                mc_uuid = acc.get_mc_uuid()
                mc_acc = MCAccount(mc_username, mc_uuid, minecraft_tok.get_token())
                acc.update_minecraft_account(mc_acc)
            except Exception:
                pass


"""
Looks for accounts which are allocated to IP addresses/system users
which aren't in use right now (therefore the Minecraft account
can't be in use) and releases them.
"""
def release_unused_accounts(cfg):
    logins = SSHLogins()
    all_accounts = alloc_engine.get_accounts()

    for acc in all_accounts:

        client_username = acc.get_client_username()
        client_ip = acc.get_client_ip()

        # If the IP address to which the account was allocated
        # no longer has the user to which the account was allocated
        # logged in to that machine, then we can release the account
        sessions = logins.get_specific_sessions(client_username, client_ip)
        if len(sessions) == 0:
            acc.release()

