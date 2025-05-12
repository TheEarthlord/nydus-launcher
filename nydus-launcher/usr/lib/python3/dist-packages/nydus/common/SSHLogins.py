
import subprocess
from nydus.common import validity

# Uses the 'who' command to find all the users
# who are currently logged on via ssh.
# Sample 'who' output
# crutech  tty7         2025-01-01 13:27 (:0)
# crutech  pts/1        2025-01-01 13:40 (127.0.0.1)
# 
# The format is
# username space tty space date space time space (ipaddr)
# So when split by whitespace we expect 5 fields

LOGINS_COMMAND = "/usr/bin/who"
WHO_FIELDS = 4
USERNAME_FIELD = 0
IPADDR_FIELD = 4
assert USERNAME_FIELD < WHO_FIELDS+1
assert IPADDR_FIELD < WHO_FIELDS+1

class SSHSession:

    """
    This class is intended to represent one user's SSH session
    logging into the current machine from another remote one.
    The username is their local username (not the one on the machine
    they started from; we can't know that) and the ip address
    is the address from which they came.
    """
    def __init__(self, username, ip_addr):
        if not validity.is_valid_system_username(username):
            raise ValueError("SSHSession must be given valid system username. Was given {}".format(username))

        if not validity.is_valid_ipaddr(ip_addr):
            raise ValueError("SSHSession must be given valid IP address. Was given {}".format(ip_addr))

        self.username = username
        self.ip_addr = ip_addr

    def get_username(self):
        return self.username

    def get_ipaddr(self):
        return self.ip_addr

    def __eq__(self, other):
        if type(self) == type(other):
            if self.get_username() == other.get_username():
                if self.get_ipaddr() == other.get_ipaddr():
                    return True
        return False

    def __repr__(self):
        return "{} from {}".format(self.username, self.ip_addr)

"""
To get data about who's logged in right now, instantiate
this class or call update_data on an existing instance of it
then call whatever methods you want to get the data you want.
"""
class SSHLogins:

    def __init__(self):
        self.update_data()

    """
    Calls the who command and updates the internally
    stored data of which users are logged in via ssh
    and where from.
    """
    def update_data(self):

        # Wipe existing data
        self.sessions = []

        completed_subp = subprocess.run([LOGINS_COMMAND], capture_output=True)
        stderr = completed_subp.stderr.decode()
        if completed_subp.returncode != 0:
            raise ValueError("Running '{}' command failed. stderr: {}".format(LOGINS_COMMAND, stderr))

        who_out = completed_subp.stdout.decode()

        lines = who_out.strip().split("\n")
        
        for line in lines:
            parts = line.split()

            # There are three possibilities for lines in 'who'
            # 1) A local user with a display; 5 parts to the line and the 5th is the display number. Skip.
            # 2) An ssh user; 5 parts to the line and the 5th is the origin IP address. We want to find all of these.
            # 3) A local user without a display; 4 parts to the line. Skip.

            if len(parts) == WHO_FIELDS:
                continue

            if len(parts) != WHO_FIELDS + 1:
                raise IndexError("Expected {} or {} whitespace-separated fields in output of '{}', but got {}".format(WHO_FIELDS, WHO_FIELDS+1, LOGINS_COMMAND, len(parts)))

            username = parts[USERNAME_FIELD]
            origin = parts[IPADDR_FIELD]

            ip_addr = origin.lstrip("(").rstrip(")")

            # Not all 'who' output lines are ssh logins.
            # We only want the ones where the login originates
            # over the network i.e. from an IP address
            if ip_addr == origin or not validity.is_valid_ipaddr(ip_addr):
                continue

            session = SSHSession(username, ip_addr)

            self.sessions.append(session)

    def get_all_sessions(self):
        return self.sessions

    """
    Get all sessions of the specified username
    Returns list
    """
    def get_user_sessions(self, username):
        return [ses for ses in self.sessions if ses.get_username() == username]

    """
    Get all sessions originating from the specified IP address
    Returns list
    """
    def get_ipaddr_sessions(self, ipaddr):
        return [ses for ses in self.sessions if ses.get_ipaddr() == ipaddr]

    """
    Get all sessions which belong to the specified username and originate
    from the specified IP address.
    Returns a list. There will likely only be 1 or 0 entry in the list,
    but it is theoretically possible for there to be more.
    """
    def get_specific_sessions(self, username, ipaddr):
        return [ses for ses in self.sessions if ses.get_username() == username and ses.get_ipaddr() == ipaddr]
