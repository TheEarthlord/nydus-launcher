
import os
import datetime

def get_log_dir():
    return "/var/log/nydus"

def get_client_log_path():
    return os.path.join(get_log_dir(), "nydus-client.log") 

"""
This function empties the Nydus client logfile.
It should be called when a new instance of the Nydus client
starts, so the logfile doesn't grow forever.
Returns nothing
"""
def restart_client_log():
    with open(get_client_log_path(), "w") as f:
        f.flush()

"""
message: string, the statement to log
This function adds things like a timestamp to the message,
turning it into a line of information ready to be inserted
into the nydus launcher client logs
Returns string, the message with logging additions
"""
def prepare_log_message(message):

    if not message.endswith("\n"):
        message += "\n"

    log_ts = datetime.datetime.now().isoformat(timespec="microseconds")
    logmessage = "[{}] {}".format(log_ts, message)
    return logmessage

"""
message: string, the statement to log
This function logs the given statement
in the nydus client's logfile
"""
def log_client(message):
    message = prepare_log_message(message)
    with open(get_client_log_path(), "a") as f:
        f.write(message)
        f.flush()
