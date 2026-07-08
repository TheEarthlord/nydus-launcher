#!/usr/bin/python3

import datetime
import os
from nydus.common.validity import TIME_FORMAT
from nydus.common.MCAccount import MCAccount
from nydus.common import validity
from nydus.server.AccessToken import AccessToken
from nydus.server.AccountAuthTokens import AccountAuthTokens
from nydus.server.log import log_server

# Decides which account to give to a client requesting an account.
# Stores the currently allocated accounts in a file.
# Locking blocks race conditions, since each client request threads off the
# main daemon.
# Also handles releasing account allocations by checking for signs a client
# is no longer using that Minecraft account.


# The allocation file uses csv (is there any reason for csv to be
# a problem? Any case where a comma might appear in one of the fields?
# if so we can use tab separated values instead

# Structure is
# client_ip, client_user, time_allocated, username, uuid, access_token, token_time

# That is
# Ip address of the client to which this account has been allocated
# System user who was logged into the machine to which this account was allocated
# Time the allocation was done
# Minecraft account username
# Minecraft account uuid
# Minecraft account access token
# Time at which the access token was aquired

# The first three fields will be empty for unallocated accounts

# The file will be used for

# 1) Account allocation
# read the file, look for an account with first three fields blank,
# write the client IP, client user, and current time in there
# Note one client can only have one account allocated at a time.
# When you allocate one account to a client, also release all others
# allocated to them.

# 2) Account release
# if a client sends a release signal, look through the file for
# all accounts allocated to that client and erase their client IP,
# client user, and alloc time.

# 3) Cleanup
# read through the file
# Release all accounts which
#   - have been allocated more than 2 hours
#   - the user to which they were allocated is no longer logged in on that client
#     (find out using process list since logins are over ssh)
#   - the client to which they were allocated is no longer active
#     (find out using ping or if that address is no longer DHCP allocated)

# 4) Renewal
# Use the msal process to get a new access token and replace the old token
# with the new one.
# This needs to happen periodically. How often?

RESERVED_TOKEN = "RESERVED"

ALLOC_FILE = "nydus-alloc.csv"

ALLOC_DELIM = ","

# How long an account allocation lasts before
# it will be deleted
ALLOC_TIMEOUT = datetime.timedelta(hours=9)

FIELDS = [
    "reserved",
    "client_ip",
    "client_username",
    "alloc_time",
    "ms_username",
    "msal_token",
    "msal_expiry",
    "xboxlive_token",
    "xboxlive_expiry",
    "xsts_token",
    "xsts_expiry",
    "xsts_hash",
    "mc_token",
    "mc_expiry",
    "mc_username",
    "mc_uuid",
]

SUMMARY_FIELDS = [
    "reserved",
    "client_ip",
    "client_username",
    "alloc_time",
    "ms_username",
    "mc_username",
]

SUMMARY_DELIM = "|"

SUMMARY_PADDINGS = [
    8,
    15,
    20,
    19,
    33,
    33,
]

UUID_PADDINGS = [
    33,
    33,
    32,
]

assert len(SUMMARY_FIELDS) == len(SUMMARY_PADDINGS),\
    "Must have exactly one padding size for each summary field. Had {} paddings and {} fields".format(
        len(SUMMARY_PADDINGS), len(SUMMARY_FIELDS))

"""
Represents one line of the account allocation
database file.
The alloc_time and token_time attributes store
datetime objects, but you should pass a string, not a datetime,
to the constructor for those fields.
"""
class AllocAccount:

    """
    Constructor accepts all the fields individually.
    It's intended to receive data direct from the allocation file.
    Order of parameters to constructor must be same as order of
    parameters in allocation file.
    If you've independently created an AccountAuthTokens instance
    and want to use that directly, call the class method
    AllocAccount.create_from_aat()
    """
    def __init__(self, reserved, client_ip, client_username, alloc_time,
            ms_username, msal_token, msal_expiry, xboxlive_token,
            xboxlive_expiry, xsts_token, xsts_expiry, xsts_hash,
            mc_token, mc_expiry, mc_username, mc_uuid):

        self.set_reserved(reserved)
        self.set_client_ip(client_ip)
        self.set_client_username(client_username)
        self.set_alloc_time(alloc_time)

        # AccessTokens need to be given a datetime as their
        # second arg, so we convert them here.

        if not isinstance(msal_expiry, datetime.datetime):
            msal_expiry = datetime.datetime.strptime(msal_expiry, TIME_FORMAT)

        if not isinstance(xboxlive_expiry, datetime.datetime):
            xboxlive_expiry = datetime.datetime.strptime(xboxlive_expiry, TIME_FORMAT)

        if not isinstance(xsts_expiry, datetime.datetime):
            xsts_expiry = datetime.datetime.strptime(xsts_expiry, TIME_FORMAT)

        if not isinstance(mc_expiry, datetime.datetime):
            mc_expiry = datetime.datetime.strptime(mc_expiry, TIME_FORMAT)

        msal_at = AccessToken(msal_token, msal_expiry)
        xbl_at = AccessToken(xboxlive_token, xboxlive_expiry)
        xsts_at = AccessToken(xsts_token, xsts_expiry, tokhash=xsts_hash)
        mc_at = AccessToken(mc_token, mc_expiry)
        mc_acc = MCAccount(mc_username, mc_uuid, mc_token)
        aat = AccountAuthTokens(ms_username, msal_at, xbl_at, xsts_at, mc_at, mc_acc)

        self.set_account_auth_tokens(aat)


    def num_fields():
        return len(FIELDS)

    """
    Creates a new AllocAccount with the data you've passed it.
    In particular, it accepts a finished AccountAuthTokens instance
    rather than requiring all data points individually as the
    constructor does.
    Mainly for use when all users are newly authenticated and
    the allocation file is being created for the first time.
    Note that even though you pass in an AccountAuthTokens,
    a new one will be created due to the nature of the AllocAccount
    constructor which is called internally.
    Remember client_ip, client_username, and alloc_time can be empty
    strings, and they should be if the database file is being created
    from scratch.
    """
    def create_from_aat(reserved, client_ip, client_username, alloc_time, aat):

        if not isinstance(aat, AccountAuthTokens):
            raise TypeError("To create an AllocAccount using AccountAuthTokens, an AccountAuthTokens instance must be provided. Instead, {} was given.".format(type(aat)))

        return AllocAccount(
            reserved,
            client_ip,
            client_username,
            alloc_time,
            aat.get_microsoft_username(),
            aat.get_msal_token().get_token(),
            aat.get_msal_token().get_expiry(),
            aat.get_xboxlive_token().get_token(),
            aat.get_xboxlive_token().get_expiry(),
            aat.get_xsts_token().get_token(),
            aat.get_xsts_token().get_expiry(),
            aat.get_xsts_token().get_hash(),
            aat.get_minecraft_token().get_token(),
            aat.get_minecraft_token().get_expiry(),
            aat.get_minecraft_account().get_username(),
            aat.get_minecraft_account().get_uuid(),
        )

    """
    Creates the header line to go in the top of the allocation
    database file.
    Does not include a newline on the end
    """
    def make_header():
        return ALLOC_DELIM.join(FIELDS)

    """
    Creates the header line to go in the top of the summary view.
    Does not include a newline on the end
    """
    def make_summary_header():
        header_blocks = []
        for i in range(len(SUMMARY_FIELDS)):
            field = SUMMARY_FIELDS[i]
            padding = SUMMARY_PADDINGS[i]
            formstr = " {:" + str(padding) + "} "
            block = formstr.format(field)
            header_blocks.append(block)

        outstr = SUMMARY_DELIM.join(header_blocks)
        return outstr

    """
    Creates the header line to go in the top of the uuid-show view
    Does not include a newline on the end
    """
    def make_uuid_header():
        fields = ["ms-username", "mc-username", "uuid"]
        assert len(fields) == len(UUID_PADDINGS), "make_uuid_header is misconfigured"

        header_blocks = []
        for i in range(len(fields)):
            field = fields[i]
            padding = UUID_PADDINGS[i]
            formstr = " {:" + str(padding) + "} "
            block = formstr.format(field)
            header_blocks.append(block)
        outstr = SUMMARY_DELIM.join(header_blocks)
        return outstr

    """
    Creates a line of summary data, for easy viewing.
    Includes reservation status, allocation client IP, allocation client username, allocation time,
    minecraft username, and microsoft username.
    It's spaced for easy reading.
    Does NOT include a newline on the end.
    """
    def summary(self):
        summary_blocks = []
            
        reserved_field = ""
        if self.is_reserved():
            reserved_field = RESERVED_TOKEN

        fields = [
            self.get_reserved_state(),
            self.get_client_ip(),
            self.get_client_username(),
            self.get_alloc_time(),
            self.get_ms_username(),
            self.get_mc_username(),
        ]

        for i in range(len(fields)):
            value = fields[i]
            if isinstance(value, datetime.datetime):
                value = value.strftime(TIME_FORMAT)
            padding = SUMMARY_PADDINGS[i]
            formstr = " {:" + str(padding) + "} "
            block = formstr.format(value)
            summary_blocks.append(block)

        outstr = SUMMARY_DELIM.join(summary_blocks)
        return outstr

    """
    Creates a line of summary data to show account uuid
    Includes Minecraft username, Microsoft username, uuid
    It's spaced for easy reading.
    Does NOT include a newline on the end.
    """
    def uuid_show(self):
        summary_blocks = []
            
        fields = [
            self.get_ms_username(),
            self.get_mc_username(),
            self.get_mc_uuid(),
        ]

        for i in range(len(fields)):
            value = fields[i]
            padding = UUID_PADDINGS[i]
            formstr = " {:" + str(padding) + "} "
            block = formstr.format(value)
            summary_blocks.append(block)

        outstr = SUMMARY_DELIM.join(summary_blocks)
        return outstr


    def copy(self):
        return AllocAccount(
            self.get_reserved_state(),
            self.get_client_ip(),
            self.get_client_username(),
            self.get_alloc_time(),
            self.get_account_auth_tokens().copy(),
        )

    """
    There should not be accounts which have only some of the first
    3 fields filled but not all. However, if such accounts exist,
    we count them as unallocated because clearly the allocation
    process broke somehow.
    """
    def is_allocated(self):
        if self.client_ip and self.client_username and self.alloc_time:
            return True
        return False

    """
    Returns True if allocation was successful, False otherwise
    Note: "successful" doesn't refer to writing the change to
    the allocation database, just to setting the data structure to
    being allocated in program memory.
    """
    def allocate(self, client_ip, client_username):
        if self.is_reserved():
            log_server("Tried to allocate account {} with uuid {} to IP {} and username {}, but it was reserved".format(\
                    self.get_ms_username(), self.get_mc_uuid(), client_ip, client_username))
            return False
        now = datetime.datetime.now()
        now_str = now.strftime(TIME_FORMAT)
        self.set_client_ip(client_ip)
        self.set_client_username(client_username)
        self.set_alloc_time(now_str)
        return True

    """
    Returns True if release was successful, False otherwise
    """
    def release(self):
        if self.is_reserved():
            log_server("Tried to release account {} with uuid {}, but it was reserved".format(\
                    self.get_ms_username(), self.get_mc_uuid()))
            return False
        self.set_client_ip("")
        self.set_client_username("")
        self.set_alloc_time("")
        return True

    """
    If an account is "reserved", it will not be allocated
    or released. Reservation can only be set and unset
    by directly using nydus-cli; it won't be done automatically
    by the server.
    Reservation is intended for if a machine needs to be able to
    log into Minecraft but can't run the Nydus Launcher client.
    Reserve one of the Minecraft accounts so it won't get
    allocated somewhere else, then use it freely on the no-Nydus
    machine.
    """
    def is_reserved(self):
        return self.account_reserved

    def reserve(self):
        self.account_reserved = True

    def unreserve(self):
        self.account_reserved = False

    # Type checks for the 'update' methods
    # occur inside the AccountAuthTokens method where applicable
    # Use the 'update' methods to replace tokens when one
    # has been renewed.

    def update_msal_token(self, new_msal_token):
        self.aat.set_msal_token(new_msal_token)

    def update_xboxlive_token(self, new_xbl_token):
        self.aat.set_xboxlive_token(new_xbl_token)

    def update_xsts_token(self, new_xsts_token):
        self.aat.set_xsts_token(new_xsts_token)

    def update_minecraft_token(self, new_mc_token):
        self.aat.set_minecraft_token(new_mc_token)

    def update_minecraft_account(self, new_mc_account):
        self.aat.set_minecraft_account(new_mc_account)

    """
    Returns True if the account is allocated and has been allocated
    for longer than the alloc timeout.
    Otherwise, return False (including if the account is not allocated,
    or is reserved)
    """
    def alloc_expired(self):

        if self.is_reserved():
            return False
        now = datetime.datetime.now()
        if self.get_alloc_time():
            if now - self.get_alloc_time() > ALLOC_TIMEOUT:
                return True
        return False

    def msal_expired(self):
        return self.aat.get_msal_token().is_expired()

    def xboxlive_expired(self):
        return self.aat.get_xboxlive_token().is_expired()

    def xsts_expired(self):
        return self.aat.get_xsts_token().is_expired()

    def minecraft_expired(self):
        return self.aat.get_minecraft_token().is_expired()

    # We default msal's renewal window to only one cleanup period,
    # not 2 like the other tokens types, because msal tokens are
    # only valid for an hour and the cleanup period is half an
    # hour so two periods would renew the token every cleanup.
    def msal_needs_renewal(self, check_interval, num_intervals=1):
        return self.aat.get_msal_token().needs_renewal(check_interval, num_intervals)

    # Xbox and Minecraft tokens usually expire a day after issue,
    # so 2*cleanup_period = 1 hour is plenty of warning.
    def xboxlive_needs_renewal(self, check_interval, num_intervals=2):
        return self.aat.get_xboxlive_token().needs_renewal(check_interval, num_intervals)

    def xsts_needs_renewal(self, check_interval, num_intervals=2):
        return self.aat.get_xsts_token().needs_renewal(check_interval, num_intervals)

    def minecraft_needs_renewal(self, check_interval, num_intervals=2):
        return self.aat.get_minecraft_token().needs_renewal(check_interval, num_intervals)

    """
    reserved_token: string, from the alloc database.
    Should be contents of RESERVED_TOKEN or empty string
    """
    def set_reserved(self, reserved_token):
        if reserved_token == RESERVED_TOKEN:
            self.account_reserved = True
        elif reserved_token == "":
            self.account_reserved = False
        else:
            raise ValueError("Reserved state entry must be either {} or ''. Instead, got {}".format(RESERVED_TOKEN, reserved_token))

    # We must allow empty string for client_ip, client_username, and
    # alloc time as empty strings for them indicate an unallocated account
    def set_client_ip(self, client_ip):
        if client_ip == "" or validity.is_valid_ipaddr(client_ip):
            self.client_ip = client_ip
        else:
            raise ValueError("Client IP value is not a valid IP address: {}".format(client_ip))

    def set_client_username(self, client_username):
        if client_username == "" or validity.is_valid_system_username(client_username):
            self.client_username = client_username
        else:
            raise ValueError("Client username value is not a valid system username: {}".format(client_username))

    def set_alloc_time(self, alloc_time):
        if alloc_time == "":
            self.alloc_time = alloc_time
        elif validity.is_valid_str_timestamp(alloc_time):
            self.alloc_time = datetime.datetime.strptime(alloc_time, TIME_FORMAT)
        else:
            raise ValueError("Alloc time value is not a valid timestamp: {}".format(alloc_time))

    def set_account_auth_tokens(self, aat):
        if isinstance(aat, AccountAuthTokens):
            self.aat = aat
        else:
            raise TypeError("Object given is not an AccountAuthTokens class: {}".format(aat))

    def get_reserved_state(self):
        if self.account_reserved:
            return RESERVED_TOKEN
        else:
            return ""

    def get_client_ip(self):
        return self.client_ip

    def get_client_username(self):
        return self.client_username

    def get_alloc_time(self):
        return self.alloc_time

    def get_account_auth_tokens(self):
        return self.aat

    def get_ms_username(self):
        return self.aat.get_microsoft_username()

    """
    Specifically the token string, not the AccessToken object
    """
    def get_msal_token(self):
        return self.aat.get_msal_token().get_token()

    def get_msal_expiry(self):
        return self.aat.get_msal_token().get_expiry()

    """
    Specifically the token string, not the AccessToken object
    """
    def get_xboxlive_token(self):
        return self.aat.get_xboxlive_token().get_token()

    def get_xboxlive_expiry(self):
        return self.aat.get_xboxlive_token().get_expiry()

    """
    Specifically the token string, not the AccessToken object
    """
    def get_xsts_token(self):
        return self.aat.get_xsts_token().get_token()

    def get_xsts_expiry(self):
        return self.aat.get_xsts_token().get_expiry()

    def get_xsts_hash(self):
        return self.aat.get_xsts_token().get_hash()

    """
    Specifically the token string, not the AccessToken object
    """
    def get_mc_token(self):
        return self.aat.get_minecraft_token().get_token()

    def get_mc_expiry(self):
        return self.aat.get_minecraft_token().get_expiry()

    """
    For these get functions, 'at' stands for 'AccessToken'
    """
    def get_msal_at(self):
        return self.aat.get_msal_token()

    def get_xboxlive_at(self):
        return self.aat.get_xboxlive_token()

    def get_xsts_at(self):
        return self.aat.get_xsts_token()

    def get_mc_at(self):
        return self.aat.get_minecraft_token()

    def get_mc_username(self):
        return self.aat.get_minecraft_account().get_username()

    def get_mc_uuid(self):
        return self.aat.get_minecraft_account().get_uuid()

    """
    Creates a line of data, suitable for writing back into
    the account allocation database file.
    Does NOT include a newline on the end.
    """
    def __repr__(self):
        fields = [
            self.get_reserved_state(),
            self.get_client_ip(),
            self.get_client_username(),
            self.get_alloc_time(),
            self.get_ms_username(),
            self.get_msal_token(),
            self.get_msal_expiry(),
            self.get_xboxlive_token(),
            self.get_xboxlive_expiry(),
            self.get_xsts_token(),
            self.get_xsts_expiry(),
            self.get_xsts_hash(),
            self.get_mc_token(),
            self.get_mc_expiry(),
            self.get_mc_username(),
            self.get_mc_uuid(),
        ]

        for i in range(len(fields)):
            obj = fields[i]

            # Make sure datetimes are written out in the right format
            if isinstance(obj, datetime.datetime):
                fields[i] = obj.strftime(TIME_FORMAT)
            else:
                fields[i] = str(obj)

        assert len(fields) == AllocAccount.num_fields()
        return ALLOC_DELIM.join(fields)

"""
Initiate the AllocEngine with the path to the csv containing all
the Minecraft accounts
This class is intended to be created again by each thread that
needs to work with the account database, then call one
of its methods to do one of the operations.
"""
class AllocEngine:

    """
    When creating the alloc db file for the first time, leave it empty and
    AllocEngine won't read any data out of it.
    Then call the create_db method to set up the accounts and write the data
    into the file.
    """
    def __init__(self, path):
        if not isinstance(path, str):
            raise TypeError("Path to allocation database file must be a string. Was {}".format(path))

        if not os.path.isfile(path):
            raise FileNotFoundError("Path to allocation database file must exist. Was {}".format(path))

        try:
            with open(path, "r") as f:
                pass
        except PermissionError:
            raise PermissionError("Allocation database file was not readable. Given path is {}".format(path))
        
        self.path = path
        self.accounts = []
        self.load_alloc_db()

    def num_total_accounts(self):
        return len(self.accounts)

    def __repr__(self):
        return AllocEngine.list_to_string(self.accounts)

    """
    Returns the exact account objects, not copies, because this method is
    used to access the underlying data so that changes can be made like
    renewing tokens.
    """
    def get_accounts(self):
        return self.accounts

    def get_allocated_accounts(self):
        return [acc for acc in self.accounts if acc.is_allocated()]

    """
    Given a list of AllocAccount objects, creates a string
    consisting of lines. The first line is the header for AllocAccount fields,
    all other lines represent the accounts in the provided list.
    The string is returned.
    """
    def list_to_string(acclist):
        assert isinstance(acclist, list), "Provided object must be a list of AllocAccounts. Was {}".format(acclist)
        for elem in acclist:
            assert isinstance(elem, AllocAccount), "Provided object must be a list of AllocAccounts. Contained an element '{}'".format(elem)
        outstr = ""
        outstr += "{}\n".format(AllocAccount.make_header())
        for acc in acclist:
            outstr += "{}\n".format(acc)
        return outstr

    def view_uuid(self, uuid):
        if not validity.is_valid_minecraft_uuid(uuid):
            raise ValueError("Not a valid Minecraft uuid: {}".format(uuid))

        to_view = [acc for acc in self.accounts if acc.get_mc_uuid() == uuid]
        return AllocEngine.list_to_string(to_view)

    def view_ip(self, client_ip):
        if not validity.is_valid_ipaddr(client_ip):
            raise ValueError("Not a valid IP address: {}".format(client_ip))

        to_view = [acc for acc in self.accounts if acc.get_client_ip() == client_ip]
        return AllocEngine.list_to_string(to_view)
    
    """
    Returns a string containing a summary form of the allocation database
    that shows only Microsoft username, Minecraft username, and Minecraft uuid.
    The string will include every account in the attached AllocEngine.
    """
    def uuid_show(self):
        outstr = ""
        outstr += "{}\n".format(AllocAccount.make_uuid_header())
        for acc in self.accounts:
            outstr += "{}\n".format(acc.uuid_show())
        return outstr
    
    """
    Returns a summary string (like that given by list_to_summary)
    but specifically for all the accounts in the attached AllocEngine
    """
    def summary(self):
        return AllocEngine.list_to_summary(self.accounts)

    """
    Returns a string, containing a summary form of the allocation database.
    The summary form shows only allocation client IP, allocation username, allocation time,
    minecraft username, and microsoft username, and is spaced for easy viewing.
    Must be given a list of AllocAccounts.
    """
    def list_to_summary(acclist):
        assert isinstance(acclist, list), "Provided object must be a list of AllocAccounts. Was {}".format(acclist)
        for elem in acclist:
            assert isinstance(elem, AllocAccount), "Provided object must be a list of AllocAccounts. Contained an element '{}'".format(elem)

        outstr = ""
        outstr += "{}\n".format(AllocAccount.make_summary_header())
        for acc in acclist:
            outstr += "{}\n".format(acc.summary())
        return outstr
    
    def summary_ip(self, client_ip):
        if not validity.is_valid_ipaddr(client_ip):
            raise ValueError("Not a valid IP address: {}".format(client_ip))

        to_view = [acc for acc in self.accounts if acc.get_client_ip() == client_ip]
        return AllocEngine.list_to_summary(to_view)

    def summary_uuid(self, uuid):
        if not validity.is_valid_minecraft_uuid(uuid):
            raise ValueError("Not a valid Minecraft uuid: {}".format(uuid))

        to_view = [acc for acc in self.accounts if acc.get_mc_uuid() == uuid]
        return AllocEngine.list_to_summary(to_view)

    def write_changes(self):
        try:
            with open(self.path, "w") as f:
                f.write(str(self))
                f.flush()
        except PermissionError:
            raise PermissionError("Could not write to allocation database file. Given path is {}".format(self.path))

    def load_alloc_db(self):
        with open(self.path, "r") as f:

            first_line = True
            for line in f:

                # Skip first line, since it contains the header for each column
                if first_line:
                    first_line = False
                    continue

                line = line.strip()
                parts = line.split(ALLOC_DELIM)
                if len(parts) != AllocAccount.num_fields():
                    raise ValueError("Line in account allocation database was invalid. It should have had {} {}-separated elements, but had {}. Line looked like: {}".format(AllocAccount.num_fields(), ALLOC_DELIM, len(parts), line))
                
                # Note: this instantiation depends on the order of fields
                # being the same in the db file and in the Account class
                # constructor
                acc = AllocAccount(*parts)
                self.accounts.append(acc)

    """
    If an unallocated account is found, marks it allocated and
    returns the object representing it.
    If no unallocated account is found, returns None.
    
    Always deallocates all accounts currently allocated to this client IP
    """
    def allocate_one_account(self, client_ip, client_username):

        if not validity.is_valid_ipaddr(client_ip):
            raise ValueError("Client IP was not a valid IP address: {}".format(client_ip))

        if not validity.is_valid_system_username(client_username):
            raise ValueError("Client username was not a valid system username: {}".format(client_username))

        if client_username == "root":
            raise ValueError("Will not allocate Minecraft accounts to root.")

        # Release everything currently allocated to this client
        for acc in self.accounts:
            if acc.is_allocated() and acc.get_client_ip() == client_ip and acc.get_client_username() == client_username:
                
                result = acc.release()
                
                if result:
                    log_server("Released account {} which was allocated to IP {} because IP {} has requested a new account".format(\
                            acc.get_ms_username(), client_ip, client_ip))

        for acc in self.accounts:
            if not acc.is_allocated():
                result = acc.allocate(client_ip, client_username)

                if result:
                    self.write_changes()

                    log_server("Allocated account {} to IP {} and username {} because an account was requested by IP {}".format(\
                            acc.get_ms_username(), acc.get_client_ip(), acc.get_client_username(), client_ip))

                    return acc
        return None

    """
    Finds all accounts allocated to both the given client IP
    and the given username, and releases them.
    """
    def release_account(self, client_ip, client_username):
        if not validity.is_valid_ipaddr(client_ip):
            raise ValueError("Not a valid IP address: {}".format(client_ip))

        if not validity.is_valid_system_username(client_username):
            raise ValueError("Client username was not a valid system username: {}".format(client_username))

        to_release = []
        for acc in self.accounts:
            if acc.is_allocated():
                if acc.get_client_ip() == client_ip:
                    if acc.get_client_username() == client_username:
                        to_release.append(acc)

        for acc in to_release:
            result = acc.release()
            if result:
                log_server("Released account {}; release of accounts allocated to IP {} and username {} was requested".format(\
                        acc.get_ms_username(), client_ip, client_username))

        self.write_changes()

    """
    Finds account by uuid
    If the account is found and currently allocated, releases it
    Note that if (somehow) two lines have the same account uuid,
    both will be released.
    """
    def release_account_uuid(self, uuid):
        if not validity.is_valid_minecraft_uuid(uuid):
            raise ValueError("Not a valid Minecraft uuid: {}".format(uuid))

        to_release = [acc for acc in self.accounts\
                if acc.is_allocated() and acc.get_mc_uuid() == uuid]

        for acc in to_release:
            result = acc.release()
            if result:
                log_server("Released account {}; release of account with uuid {} was requested".format(\
                        acc.get_ms_username(), uuid))

        self.write_changes()

    """
    Finds all accounts allocated to the given client IP
    and releases them.
    """
    def release_account_ip(self, client_ip):
        if not validity.is_valid_ipaddr(client_ip):
            raise ValueError("Not a valid IP address: {}".format(client_ip))

        to_release = [acc for acc in self.accounts \
                if acc.is_allocated() and acc.get_client_ip() == client_ip]

        for acc in to_release:
            result = acc.release()
            if result:
                log_server("Released account {}; release of accounts allocated to IP {} was requested".format(\
                        acc.get_ms_username(), client_ip))

        self.write_changes()
    
    """
    Finds an account (or all accounts if there are more than one) of a specific
    uuid, and allocates them to the given client IP address and system username
    Overwrites existing allocation of the account(s) in question.
    """
    def allocate_uuid(self, uuid, client_ip, client_username):
        if not validity.is_valid_ipaddr(client_ip):
            raise ValueError("Client IP was not a valid IP address: {}".format(client_ip))

        if not validity.is_valid_system_username(client_username):
            raise ValueError("Client username was not a valid system username: {}".format(client_username))

        if not validity.is_valid_minecraft_uuid(uuid):
            raise ValueError("Not a valid Minecraft uuid: {}".format(uuid))

        to_allocate = [acc for acc in self.accounts\
                if acc.get_mc_uuid() == uuid]

        for acc in to_allocate:
            result = acc.allocate(client_ip, client_username)
            if result:
                log_server("Allocated account {} to IP {} and username {}; an allocation was requested for uuid {}".format(\
                        acc.get_ms_username(), acc.get_client_ip(), acc.get_client_username(), uuid))

        self.write_changes()

    """
    Finds an account (or all accounts if there are more than one) of a specific
    uuid, and reserves them.
    Reservation means an account can't be allocated by any means until unreserved.
    """
    def reserve_uuid(self, uuid):
        if not validity.is_valid_minecraft_uuid(uuid):
            raise ValueError("Not a valid Minecraft uuid: {}".format(uuid))

        to_reserve = [acc for acc in self.accounts\
                if acc.get_mc_uuid() == uuid]

        for acc in to_reserve:
            acc.reserve()
            log_server("Reserved account {} with uuid {}".format(\
                    acc.get_ms_username(), acc.get_mc_uuid()))
        self.write_changes()

    """
    Finds an account (or all accounts if there are more than one) of a specific
    uuid, and unreserves them.
    Reservation means an account can't be allocated by any means until unreserved.
    """
    def unreserve_uuid(self, uuid):
        if not validity.is_valid_minecraft_uuid(uuid):
            raise ValueError("Not a valid Minecraft uuid: {}".format(uuid))

        to_unreserve = [acc for acc in self.accounts\
                if acc.get_mc_uuid() == uuid]

        for acc in to_unreserve:
            acc.unreserve()
            log_server("Unreserved account {} with uuid {}".format(\
                    acc.get_ms_username(), acc.get_mc_uuid()))
        self.write_changes()


    """
    aat_list: a list of AccountAuthTokens instances.
    This method is intended to be called when no accounts were
    present in the allocation db file (it will raise an Exception
    if accounts were found). It will create an
    entry for each of the AccountAuthTokens instances given,
    and write them all into the file.
    """
    def create_db(self, aat_list):
        if not isinstance(aat_list, list):
            raise TypeError("Must pass a list to create_db method. Instead, got a {}".format(type(aat_list)))

        for elem in aat_list:
            if not isinstance(elem, AccountAuthTokens):
                raise TypeError("The aat list given to create_db must contain only AccountAuthTokens, but found a {}".format(type(elem)))

        if len(self.accounts) > 0:
            raise ValueError("create_db is intended to be called when no accounts were found in the allocation db file, but AllocEngine found {} accounts".format(len(self.accounts)))

        for aat in aat_list:
            self.accounts.append(AllocAccount.create_from_aat("", "", "", "", aat))

        self.write_changes()


    """
    aat_list: a list of AccountAuthTokens instances
    This method is similar to create_db, but functions when accounts
    were found in the allocation db file. It will create a new
    allocation db entry for each account represented by the AccountAuthTokens
    instances given, and append those to the existing ones from
    the db file, then write the whole resulting account set back
    into the file.
    This method is intended for situations when authenticating some
    accounts fails initially so the alloc db file is created without
    them, but they are successfully authenticated later and need
    to be added to the roster of available accounts.
    """
    def extend_db(self, aat_list):
        if not isinstance(aat_list, list):
            raise TypeError("Must pass a list to extend_db method. Instead, got a {}".format(type(aat_list)))

        for elem in aat_list:
            if not isinstance(elem, AccountAuthTokens):
                raise TypeError("The aat list given to extend_db must contain only AccountAuthTokens, but found a {}".format(type(elem)))

        for aat in aat_list:
            self.accounts.append(AllocAccount.create_from_aat("", "", "", "", aat))

        self.write_changes()

    """
    Releases all the accounts which are past their allocation timeout.
    """
    def release_expired(self):
        for acc in self.accounts:
            if acc.alloc_expired() and not acc.is_reserved():
                result = acc.release()
                if result:
                    log_server("Released account {}; allocation expired".format(\
                            acc.get_ms_username()))


