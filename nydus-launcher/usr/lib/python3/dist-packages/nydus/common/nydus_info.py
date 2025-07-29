
import sys

def get_launcher_name():
    return "nydus-launcher"

def get_launcher_version():
    return "2.2.1"

def get_version_arg():
    return "--version"

"""
This function checks if the currently running program
was given the 'show version' argument (the string
returned by get_version_arg) in the first position.
If so, it prints the current Nydus Launcher
version and exits.
This function access sys.argv, and will exit
the entire program if the version was requested.
If the version was not requested, it returns
and allows the caller to proceed normally.
"""
def request_version():
    if len(sys.argv[1]) > 1:
        arg = sys.argv[1]
        if arg == get_version_arg():
            print(get_launcher_version())
            exit(0)
