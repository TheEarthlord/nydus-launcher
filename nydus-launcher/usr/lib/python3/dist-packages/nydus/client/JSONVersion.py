
import json
import os
from nydus.client.JavaRuntime import JavaRuntime
from nydus.client import utils

# Top level keys, used to decide which method should process each piece of the version file's top dictionary
ARGUMENTS_KEY = "arguments"
GAME_KEY = "game"
JVM_KEY = "jvm"
ASSETINDEX_KEY = "assetIndex"
ID_KEY = "id"
JAVAVERSION_KEY = "javaVersion"
LIBRARIES_KEY = "libraries"
LOGGING_KEY = "logging"
MAINCLASS_KEY = "mainClass"
TYPE_KEY = "type"

# Lower level keys, usually containing one piece of data each
VALUE_KEY = "value"
FEATURES_KEY = "features"
SHA1_KEY = "sha1"
URL_KEY = "url"
COMPONENT_KEY = "component"
DOWNLOADS_KEY = "downloads"
ARTIFACT_KEY = "artifact"
PATH_KEY = "path"
NAME_KEY = "name"
RULES_KEY = "rules"
ACTION_KEY = "action"
OS_KEY = "os"
CLIENT_KEY = "client"
ARGUMENT_KEY = "argument"
FILE_KEY = "file"


VARNAME_START = "${"
VARNAME_END = "}"

"""
Returns True if name is a string and a variable for the JSON version
purposes (i.e. starts with '${', ends with '}', and has something in
between)
"""
def is_variable(name):
    if not isinstance(name, str):
        return False
    if name.startswith(VARNAME_START):
        if name.endswith(VARNAME_END):
            nstart = len(VARNAME_START)
            nend = len(name) - len(VARNAME_END)
            middle = name[nstart:nend]
            middle = middle.strip()
            if middle:
                return True
    return False

"""
Returns True if arg is a string of the form
"name=variable"
where variable begin with VARNAME_START and end with VARNAME_END
as in is_variable.
Note that strings which make is_variable True will make this function False;
this function requires something in front of the variable.
"""
def contains_variable(arg):
    if not isinstance(arg, str):
        return False
    nstart = arg.find(VARNAME_START)
    if nstart < 0:
        return False
    nend = arg.find(VARNAME_END)
    if nend < 0:
        return False

    # Start must be before end
    if nend <= nstart:
        return False

    if nstart > 0 and nend > nstart:
        if arg[nstart - 1] == "=":

            # Everything before the equals
            prepart = arg[:nstart - 1]

            # Changing nstart to the index after the end
            # the VARSTART, rather than the index of the
            # beginning
            nstart += len(VARSTART)
            middle = arg[nstart:nend]
            
            # We want the variable name and part before
            # the variable to be nonempty
            if prepart.strip() and middle.strip():
                return True
    return False
    
"""
If arg is a string which is a variable or contains a variable
(according to is_variable and contains_variable), then get
the name of that variable (the part between VARNAME_START and
VARNAME_END) and return it. Else, return empty string.
"""
def get_varname(arg):

    if is_variable(arg) or contains_variable(arg):
        nstart = arg.find(VARNAME_START) + len(VARNAME_START)
        nend = arg.find(VARNAME_END)
        middle = arg[nstart:nend]
        return middle
        
    return ""

"""
arg: string, an argument containing a variable or which is a variable
    according to is_variable or contains_variable
newval: string, a value which will be placed where the variable was in
    the argument, including removal of VARSTART and VAREND
Returns the arg with newval placed where the variable was.
If no variable can be found or newval is not a string, return empty string.
"""
def replace_varname(arg, newval):
    if not isinstance(newval, str):
        return ""

    if is_variable(arg) or contains_variable(arg):
        nstart = arg.find(VARNAME_START)
        nend = arg.find(VARNAME_END) + len(VARNAME_END)
        first_part = arg[:nstart]
        last_part = arg[nend:]
        result = first_part + newval + last_part
        return result

    return ""

# Class for storing all the information contained
# in a particular JSON version file

# In general, fields containing None or empty string did
# not appear in the json or have not yet been processed.
# Filled fields will be strings, lists with elements, or
# something else.
# This distinction is particularly useful when processing
# inheritance.

# Intention is to write the constructor such that it doesn't
# need to touch the filesystem. All user and filesystem-specific
# information is only brought in when downloading the files
# and forming the launch command.

class JSONVersion:

    """
    Accepts a dictionary, the result of parsing a JSON version file,
    and extracts all the information about that version.
    Note this class does not process inheritance. It will find if this version inherits from another,
    but will not read the ancestor version's file and add that data to this instance of its own accord.
    """

    def __init__(self, verjson):

        if not isinstance(verjson, dict):
            raise TypeError("Must be given a dictionary of JSON data to instantiate JSONVersion")

        # Core fields
        self.game_args = []
        self.jvm_args = []

        # Need to rethink details of how this is stored
        self.asset_index = None

        self.id = None

        # Will contain a JavaRuntime class instance
        self.java_runtime = None

        self.jars = []

        # Need to think carefully about how this is stored
        self.log_config = None

        self.main_class = None
        self.version_type = None
        self.inherits_from = None
        
        # Hard coded, observed from past launches
        self.user_type = "msa"

        self.read_json(verjson)

    """
    version: string, Minecraft version validated by common.validity
    Returns a JSONVersion instance for the corresponding Minecraft version.
    Works by parsing the version file then calling the JSONVersion constructor.
    """
    def from_version(version):

        if not validity.is_valid_minecraft_version(version):
            raise ValueError("Must provide valid Minecraft version to JSONVersion.from_version. Was given {}".format(version))
        
        json_file = os.path.join(utils.get_minecraft_path(), "versions", version, "{}.json".format(version))

        with open(json_file, "r") as f:
            try:
                verjson = json.load(f)
            except JSONDecodeError as e:
                raise ValueError("Failed to parse json in {} at line {} col {} char {}"\
                            \.format(json_file, e.lineno, e.colno, e.pos))
        return JSONVersion(verjson)

    """
    verjson: a dictionary containing json data from the version file.
    This method fills out the instance with the data found in the JSON.
    """
    def read_json(self, verjson):
        pass

    """
    ancestor: a JSONVersion instance
    The assumption is that the JSONVersion instance given as 'ancestor' is one this instance should inherit from.
    This method modifies this instance accordingly, overwriting and adding material from the ancestor instance as appropriate.
    """
    def inherit_from(self, ancestor):
        pass

    """
    Looks for all the files known to be needed for this Minecraft version.
    If any are missing, downloads them if possible
    """
    def download_all(self):
        pass

    """
    mc_account: an instance of MCAccount
    Many parts of the Minecraft version data involve variables, identifiable by the form "${varname}".
    This method expands all such variables in this instance's data to their real values. The method is
    only called by make_launch_command, not in the normal process of instantiating the class.
    A Minecraft account must be provided because some of the variables are username, access token, etc.
    """
    def replace_variables(self, mc_account):

        # There are two kinds of variables in the data;
        # "argname" "${varname}"
        # and
        # "argname=${varname}"
        # In the first case, the variable is a seperate argument tothe name of the data it provides.
        # In the second case, the name and variable are both contained in one argument to the process.
        # We need to search for and replace both kinds.
        pass

    """
    mc_account: an instance of MCAccount
    Returns a list of strings, the command and args to create a new process which is a Minecraft
    game running this version. Does not actually launch the game; something else needs to create
    the new process using this method's return value.
    """
    def make_launch_command(self, mc_account):
        pass
