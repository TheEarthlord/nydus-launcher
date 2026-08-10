
"""
Utilities needed in multiple Nydus client modules
"""

import os
import pwd
import re
from nydus.common import validity
from nydus.common.validity import MC_VERSION_PARTS

"""
Raises OSError if something's wrong with pwd database entry
"""
def get_pwd_entry(uid=None):

    if not uid:
        # May raise OSError
        uid = os.getuid()

    try:
        pwdentry = pwd.getpwuid(uid)
    except KeyError:
        raise OSError("Could not find pwd database entry for uid {}.".format(uid))

    if not isinstance(pwdentry, pwd.struct_passwd):
        raise OSError("getpwuid returned a {} instead of a pwd database entry for uid {}.".format(type(pwdentry), uid))

    return pwdentry


"""
Raises OSError if username can't be found for some reason
"""
def get_username():

    pwdentry = get_pwd_entry()

    if not hasattr(pwdentry, "pw_name"):
        raise OSError("pwd database entry for uid {} has no username.".format(uid))

    username = pwdentry.pw_name

    if not isinstance(username, type("")):
        raise OSError("getpwuid for uid {} gave non-string where username should be.".format(uid))

    if username == "":
        raise OSError("getpwuid returned empty string for username of uid {}.".format(uid))

    return username

"""
Raises OSError if home directory can't be found for some reason
"""
def get_home_dir():

    pwdentry = get_pwd_entry()

    expanded_homedir = os.path.expanduser("~")

    if hasattr(pwdentry, "pw_dir"):
        home_dir = pwdentry.pw_dir

    # os.path.expanduser returns the original string if expansion
    # failed
    elif expanded_homedir != "~":
        # Plan B; use os.path's user home directory expansion
        home_dir = expanded_homedir

    else:
        # Plan C; assume standard structure and get username
        username = get_username()
        home_dir = os.path.join("/home", username)

    # We have our prospective home directory
    
    if not isinstance(home_dir, str):
        raise OSError("User's home directory is not a string.")

    if home_dir == "":
        raise OSError("User's home directory is an empty string.")

    if not os.path.isdir(home_dir):
        raise OSError("User's home directory {} does not exist.".format(home_dir))

    return home_dir


"""
Gets path to current user's .minecraft folder (including '.minecraft' in the path)
Raises OSError if it can't be found.
"""
def get_minecraft_path():
    
    home_dir = get_home_dir()

    minecraft_path = os.path.join(home_dir, ".minecraft")

    if not os.path.isdir(minecraft_path):
        raise OSError("User's Minecraft directory does not exist at {}".format(minecraft_path))
    return minecraft_path

"""
Gets path to the position under which downloaded jar files are usually placed.
Usually ~/.minecraft/libraries
"""
def get_minecraft_libraries_path():
    return os.path.join(get_minecraft_path(), "libraries")

"""
Gets path to current user's Minecraft assets folder
(usually /home/<username>/.minecraft/assets)
Raises OSError if it can't be found.
"""
def get_minecraft_assets_path():
    mc_path = get_minecraft_path()
    assets_path = os.path.join(mc_path, "assets")

    if not os.path.isdir(assets_path):
        raise OSError("User's Minecraft assets directory does not exist at {}".format(assets_path))

    return assets_path

"""
Gets path to the current user's Minecraft log config folder
(usually /home/<username>/.minecraft/assets/log_configs)
Raises OSError if it can't be found.
"""
def get_minecraft_log_config_dir():
    assets_path = get_minecraft_assets_path()
    log_cdir = os.path.join(assets_path, "log_configs")

    if not os.path.isdir(log_cdir):
        raise OSError("User's Minecraft log config directory does not exist at {}".format(log_cdir))
    return log_cdir

"""
index: an integer or string representing an integer. Must be nonnegative.
Get path to location for a specific asset index's JSON file.
Usually /home/<username>/.minecraft/assets/indexes/<index>.json
Does not check whether the file actually exists.
"""
def get_asset_index_path(index):

    valid_index = validity.is_nonnegative_integer(index) or\
        (isinstance(index, int) and index > 0)

    if not valid_index:
        raise ValueError("Minecraft assets index must be a nonnegative integer. Was given {}".format(index))

    assets_path = get_minecraft_assets_path()
    json_path = os.path.join(assets_path, "indexes", "{}.json".format(index))
    return json_path

"""
Returns a string; the path to the json file which gives information
about all available Minecraft versions, inside the user's .minecraft folder.
Specifically, this is
/home/<user>/.minecraft/versions/version_manifest_v2.json
Raises OSError if it can't be found or can't be read.
"""
def get_version_manifest():
    minecraft_path = get_minecraft_path()
    manifest = os.path.join(minecraft_path, "versions", "version_manifest_v2.json")

    if not validity.is_valid_file(manifest):
        raise OSError("User's Minecraft version manifest does not exist or could not be read at {}".format(manifest))
    return manifest

"""
Python's default lstrip, given a to_strip string of more than one character,
will strip everything off the original string until it finds a character
which does not appear in the to_strip string at all.
i.e. 'https://thog.com'.lstrip('https://') will return 'og.com', not 'thog.com'
becuase the 't' and 'h' in 'thog' are also characters in 'https://'.
This function strips only the exact to_strip string provided, and doesn't
change the original string if it doesn't start with to_strip.
So strict_lstrip('https://thog.com', 'https://') will return 'thog.com'
and strict_lstrip('https:google', 'ht') will return 'tps:google'
"""
def strict_lstrip(orig, to_strip):
    assert isinstance(orig, str), "non-string provided as orig to strict_lstrip: {}".format(orig)
    assert isinstance(to_strip, str), "non-string provided as to_strip to strict_lstrip: {}".format(to_strip)

    if not orig.startswith(to_strip):
        return orig

    new = orig[len(to_strip):]
    return new

"""
strict_rstrip is to rstrip as strict_lstrip is to lstrip
"""
def strict_rstrip(orig, to_strip):
    assert isinstance(orig, str), "non-string provided as orig to strict_rstrip: {}".format(orig)
    assert isinstance(to_strip, str), "non-string provided as to_strip to strict_rstrip: {}".format(to_strip)

    if not orig.endswith(to_strip):
        return orig

    new = orig[:len(orig) - len(to_strip)]
    return new

"""
We expect url is https, and ends in a file path, since that seems to be the case
for all urls indicating files to download
"""
def is_download_url(url):

    assert isinstance(url, str), "non-string provided as url to is_download_url: {}".format(url)

    protocol = "https://"

    if not url.startswith(protocol):
        # Not https
        return False

    without_protocol = strict_lstrip(url, protocol)

    slash_idx = without_protocol.find("/")
    if slash_idx < 0:
        # No file path
        return False

    domain = without_protocol[:slash_idx]
    path = without_protocol[slash_idx + 1:]

    if len(domain) < 1:
        return False

    if len(path) < 1:
        return False
    
    return True

"""
If the url conforms to is_download_url, returns the domain
"""
def get_url_domain(url):
    assert is_download_url(url), "url provided to get_url_domain is not a download url: {}".format(url)
    protocol = "https://"
    without_protocol = strict_lstrip(url, protocol)

    slash_idx = without_protocol.find("/")
    if slash_idx < 0:
        # No file path
        raise ValueError("url {} did not have a file path despite passing the check for being a download url")

    domain = without_protocol[:slash_idx]
    path = without_protocol[slash_idx + 1:]
    return domain

"""
If the url conforms to is_download_url, returns the path
"""
def get_url_path(url):
    assert is_download_url(url), "url provided to get_url_path is not a download url: {}".format(url)
    protocol = "https://"
    without_protocol = strict_lstrip(url, protocol)

    slash_idx = without_protocol.find("/")
    if slash_idx < 0:
        # No file path
        raise ValueError("url {} did not have a file path despite passing the check for being a download url")

    path = without_protocol[slash_idx + 1:]
    return path

"""
A Minecraft version may be of the form X.Y.Z where X, Y, and Z are integers,
but it may also be of the form X.Y.Z-somestring, such as if you're running
Optifine in which case you might get something like X.Y.Z-Optifine_U_J9
This function takes in a Minecraft version string and returns a string
containing only the dot-separated digits.
"""
def get_version_numbers(mc_version):
    if not validity.is_valid_minecraft_version(mc_version):
        raise ValueError("get_version_numbers must be given a valid Minecraft version string. Instead, was given {}".format(mc_version))

    if validity.is_valid_version(mc_version, MC_VERSION_PARTS):
        return mc_version

    dash_parts = mc_version.split("-")
    if len(dash_parts) == 2:
        # First part is numberic
        # Second part is text we don't need.

        if validity.is_valid_version(dash_parts[0], MC_VERSION_PARTS):
            return dash_parts[0]

    raise ValueError("{} seems to not be a valid Minecraft version; could not isolate the numeric part.".format(mc_version))

"""
sha1 hash digests appearing in the Minecraft json files
are presented as 40 hexadecimal digits
digest: a string
Returns True if the digest is the right form for a sha1 hash
False otherwise
"""
def is_sha1(digest):
    assert isinstance(digest, str), "sha1 digest given was not a string: {}".format(digest)

    if re.fullmatch(r"[0-9a-f]{40}", digest):
        return True
    return False

if __name__ == "__main__":
    print(get_minecraft_path())
