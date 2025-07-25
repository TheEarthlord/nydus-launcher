
import json
import os
from json.decoder import JSONDecodeError
from nydus.client import validity
from nydus.client import utils
from nydus.client.JavaRuntime import JavaRuntime

# Top level keys, used to decide which method should process each piece of the version file's top dictionary
ARGUMENTS_KEY = "arguments"
ASSETINDEX_KEY = "assetIndex"
ID_KEY = "id"
INHERITSFROM_KEY = "inheritsFrom"
JAVAVERSION_KEY = "javaVersion"
LIBRARIES_KEY = "libraries"
LOGGING_KEY = "logging"
MAINCLASS_KEY = "mainClass"
TYPE_KEY = "type"

# Lower level keys, usually containing one piece of data each
GAME_KEY = "game"
JVM_KEY = "jvm"
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


USERNAME_ARG = "--username"
UUID_ARG = "--uuid"
ACCESSTOKEN_ARG = "--accessToken"


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

# TODO there needs to be a final validity check of the JSONVersion data
# This determines that the version is fine to go ahead with launching,
# that it has all the different pieces of data needed for a valid Minecraft
# launch.
# Also need to at some point check that any inheritance setting does not inherit
# from itself, otherwise there could be infinite loops.

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

        # Will contain a string, the runtime name
        # When it comes to downloading stuff, create
        # a JavaRuntime instance using the name.
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
        self.sanity_check()

    """
    Called at the end of instantiation to make sure none of the data is
    broken in unfixable ways.
    This is not the check that the data is complete enough to launch Minecraft
    with, as some data may only be filled in after inheritance is processed,
    which is done manually after instantiation, and therefore after this method.
    Returns nothing; if problems are found, raises an exception.
    """
    def sanity_check(self):
        if self.inherits_from == self.id:
            raise ValueError("JSONVersion with id {} is set to inherit from itself; this is an infinte loop and not allowed".format(self.id))

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
        for key in verjson:
            value = verjson[key]
            if key == ARGUMENTS_KEY:
                self.read_arguments(value)
            elif key == ASSETINDEX_KEY:
                self.read_assetindex(value)
            elif key == ID_KEY:
                self.read_id(value)
            elif key == INHERITSFROM_KEY:
                self.read_inheritsfrom(value)
            elif key == JAVAVERSION_KEY:
                self.read_javaversion(value)
            elif key == LIBRARIES_KEY:
                self.read_libraries(value)
            elif key == LOGGING_KEY:
                self.read_logging(value)
            elif key == MAINCLASS_KEY:
                self.read_mainclass(value)
            elif key == TYPE_KEY:
                self.read_type(value)
            else:
                raise ValueError("Unrecognised key in version json top level: {}".format(key))

    """
    argjson: contents under the key "arguments" in a version json.
        Should be a dictionary containing two keys, "game", and "jvm".
    """
    def read_arguments(self, argjson):
        if not isinstance(argjson, dict):
            raise TypeError("JSONVersion expected a dict under key 'arguments' but got a {}".format(type(argjson)))
        for key in argjson:
            value = argjson[key]
            if key == GAME_KEY:
                self.read_game_arguments(value)
            elif key == JVM_KEY:
                self.read_jvm_arguments(value)
            else:
                raise ValueError("Unrecognised key in version json under 'arguments': {}".format(key))

    """
    gamejson: contents under the key "game" under the key "arguments" in a version json.
        Should be a list containing strings and dictionaries. The dictionaries are
        args with attached rules for when they should and should not be included.
        The strings are simple arguments to include every time.
    """
    def read_game_arguments(self, gamejson):
        if not isinstance(gamejson, list):
            raise TypeError("JSONVersion expected a list under key 'game' under key 'arguments' but got a {}".format(type(gamejson)))

        for elem in gamejson:
            if isinstance(elem, str):
                self.game_args.append(elem)
            elif isinstance(elem, dict):
                #TODO
                pass
            else:
                raise TypeError("JSONVersion found unexpected data type in list of game args: {}".format(type(elem)))

    """
    jvmjson: contents under the key "jvm" under the key "arguments" in a version json.
        Should be a list containing strings and dictionaries. The dictionaries are
        args with attached rules for when they should and should not be included.
        The strings are simple arguments to include every time.
    """
    def read_jvm_arguments(self, jvmjson):
        if not isinstance(jvmjson, list):
            raise TypeError("JSONVersion expected a list under key 'jvm' under key 'arguments' but got a {}".format(type(jvmjson)))

        for elem in jvmjson:
            if isinstance(elem, str):
                self.jvm_args.append(elem)
            elif isinstance(elem, dict):
                #TODO
                pass
            else:
                raise TypeError("JSONVersion found unexpected data type in list of game args: {}".format(type(elem)))

    """
    assetjson: contents under the key "assetIndex" in a version json.
        Should be a dictionary describing asset and asset index.
    """
    def read_assetindex(self, assetjson):
        pass

    """
    idjson: contents under the key "id" in a version json.
        Should be a string, the version name.
    """
    def read_id(self, idjson):
        if validity.is_valid_minecraft_version(idjson):
            self.id = idjson
        else:
            raise ValueError("JSONVersion expected a minecraft version string under the key 'id', but got '{}' of type {}".format(idjson, type(idjson)))


    """
    inheritjson: contents under the key "inheritsFrom" in a version json.
        Should be a string, the version name which this version inherits from.
    """
    def read_inheritsfrom(self, inheritjson):
        if validity.is_valid_minecraft_version(inheritjson):
            self.inherits_from = inheritjson
        else:
            raise ValueError("JSONVersion expected a minecraft version string under the key 'inheritsFrom', but got '{}' of type {}".format(inheritjson, type(inheritjson)))
    
    """
    javajson: contents under the key "javaVersion" in a version json.
        Should be a dictionary describing the java runtime needed.
    """
    def read_javaversion(self, javajson):
        pass

    """
    libjson: contents under the key "libraries" in a version json.
        Should be a list containing dictionaries, each describing one jar file needed.
    """
    def read_libraries(self, libjson):
        pass

    """
    logjson: contents under the key "logging" in a version json.
        Should be a dictionary describing the log4j configuration file.
    """
    def read_logging(self, logjson):
        pass

    """
    classjson: contents under the key "mainClass" in a version json.
        Should be a string, the main class to invoke when launching Minecraft.
    """
    def read_mainclass(self, classjson):
        if validity.is_nonempty_str(classjson):
            self.main_class = classjson
        else:
            raise ValueError("JSONVersion expected a string under the key 'mainClass', but got '{}' of type {}".format(classjson, type(classjson)))

    """
    typejson: contents under the key "type" in a version json.
        Should be a string, the type of Minecraft version this is.
        Usually it's "release".
    """
    def read_type(self, typejson):
        if validity.is_nonempty_str(typejson):
            self.type = typejson
        else:
            raise ValueError("JSONVersion expected a string under the key 'type', but got '{}' of type {}".format(typejson, type(typejson)))

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
    Checks that all the data is complete enough to create a launch command with.
    This method does not check that files have been downloaded and correctly stored;
    only that the right fields are present in the JSONVersion instance.
    This includes
    - game_args must be nonempty and must include username, uuid, and access token
    - jvm_args must be nonempty
    - asset_index must exist
    - id must exist
    - java_runtime must exist
    - jars must be nonempty
    - log_config must exist
    - main_class must exist
    - version_type must exist
    - user_type must exist
    Returns nothing. Raises an exception if something is missing.
    """
    def check_launch_ready(self):
        if not self.id:
            raise ValueError("JSONVersion not ready to launch: no id")

        if not self.game_args:
            raise ValueError("JSONVersion {} not ready to launch: no game args".format(self.id))

        if not USERNAME_ARG in self.game_args:
            raise ValueError("JSONVersion {} not ready to launch: username argument missing from game args")

        if not UUID_ARG in self.game_args:
            raise ValueError("JSONVersion {} not ready to launch: uuid argument missing from game args")

        if not ACCESSTOKEN_ARG in self.game_args:
            raise ValueError("JSONVersion {} not ready to launch: access token argument missing from game args")

        if not self.jvm_args:
            raise ValueError("JSONVersion {} not ready to launch: no jvm args".format(self.id))

        if not self.jars:
            raise ValueError("JSONVersion {} not ready to launch: no jars".format(self.id))

        if not self.asset_index:
            raise ValueError("JSONVersion {} not ready to launch: no asset index".format(self.id))

        if not self.java_runtime:
            raise ValueError("JSONVersion {} not ready to launch: no java runtime".format(self.id))

        if not self.log_config:
            raise ValueError("JSONVersion {} not ready to launch: no log config".format(self.id))

        if not self.main_class:
            raise ValueError("JSONVersion {} not ready to launch: no main class".format(self.id))

        if not self.version_type:
            raise ValueError("JSONVersion {} not ready to launch: no version type".format(self.id))

        if not self.user_type:
            raise ValueError("JSONVersion {} not ready to launch: no user type".format(self.id))

    """
    mc_account: an instance of MCAccount
    Returns a list of strings, the command and args to create a new process which is a Minecraft
    game running this version. Does not actually launch the game; something else needs to create
    the new process using this method's return value.
    May raise exceptions if the instance does not have sufficient data to launch Minecraft.
    """
    def make_launch_command(self, mc_account):
        pass
