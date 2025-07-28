
import hashlib
import json
import os
from json.decoder import JSONDecodeError
from nydus.common import validity
from nydus.common import nydus_info
from nydus.common.MCAccount import MCAccount
from nydus.client import utils
from nydus.client import varstrings
from nydus.client.DownloadFile import DownloadFile
from nydus.client.JavaRuntime import JavaRuntime

CPJAR_SEPARATOR = ":"
JAR_NAMEPATH_SEPARATOR = ":"

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

# These are the variables which we replace with actual values
# using the data in the JSONVersion instance.
PLAYERNAME_VAR = "auth_player_name"
VERSION_VAR = "version_name"
GAMEDIR_VAR = "game_directory"
ASSETROOT_VAR = "assets_root"
ASSETINDEX_VAR = "assets_index_name"
UUID_VAR = "auth_uuid"
ACCESSTOKEN_VAR = "auth_access_token"
USERTYPE_VAR = "user_type"
VERSTIONTYPE_VAR = "version_type"
NATIVESDIR_VAR = "natives_directory"
LAUNCHERNAME_VAR = "launcher_name"
LAUNCHERVERSION_VAR = "launcher_version"
CLASSPATH_VAR = "classpath"
# Not sure why this varname is so generic, but
# it's the log configuration file path
LOGCONFIG_VAR = "path",

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

    def copy(self):
        return JSONFileStore(self.name, self.sha1, self.url)

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

# The json at ~/.minecraft/versions/version_manifest_v2.json has info on how to
# download the version json for each Minecraft version. If the desired version json
# were missing (when using from_version), we theoretically could
# look it up and try to download any missing version files.
# We don't, in part to emphasise that you should use the Minecraft launcher to set
# up before using the Nydus Launcher, and in part because each version also requires
# a jar file that's not in the version json and we don't know how to download;
# you have to use the Minecraft launcher anyway to make sure you get that one.

# It seems version_manifest_v2.json is downloaded from
# https://launchermeta.mojang.com/mc/game/version_manifest_v2.json



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

        # String, absolute path to java runtime entry binary.
        # Only filled out during download_all when the runtime class
        # is instantiated.
        self.java_runtime_bin = None

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

    def get_game_args(self):
        newlist = [a for a in self.game_args]
        return newlist

    def get_jvm_args(self):
        newlist = [a for a in self.jvm_args]
        return newlist

    def get_asset_index(self):
        if isinstance(self.asset_index, JSONFileStore):
            return self.asset_index.copy()
        else:
            return self.asset_index

    def get_id(self):
        return self.id

    def get_java_runtime(self):
        return self.java_runtime

    def get_jars(self):
        newlist = []
        for a in self.jars:
            if isinstance(a, JSONFileStore):
                newlist.append(a.copy())
            else:
                newlist.append(a)
        return newlist

    def get_log_config(self):
        if isinstance(self.log_config, JSONFileStore):
            return self.log_config.copy()
        else:
            return self.log_config

    def get_log_config_arg(self):
        return self.log_config_arg

    def get_main_class(self):
        return self.main_class

    def get_version_type(self):
        return self.version_type

    def get_inherits_from(self):
        return self.inherits_from

    def get_user_type(self):
        return self.user_type

    def get_natives_dir(self):
        # The natives dir used by the official MC launcher is
        # .minecraft/bin/<some-hash>
        # with a different hash for each version.
        # I can't figure out what string is hashed to get that directory,
        # so we're making our own.
        hashclass = hashlib.sha1()
        version_bytes = self.version.encode("utf-8")

        hashclass.update(version_bytes)
        version_hash = hashclass.hexdigest()
        natives_dir = os.path.join(utils.get_minecraft_path(), "bin", version_hash)
        return natives_dir

    """
    There is usually a jar file in the same place as the json file
    which tells us everything about the current version.
    If so, we probably need to include it in our set of jars.
    This function returns a string, the path to that primary
    jar file.
    Usually of the form
    /home/<username>/.minecraft/versions/<version>/<version>.jar
    """
    def get_main_jar_file(self):
        return os.path.join(utils.get_minecraft_path(), "versions", self.id, "{}.jar".format(self.id))

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

        if not os.path.isfile(json_file):
            raise FileNotFoundError("Version json file {} does not exist. Have you made sure to download the necessary materials with the Minecraft launcher before using the Nydus launcher?".format(json_file))

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

        if not validity.is_valid_java_runtime(runtime):
            raise ValueError("Expected key '{}' to contain a valid java runtime string, but instead got '{}' of type {}".format(COMPONENT_KEY, runtime, type(runtime)))

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
        # Note, from observation, this name is a colon-separated path under 'libraries' to a directory
        # It does not end in '.jar'; we just need to add all the jarfiles we find inside
        # the indicated directory.
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
    Note this method is not recursive. It does not find or process any inheritance of the ancestor. You should follow
    the chain of ancestor inheritance to the top, then call this method for each step down the chain, ending with the
    version you actually which to launch.
    """
    def inherit_from(self, ancestor):
        # The rules are
        # game_args, jvm_args, jars have ancestor data added to them
        # id, asset_index, java_runtime, log_config,
        # log_config_arg, main_class, version_type, user_type
        # are overwritten by ancestor data only if they don't exist
        # in the current version's data.

        ancs_game_args = ancestor.get_game_args()
        self.game_args.extend(ancs_game_args)

        ancs_jvm_args = ancestor.get_jvm_args()
        self.jvm_args.extend(ancs_jvm_args)

        ancs_jars = ancestor.get_jars()
        self.jars.extend(ancs_jars)

        if not self.id:
            self.id = ancestor.get_id()

        if not self.asset_index:
            self.asset_index = ancestor.get_asset_index()

        if not self.java_runtime:
            self.java_runtime = ancestor.get_java_runtime()

        if not self.log_config:
            self.log_config = ancestor.get_log_config()

        if not self.log_config_arg:
            self.log_config_arg = ancestor.get_log_config_arg()

        if not self.main_class:
            self.main_class = ancestor.get_main_class()

        if not self.version_type:
            self.version_type = ancestor.get_version_type()

        if not self.user_type:
            self.user_type = ancestor.get_user_type()

    """
    Looks for all the files known to be needed for this Minecraft version.
    If any are missing, downloads them if possible.
    Note this method requires a user, a .minecraft directory, and so on.
    """
    def download_all(self):

        self.download_asset_index()
        self.download_java_runtime()
        self.download_jars()
        self.download_log_config()

    def download_asset_index(self):
        if isinstance(self.asset_index, JSONFileStore):
            fpath = utils.get_asset_index_path(self.asset_index.get_name())
            dirpath = os.path.dirname(fpath)
            fname = os.path.basename(fpath)

            df = DownloadFile(
                self.asset_index.get_url(),
                self.asset_index.get_sha1(),
                name=fname,
                path=dirpath,
            )
            df.download()

        else:
            raise TypeError("Attempted to download asset_index but object was '{}' instead of a JSONFileStore".format(self.asset_index))

    """
    This method also fills out the java_runtime_bin field
    """
    def download_java_runtime(self):
        jr = JavaRuntime(self.java_runtime)
        jr.setup_runtime()
        self.java_runtime_bin = jr.get_java()

    def download_jars(self):
        for jarfile in self.jars:
            if isinstance(jarfile, str):
                # Nothing to download, but we need to check the directory exists
                name_parts = jarfile.split(JAR_NAMEPATH_SEPARATOR)
                dirpath = os.path.join(utils.get_minecraft_libraries_path(), *name_parts)
                if not os.path.isdir(dirpath):
                    raise FileNotFoundError("No directory at {} to get undownloadable required jar files for JSONVersion".format(dirpath))

            elif isinstance(jarfile, JSONFileStore):
                # If a JSONFileStore was used, the file
                # had a path which was stored as the id
                path = jarfile.get_name()
                url = jarfile.get_url()
                sha1 = jarfile.get_sha1()

                fname = os.path.basename(path)

                # The DownloadFile class, if not given a path to put the file under,
                # assumes it's a jar which belongs under 'libraries' and uses the
                # url to figure the rest of the path out.
                df = DownloadFile(url, sha1, name=fname)
                df.download()

            else:
                raise TypeError("In list of jars, was expecting only string and JSONFileStore, but found {}".format(type(jarfile)))

    def download_log_config(self):
        if isinstance(self.log_config, JSONFileStore):
            dirpath = utils.get_minecraft_log_config_dir()
            fname = self.log_config.get_name()

            df = DownloadFile(
                self.log_config.get_url(),
                self.log_config.get_sha1(),
                name=fname,
                path=dirpath,
            )
            df.download()

        else:
            raise TypeError("Attempted to download log_config but object was '{}' instead of a JSONFileStore".format(self.log_config))


    """
    Calculates the full contents of the classpath variable (colon-separated
    list of absolute paths to all the jarfiles).
    Returns the result as a string.
    """
    def compute_classpath(self):

        abs_jarpaths = []

        # There is a jar file ~/.minecraft/versions/<version>/<version>.jar
        # which is not explicitly listed in the json, but it needed for Minecraft
        # to launch.
        # We add it to the list here, rather than when instantiating the class, so
        # that it won't be inherited from ancestors.
        main_jar_path = self.get_main_jar_file()
        if os.path.isfile(main_jar_path):
            self.jars.append(main_jar_path)

        for jar in self.jars:
            if os.path.isabs(jar):
                abs_jarpath.append(jar)
            elif isinstance(jar, str):
                # The file did not provide download information; we have to
                # infer its path using only its name.
                # Files without download information usually form their name
                # using their path under 'libraries' colon-separated.
                # The name only contains a path to a directory; we need to add all
                # the jarfiles inside that directory to our classpath.

                name_parts = jar.split(JAR_NAMEPATH_SEPARATOR)
                dirpath = os.path.join(utils.get_minecraft_libraries_path(), *name_parts)
                contents = os.listdir(dirpath)
                for name in contents:
                    fullpath = os.path.join(dirpath, name)
                    if name.endswith(".jar") and os.path.isfile(fullpath):
                        abs_jarpaths.append(fullpath)

            elif isinstance(jar, JSONFileStore):
                # The file provided download information and we can use
                # the DownloadFile class to infer its path.
                path = jar.get_name()
                url = jar.get_url()
                sha1 = jar.get_sha1()

                fname = os.path.basename(path)

                # The DownloadFile class, if not given a path to put the file under,
                # assumes it's a jar which belongs under 'libraries' and uses the
                # url to figure the rest of the path out.
                df = DownloadFile(url, sha1, name=fname)
                abs_jarpaths.append(df.get_fullpath())

        classpath = CPJAR_SEPARATOR.join(abs_jarpath)
        return classpath

    """
    Calculates the full path to the log config xml file
    using the JSONVersion's instance data.
    Returns the result as a string.
    """
    def compute_log_path(self):
        dirpath = utils.get_minecraft_log_config_dir()
        fname = self.log_config.get_name()
        return os.path.join(dirpath, fname)

    """
    mc_account: an instance of MCAccount
    Many parts of the Minecraft version data involve variables, identifiable by the form "${varname}".
    This method expands all such variables in this instance's data to their real values. Therefore,
    it will modify the contents of fields jvm_args, log_config_arg, and game_args using other data
    the class has stored.
    The method is only called by make_launch_command, not in the normal process of instantiating the class.
    A Minecraft account must be provided because some of the variables are username, access token, etc.
    """
    def replace_variables(self, mc_account):

        # Dicts which tells us, for each variable name, the method
        # that gets its value. We have to define the dict here
        # because some of the methods are on the current JSONVersion
        # dict.
        REPLACE_VARNAMES = {
            PLAYERNAME_VAR: mc_account.get_username,
            VERSION_VAR: self.get_id,
            GAMEDIR_VAR: utils.get_minecraft_path,
            ASSETROOT_VAR: utils.get_minecraft_assets_path,
            ASSETINDEX_VAR: self.asset_index.get_name,
            UUID_VAR: mc_account.get_uuid,
            ACCESSTOKEN_VAR: mc_account.get_token,
            USERTYPE_VAR: self.get_user_type,
            VERSTIONTYPE_VAR: self.get_version_type,
            NATIVESDIR_VAR: self.get_natives_dir,
            LAUNCHERNAME_VAR: nydus_info.get_launcher_name,
            LAUNCHERVERSION_VAR: nydus_info.get_launcher_version,
            CLASSPATH_VAR: self.compute_classpath,
            LOGCONFIG_VAR: self.compute_log_path,
        }

        # There are two kinds of variables in the data;
        # "argname" "${varname}"
        # and
        # "argname=${varname}"
        # In the first case, the variable is a seperate argument tothe name of the data it provides.
        # In the second case, the name and variable are both contained in one argument to the process.
        # We need to search for and replace both kinds.

        # First we delete the variables that are to be ignored
        varstrings.remove_ignored_variables_from_list(self.game_args)
        varstrings.remove_ignored_variables_from_list(self.jvm_args)

        # Then we expand the variables that are to be used
        varstrings.replace_variables_in_list(self.game_args, REPLACE_VARNAMES)
        varstrings.replace_variables_in_list(self.jvm_args, REPLACE_VARNAMES)

        if varstrings.is_variable(self.log_config_arg) or varstrings.contains_variable(self.log_config_arg):
            varname = varstrings.get_varname(self.log_config_arg)
            varfunc = REPLACE_VARNAMES.get(varname)
            if not varfunc:
                raise ValueError("Found variable name {} in argument {} but there was no function to compute the variable's true value".format(varname, self.log_config_arg))

            value = varfunc()

            newarg = replace_varname(self.log_config_arg, value)
            self.log_config_arg = newarg

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

        if not self.java_runtime_bin:
            raise ValueError("JSONVersion {} not ready to launch: no java runtime binary path; did you call download_all first?".format(self.id))

    """
    mc_account: an instance of MCAccount
    Returns a list of strings, the command and args to create a new process which is a Minecraft
    game running this version. Does not actually launch the game; something else needs to create
    the new process using this method's return value.
    May raise exceptions if the instance does not have sufficient data to launch Minecraft.
    """
    def make_launch_command(self, mc_account):

        if not isinstance(mc_account, MCAccount):
            raise TypeError("To make a launch command, you must pass an MCAccount instance. Instead, got a {}".format(type(mc_account)))

        self.check_launch_ready()

        self.replace_variables(mc_account)

        # Launch command is as follows:
        # java runtime
        # jvm args (which includes -cp and the jars)
        # log config arg
        # main class
        # game args (including version, username, access token, etc)

        launch_command = [
            "{}".format(self.java_runtime_bin)
        ]

        launch_command.extend(["{}".format(a) for a in self.jvm_args])
        launch_command.append("{}".format(self.log_config_arg))
        launch_command.append("{}".format(self.main_class))
        launch_command.extend(["{}".format(a) for a in self.game_args])
        return launch_command

