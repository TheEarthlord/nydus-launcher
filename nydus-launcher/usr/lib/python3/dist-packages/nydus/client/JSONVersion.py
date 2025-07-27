
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

ALLOW_ACTION = "allow"

USERNAME_ARG = "--username"
UUID_ARG = "--uuid"
ACCESSTOKEN_ARG = "--accessToken"


# Class used as a temporary store for data about
# files which may need to be downloaded in the
# future, without resolving full paths.
class JSONFileStore:

    """
    name: nonempty string
    sha1: a sha1 hash digest, in accordance with utils.is_sha1
    url: a file download url, in accordance with utils.is_download_url
    """
    def __init__(self, name, sha1, url):

        if not validity.is_nonempty_str(name):
            raise ValueError("JSONFileStore expected a nonempty string as name but was instead given '{}'".format(name))

        if not utils.is_sha1(sha1):
            raise ValueError("JSONFileStore provided a sha1 which was not a properly formatted sha1 hash digest: {}".format(sha1))

        if not utils.is_download_url(url):
            raise ValueError("JSONFileStore provided a url which was not a properly formatted download url: {}".format(url))

        self.name = name
        self.sha1 = sha1
        self.url = url

    def get_name(self):
        return self.name

    def get_sha1(self):
        return self.sha1

    def get_url(self):
        return self.url

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

        # Holds a JSONFileStore to keep the data we need to know
        # for file download and launch
        self.asset_index = None

        self.id = None

        # Will contain a string, the runtime name
        # When it comes to downloading stuff, create
        # a JavaRuntime instance using the name.
        self.java_runtime = None

        # Will contain a mix of strings (for the files which can't be downloaded)
        # and JSONFileStores (for the files which can be downloaded and we need to hold the data until downloads and launch)
        self.jars = []

        # Holds a JSONFileStore to keep the data we need to know
        # for file download and launch
        self.log_config = None
        self.log_config_arg = None

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
        
        new_args = JSONVersion.read_arglist(gamejson)
        self.game_args.extend(new_args)

    """
    jvmjson: contents under the key "jvm" under the key "arguments" in a version json.
        Should be a list containing strings and dictionaries. The dictionaries are
        args with attached rules for when they should and should not be included.
        The strings are simple arguments to include every time.
    """
    def read_jvm_arguments(self, jvmjson):
        if not isinstance(jvmjson, list):
            raise TypeError("JSONVersion expected a list under key 'jvm' under key 'arguments' but got a {}".format(type(jvmjson)))

        new_args = JSONVersion.read_arglist(jvmjson)
        self.jvm_extend(new_args)

    """
    assetjson: contents under the key "assetIndex" in a version json.
        Should be a dictionary describing asset and asset index.
    """
    def read_assetindex(self, assetjson):
        if not isinstance(assetjson, dict):
            raise TypeError("Expected a dictionary under key 'assetIndex' in version json, but got a {}".format(type(assetjson)))
        asset_id = assetjson.get(ID_KEY)
        if not asset_id:
            raise KeyError("Expected asset index under key {} but key did not exist".format(ID_KEY))

        asset_hash = assetjson.get(SHA1_KEY)
        if not asset_hash:
            raise KeyError("Expected assetIndex hash under key {} but key did not exist".format(SHA1_KEY))

        asset_url = assetjson.get(URL_KEY)
        if not asset_url:
            raise KeyError("Expected assetIndex url under key {} but key did not exist".format(URL_KEY))

        asset_store = JSONFileStore(asset_id, asset_hash, asset_url)

        self.asset_index = asset_store

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

        if not isinstance(javajson, dict):
            raise TypeError("Expected a dictionary under the key 'javaVersion' but got {} instead".format(type(javajson)))

        runtime = javajson.get(COMPONENT_KEY)

        if not validity.is_nonempty_str(runtime):
            raise ValueError("Expected key '{}' to contain a nonempty string for the java runtime, but instead got '{}' of type {}".format(COMPONENT_KEY, runtime, type(runtime)))

        self.java_runtime = runtime

    """
    libjson: contents under the key "libraries" in a version json.
        Should be a list containing dictionaries, each describing one jar file needed.
    """
    def read_libraries(self, libjson):
        if not isinstance(libjson, list):
            raise TypeError("Expected a list under the key 'libraries', but got {} instead".format(type(libjson)))

        for elem in libjson:
            if not isinstance(elem, dict):
                raise TypeError("Expected all elements of the library list to be dictionaries, but found one which is {}: '{}'".format(type(elem), elem))
            self.read_one_jar(elem)

    """
    jarjson: element inside the list under 'libraries' in version json.
        Should be a dictionary.
    This method processes the element to figure out everything that needs to be known about it, and adds it to the list of all jars.
    """
    def read_one_jar(self, jarjson):
        
        # First check if there are rules.
        # If there are rules and they fail, don't include the jar

        if RULES_KEY in jarjson:
            ruleslist = jarjson[RULES_KEY]
            resolution = self.resolve_rule(ruleslist)
            if not resolution:
                return

        # Second check if there is download information.

        downdict = jarjson.get(DOWNLOADS_KEY)
        if isinstance(downdict, dict):

            artdict = downdict.get(ARTIFACT_KEY)

            if not isinstance(artifact_dict, dict):
                raise KeyError("Expected key '{}' under key '{}' i a jar's info json to contain a dictionary, but got {}".format(ARTIFACT_KEY, DOWNLOADS_KEY, type(artifact_dict)))

            jar_path = artifact_dict.get(PATH_KEY)
            if not jar_name:
                raise KeyError("Expected jar path under key {} but key did not exist".format(PATH_KEY))

            jar_hash = artifact_dict.get(SHA1_KEY)
            if not jar_hash:
                raise KeyError("Expected jar hash under key {} but key did not exist".format(SHA1_KEY))

            jar_url = artifact_dict.get(URL_KEY)
            if not jar_url:
                raise KeyError("Expected jar url under key {} but key did not exist".format(URL_KEY))

            jar_store = JSONFileStore(jar_path, jar_hash, jar_url)

            self.jars.append(jar_store)

        # If no download information, just store the name as a string
        else:
            jar_name = jarjson.get(NAME_KEY)
            if validity.is_nonempty_str(jar_name):
                self.jars.append(jar_name)
            else:
                raise KeyError("Expected a 'name' key to contain a string as name for a jar file, but found '{}' under the key instead".format(jar_name))


    """
    logjson: contents under the key "logging" in a version json.
        Should be a dictionary describing the log4j configuration file.
    """
    def read_logging(self, logjson):
        if not isinstance(logjson, dict):
            raise TypeError("Expected the contents of key 'logging' in version json to be a dictionary, but got {}".format(type(logjson)))

        clidict = logjson.get(CLIENT_KEY)
        if not isinstance(clidict, dict):
            raise KeyError("Expected a dictionary under key '{}', but it was missing from the logging dictionary: {}".format(CLIENT_KEY, logjson))

        arg = clidict.get(ARGUMENT_KEY)
        if not validity.is_nonempty_str(arg):
            raise ValueError("Expected an argument string under the key '{}', but it was missing from the logging client dictionary {}".format(ARGUMENT_KEY, clidict))

        self.log_config_arg = arg

        filedict = clidict.get(FILE_KEY)
        if not isinstance(filedict, dict):
            raise KeyError("Expected a dictionary under key '{}', but it was missing from the logging client dictionary: {}".format(FILE_KEY, clidict))

        log_id = filedict.get(ID_KEY)
        if not log_id:
            raise KeyError("Expected logging id under key {} but key did not exist".format(ID_KEY))

        log_hash = filedict.get(SHA1_KEY)
        if not log_hash:
            raise KeyError("Expected logfile hash under key {} but key did not exist".format(SHA1_KEY))

        log_url = filedict.get(URL_KEY)
        if not log_url:
            raise KeyError("Expected logfile url under key {} but key did not exist".format(URL_KEY))

        log_store = JSONFileStore(log_id, log_hash, log_url)

        self.log_config = log_store


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
    rulelist: a list, the contents of the 'rules' key in an object in the version json
    Rules determine whether an element should be included or ignored, based
    on parameters like which OS you're running on.
    The list contains dictionaries, each representing a rule and containing a key "action" and
    some information about under what circumstances the action should be taken.
    So far I've only seen "allow" actions, meaing the object should be included if
    the rule is met.
    This method looks at the rule list and returns True if the corresponding
    element should be included, False if not.
    """
    def resolve_rule(rulelist):
        
        # If these are in the rule, the rule matches us
        wanted_elements = {
            "features": {
            },
            "os": {
                "name": "linux",
                "arch": "x86",
            }
        }

        if not isinstance(rulelist, list):
            raise TypeError("Contents of 'rules' key in version json should be a list; instead, got '{}' of type {}".format(rulelist, type(rulelist)))

        for rule in rulelist:
            for key in rule:
                if key == ACTION_KEY:
                    is_allow = (key == ALLOW_ACTION)
                else:
                    # Check that the data structure in the rule
                    # is present in the desired_elements dict
                    # If so, it passes.

                    rule_obj = rule
                    wanted_obj = wanted_elements

                    while True:
                        if len(rule_obj) > 1:
                            rkey = rule_obj.keys()[0]
                            rval = rule_obj[rkey]

                            wval = wanted_obj.get(rkey)
                            if type(wval) == type(rval):
                                if isinstance(wval, dict):
                                    rule_obj = rval
                                    wanted_obj = wval
                                elif isinstance(wval, str):
                                    if rval == wval:
                                        # The rule has a structure matching the contents of the "wanted elements" dictionary,
                                        # so the rule passes.
                                        return True
                                else:
                                    break
                            else:
                                break
                        else:
                            break
        return False


    """
    arglist: a list of dictionaries and strings.
        Each dict should contain a "rules" key and a "value" key.
    This method reads the list and returns all the "values" which
    correspond to a "rule" which is met.
    """
    def read_arglist(arglist):
        met_args = []

        for elem in arglist:
            if isinstance(elem, str):
                met_args.append(elem)

            elif isinstance(elem, dict):

                rules = elem.get(RULES_KEY)
                if not isinstance(rules, list):
                    raise KeyError("JSONVersion expected a key 'rules' containing a list inside a dictionary about an argument, but there was not one. The dictionary: {}".format(elem))
                rule_passed = JSONVersion.resolve_rule(rules)
                if rule_passed:
                    values = elem.get(VALUE_KEY)
                    if values == None:
                        raise KeyError("JSONVersion expected a key 'value' inside a dictionary about an argument, but there was not one. The dictionary: {}".format(elem))

                    if isinstance(values, str):
                        met_args.append(values)
                    elif isinstance(values, list):
                        for arg in values:
                            if isinstance(arg, str):
                                met_args.append(arg)
                    else:
                        raise TypeError("Expected contents of key 'value' regarding an argument to be a string or list, but was {}".format(type(values)))

            else:
                raise TypeError("JSONVersion found unexpected data type in list of args: {}".format(type(elem)))

        return met_args

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

        if not self.log_config_arg:
            raise ValueError("JSONVersion {} not ready to launch: no log config argument".format(self.id))

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
