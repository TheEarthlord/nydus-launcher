#!/usr/bin/python3

import os
import subprocess
import sys

# This script updates the version of the Nydus Launcher.
# There are currently two places it needs to be changed;
# the nydus_info.py code file in the nydus-common package,
# and the changelog in the debian directory (right here).

def is_nonempty_str(mystr):
    if not isinstance(mystr, str):
        return False
    if len(mystr) == 0:
        return False
    return True

def is_nonnegative_integer(num):
    if not is_integer(num):
        return False
    num = int(num)

    if num < 0:
        return False
    return True

"""
Returns True if the given string is of the form
X or X.Y or X.Y.Z or X.Y.Z.A etc.
where X, Y, and Z, etc. are non-negative integers.
num_segments: integer, how many integer elements should be
    in the version string.
"""
def is_valid_version(vers, num_segments):
    if not isinstance(num_segments, int):
        raise TypeError("num_segments for is_valid_version must be an integer. Was {}".format(type(num_segments)))

    if num_segments < 1:
        raise ValueError("num_segments for is_valid_version must be a positive integer. Was {}".format(num_segments))

    if not is_nonempty_str(vers):
        return False

    parts = vers.split(".")
    if len(parts) != num_segments:
        return False
    
    for seg in parts:
        if not is_nonnegative_integer(seg):
            return False
    return True

def main():
    script_name = sys.argv[0]

    info_path = os.path.join("..", "usr", "lib", "python3", "dist-packages", "nydus", "common", "nydus_info.py")

    if not os.path.isfile(info_path):
        print("Could not find nydus_info.py at {}".format(info_path))
        print("Are you running {} from the debian directory in Nydus Launcher source code?".format(script_name))

    info_contents = ""
    with open(info_path, "r") as f:
        info_contents = f.readlines()

    verfunc_header = "def get_launcher_version()"
    verline_idx = -1
    for i in range(len(info_contents)):
        line = info_contents[i]
        if verfunc_header in line:
            verline_idx = i+1
            break

    if verline_idx == -1:
        print("Could not find version function header in {}: '{}'".format(info_path, verfunc_header))
        exit(1)

    if verline_idx >= len(info_contents):
        print("Found line index of version statement as {}, which exceeds the {} lines in {}".format(verline_idx, len(info_contents), info_path))

    verline = info_contents[verline_idx]
    verline_delim = '"'
    verline_parts = verline.split(verline_delim)
    verpart_idx = -1
    for i in range(len(verline_parts)):
        part = verline_parts[i]
        if is_valid_version(part, 3):
            oldversion = part
            verpart_idx = i
            print("Found existing Nydus Launcher version: {}".format(oldversion))

    if verpart_idx == -1:
        print("Could not find valid Nydus Launcher version in line '{}'".format(verline))

    newversion = ""
    while not is_valid_version(newversion, 3):
        print("A valid version is of the form X.Y.Z where X, Y, and Z are nonnegative integers.")
        newversion = input("What would you like the new version to be?")

    verline_parts[verpart_idx] = newversion
    new_verline = verline_delim.join(verline_parts)
    info_contents[verline_idx] = new_verline

    with open(info_path, "w") as f:
        for line in info_contents:
            f.write(line)

    subprocess.run("/usr/bin/dch", "-v", newversion, "--distribution", "jammy")

if __name__ == "__main__":
    main()
