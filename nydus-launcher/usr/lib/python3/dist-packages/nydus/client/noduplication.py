
# Code which handles whether an instance of the Nydus Client is
# already running on this system for this user.
# If an instance of Nydus Client already exists for the current
# user, any attempts to open a new one will shut down immediately.

import os
import psutil
from nydus.client import utils
from nydus.common import validity

def get_pidfile_path():
    sys_username = utils.get_username()
    pidfile_name = "{}-nydus-client.pid".format(sys_username)
    return os.path.join("/tmp", pidfile_name)

def pidfile_exists():
    return os.path.isfile(get_pidfile_path())

"""
Returns True if we believe the Nydus Client is already running
on the current system for the current user.
False if not, and it's ok to start a new Nydus Client instance.
We declare the nydus client already running if
1) the pidfile exists (/tmp/<username>-nydus-client.pid)
2) the contents of the pidfile is a valid PID (positive integer)
3) There exists a running process with that PID.
"""
def nydus_client_running():

    rfname = get_pidfile_path()

    if pidfile_exists():
        contents = get_pidfile_contents()
        if validity.is_positive_integer(contents):
            past_pid = int(contents)
            if psutil.pid_exists(past_pid):
                return True
    return False

"""
If pidfile currently exists, returns the
(whitespace-stripped) contents of the file as a string.
If not, returns None.
"""
def get_pidfile_contents():
    if pidfile_exists():
        rfname = get_pidfile_path()

        with open(rfname, "r") as f:
            contents = f.read()
        contents = contents.strip()
        return contents
    return None


"""
To be run at the end of the program, after Minecraft is finished.
Deletes the pidfile.
Note this function raises an exception if
1) no pidfile is present
2) a pidfile exists but doesn't contain a valid PID
3) a pidfile exists but the PID it contains is not our own
Because a valid Nydus Launcher invocation should never create
any of those situations.
"""
def delete_pidfile():
    if pidfile_exists():
        rfname = get_pidfile_path()
        contents = get_pidfile_contents()
        if validity.is_positive_integer(contents):
            filepid = int(contents)
            mypid = os.getpid()
            if filepid != mypid:
                raise ValueError("When trying to delete the pidfile {}, the pid inside was {}, which does not match this Nydus Client's pid of {}".format(rfname, filepid, mypid))

        else:
            raise ValueError("When trying to delete the pidfile {}, the contents was '{}', which is not a valid PID.".format(rfname, contents))

        os.remove(rfname)

    else:
        raise FileNotFoundError("Attempting to delete pidfile {}, but it does not exist!")


"""
To be run at the beginning of the program, before the server is
contacted. Checks for the existence of a pidfile from the Nydus
Client for the current user, and if it determines that another
instance of Nydus Client is already running on the machine, this
function exits immediately to avoid duplicate Minecraft
instances.
WARNING: This function will exit the whole program if the right conditions
are met, without presenting an error message for the user.
A message will be printed to terminal if possible, for debugging purposes.
"""
def setup_pidfile():

    # The nydus_client_running check only succeeds if a pidfile exists,
    # AND there's an existing process with the same PID. If the file
    # is left over from an old crashed process, we can go ahead and
    # overwrite it with our own.
    if nydus_client_running():
        print("Shut down nydus client due to finding an existing pidfile at '{}' with contents '{}', and a running process with the same PID. Our own PID was {}".format(get_pidfile_path(), get_pidfile_contents(), os.getpid()))
        exit(0)

    rfname = get_pidfile_path()
    pid = os.getpid()
    
    with open(rfname, "w") as f:
        f.write("{}\n".format(pid))
        f.flush()

