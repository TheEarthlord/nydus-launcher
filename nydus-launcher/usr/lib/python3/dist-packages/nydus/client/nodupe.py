
# Code which handles whether an instance of the Nydus Client is
# already running on this system for this user.
# If an instance of Nydus Client already exists for the current
# user, any attempts to open a new one will shut down immediately.

import os
from nydus.client import utils

def get_runfile_path():
    sys_username = utils.get_username()
    runfile_name = "{}-nydus-client.pid".format(sys_username)
    return os.path.join("/etc", "nydus", runfile_name)

def runfile_exists():
    return os.path.isfile(get_runfile_path())

"""
Returns True if we believe the Nydus Client is already running
on the current system for the current user.
False if not, and it's ok to start a new Nydus Client instance.
"""
def nydus_client_running():
    # We declare the nydus client running if
    # the runfile exists (/etc/nydus/<username>-nydus-client.pid)
    # and the contents of the runfile is a valid pid
    # We can't easily check if there is a process with that pid
    # without additional libraries, so we don't bother.

    rfname = get_runfile_path()

    if runfile_exists():
        contents = get_runfile_contents()
        if is_positive_integer(contents):
            return True
    return False

"""
If runfile currently exists, returns the
(whitespace-stripped) contents of the file as a string.
If not, returns None.
"""
def get_runfile_contents():
    if runfile_exists():
        rfname = get_runfile_path()

        with open(rfname, "r") as f:
            contents = f.read()
        contents = contents.strip()
        return contents
    return None


def delete_runfile():
    if runfile_exists():
        rfname = get_runfile_path()
        contents = get_runfile_contents()
        if is_positive_integer(contents):
            filepid = int(contents)
            mypid = os.getpid()
            if filepid != mypid:
                raise ValueError("When trying to delete the runfile {}, the pid inside was {}, which does not match this Nydus Client's pid of {}".format(rfname, filepid, mypid))

        else:
            raise ValueError("When trying to delete the runfile {}, the contents was '{}', which is not a valid PID.".format(rfname, contents))

        os.remove(rfname)

    else:
        raise FileNotFoundError("Attempting to delete runfile {}, but it does not exist!")

def make_runfile():

    rfname = get_runfile_path()
    pid = os.getpid()
    
    with open(rfname, "w") as f:
        f.write("{}\n".format(pid))
        f.flush()
