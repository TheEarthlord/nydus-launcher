
import subprocess
import os
import json
from json.decoder import JSONDecodeError
from nydus.common import validity
from nydus.client import utils
from nydus.common.MCAccount import MCAccount
from nydus.client.DownloadFile import DownloadFile
from nydus.client.DownloadFile import MC_DOWNLOAD_DIR

# Class for storing everything we need to launch
# a specific version of Minecraft

VERSIONS_KEY = "versions"
ID_KEY = "id"
TYPE_KEY = "type"
URL_KEY = "url"
SHA1_KEY = "sha1"
INHERITS_KEY = "inheritsFrom"
LOGGING_KEY = "logging"
LOGGING_CLIENT_KEY = "client"
LOGGING_FILE_KEY = "file"
MAINCLASS_KEY = "mainClass"
LIBRARIES_KEY = "libraries"
DOWNLOADS_KEY = "downloads"
ARTIFACT_KEY = "artifact"
RULES_KEY = "rules"
NAME_KEY = "name"
ACTION_KEY = "action"
OS_KEY = "os"
PATH_KEY = "path"

DESIRED_ACTION = "allow"
DESIRED_OS = "linux"

CPJAR_SEPARATOR = ":"

# TODO
# There are lots more parameters in the version json file that this
# class doesn't handle. We really should rewrite it to handle
# everthing in there more generally.
# But need to find where to get all the variables used in those json
# files.

# The json at ~/.minecraft/versions/version_manifest_v2.json has info on all the
# different Minecraft versions available. Specifically, it gives where to
# download a json file for each version, and this json tells you the rest
# you need to know.

# Each of those version-specific json files is placed under
# ~/.minecraft/versions/<version>/<version>.json
# The version-specific jsons tell you many of the other things needed for that
# version to run, including a whole lot of other jar libraries that you should
# download and put under ~/.minecraft/libraries at the paths they individually
# specify.

# TODO
# There should also be a ~/.minecraft/versions/<version>/<version>.jar
# I don't know where you download that from.

# The json file which defines everything for this Minecraft version
# also has URLs and sha1 hashes for downloading each jar file if it doesn't
# exist.
# This class should download any such files that aren't already downloaded.

# OptiFine versions are different in a few ways.
# They do specify a few jars needed, but usually don't include
# download URLs and hashes; the file has to already exist, or else
# it won't work.
# OptiFine versions also usually inherit from the official Minecraft versions,
# so there needs to be a facility for detecting inheritance and doing
# everything in the ancestor version also.

# For a successful Minecraft launch, we want
# -cp: jars optained from version JSON
# -Dlog4j.configurationFile: whatever xml is under .minecraft/assets/log_configs but get correct answer from version JSON
# mainClass from version JSON
# --username, --version, --uuid, --accessToken from server
# --gameDir: /home/<username>/.minecraft
# --assetsDir: /home/<username>/.minecraft/assets
# --assetIndex: 16
# --userType: msa
# --versionType: release


class MCVersion:


    """
    Accepts a minecraft version (validity defined by common.validity)
    and an MCAccount instance
    """
    def __init__(self, version, mc_account):

        if not validity.is_valid_minecraft_version(version):
            raise ValueError("Must provide valid Minecraft version to MCVersion constructor. Was given {}".format(version))

        if not isinstance(mc_account, MCAccount):
            raise TypeError("Must provide an MCAccount to MCVersion constructor. Was given a {}".format(type(mc_account)))

        self.version = version

        # To be filled in from reading the version's JSON file
        # Each element in the jars list may be either a string or a DownloadFile instance.
        # DownloadFile will be used if the version's JSON included download
        # information. If not, a string which represents the jar's expected path
        # will be used. In the string case, it must already be installed in the right
        # place or launching Minecraft will fail.
        self.jars = []
        self.main_class = ""

        # MCAccount contains username, uuid, access token
        # Data obtained from server.
        self.mc_account = mc_account

        # Standard patterns based on who is logged in
        self.game_dir = utils.get_minecraft_path()
        self.assets_dir = utils.get_minecraft_assets_path()

        # Computed by looking under the assets dir
        # TODO
        # log_config may also be a DownloadFile obtained from the version json file
        self.log_config = ""

        # Hard coded, observed from past Minecraft launches
        self.asset_index = 16
        self.user_type = "msa"
        self.version_type = "release"

        self.find_log_config()
        self.read_json_file()

    """
    Gets the directory in which an xml file for log_config
    is expected to be found or placed.
    """
    def get_log_config_dir(self):
        log_cdir = os.path.join(self.assets_dir, "log_configs")
        return log_cdir

    """
    Looks for the directory log_configs under the minecraft assets
    directory. If it exists and contains an xml file, the path
    to that file is the log config parameter's value.
    This function finds that xml file and saves the path
    in the relevant class attribute.
    If there are multiple xml files, the first one found will be used.
    Raises an Exception if such a file can't be found.
    """
    def find_log_config(self):
        log_cdir = self.get_log_config_dir()
        if not os.path.isdir(log_cdir):
            raise OSError("No directory at {} to get Log4J config.".format(log_cdir))

        contents = os.listdir(log_cdir)
        for name in contents:
            filepath = os.path.join(log_cdir, name)
            if name.endswith(".xml") and os.path.isfile(filepath):
                self.log_config = filepath
                return

        raise OSError("No xml file in {} to get Log4J config from.".format(log_cdir))

    """
    Reads the json file defining this Minecraft version.
    Fills out the class with all the relevant data;
    jar files needed and class name to run when launching.
    Also processes ancestor versions if this one inherits from
    another by making more MCVersions instances.
    """
    def read_json_file(self):
        json_fname = self.get_json_file()
        with open(json_fname, "r") as f:
            try:
                version_json = json.load(f)
            except JSONDecodeError as e:
                raise ValueError("Failed to parse json in {} at line {} col {} char {}"\
                        .format(filepath, e.lineno, e.colno, e.pos))

        self.process_ancestors(version_json)
        self.read_id(version_json)
        self.read_logging(version_json)
        self.read_class(version_json)
        self.read_jars(version_json)

    """
    version_json: a dictionary, the top level of the data structure returned
        by parsing the JSON out of this Minecraft version's JSON file.
    If the current version inherits from another, this method creates an MCVersion
    instance for that version and brings all its information into this instance.
    """
    def process_ancestors(self, version_json):
        assert isinstance(version_json, dict), "Must pass a dictionary representing JSON to MCVersion.read_id. Instead, got {}".format(type(version_json))

        ancestor_id = version_json.get(INHERITS_KEY)
        if ancestor_id == None:
            # No inheritance, proceed without it
            return

        ancestor = MCVersion(ancestor_id, self.mc_account)

        # We're only going to store strings taken from the ancestor,
        # not DownloadFile instances, so make sure everything
        # the ancestor needs does get downloaded.
        ancestor.download_all()

        # Because this method is run before main class, jars,
        # and log config are taken from the current version's JSON file,
        # newer data will override the old as desired.
        self.main_class = ancestor.get_main_class()
        self.jars.extend(ancestor.get_jar_paths())
        self.log_config = ancestor.get_log_config_path()

    """
    version_json: a dictionary, the top level of the data structure returned
        by parsing the JSON out of this Minecraft version's JSON file.
    This method finds the version number stored inside the version's JSON
    and confirms it matches the one this class is configured with.
    If not, it raises an Exception.
    Returns nothing.
    """
    def read_id(self, version_json):
        assert isinstance(version_json, dict), "Must pass a dictionary representing JSON to MCVersion.read_id. Instead, got {}".format(type(version_json))

        file_id = version_json.get(ID_KEY)
        if file_id == None:
            raise KeyError("Version JSON file {} contained no key {}; could not confirm version id.".format(json_fname, ID_KEY))
        
        if file_id != self.version:
            raise ValueError("Version JSON file {} listed version id {} which does not match expected version {}".format(json_fname, file_id, self.version))

    """
    version_json: a dictionary, the top level of the data structure returned
        by parsing the JSON out of this Minecraft version's JSON file.
    This method finds the file which should be passed to the argument
    -Dlog4j.configurationFile and downloads it if necessary.
    Returns nothing. Modifies the log_config attribute if necessary.
    """
    def read_logging(self, version_json):
        assert isinstance(version_json, dict), "Must pass a dictionary representing JSON to MCVersion.read_logging. Instead, got {}".format(type(version_json))

        # If there is no entry about logging in our version json, just leave
        # it as whatever default we might have set.
        logging_dict = version_json.get(LOGGING_KEY)
        if logging_dict == None:
            return

        client_dict = logging_dict.get(LOGGING_CLIENT_KEY)
        if client_dict == None:
            return

        file_dict = client_dict.get(LOGGING_FILE_KEY)
        if file_dict == None:
            return

        fname = file_dict.get(ID_KEY)
        url = file_dict.get(URL_KEY)
        sha1 = file_dict.get(SHA1_KEY)
        if fname == None or url == None or sha1 == None:
            return

        lconfig_df = DownloadFile(url, sha1, name=fname, path=self.get_log_config_dir())
        lconfig_df.download()
        self.log_config = lconfig_df

    """
    version_json: a dictionary, the top level of the data structure returned
        by parsing the JSON out of this Minecraft version's JSON file.
    This method finds the main class which should be invoked when launching
    Minecraft.
    Returns nothing. Modifies the main_class attribute if necessary.
    """
    def read_class(self, version_json):
        assert isinstance(version_json, dict), "Must pass a dictionary representing JSON to MCVersion.read_class. Instead, got {}".format(type(version_json))

        # Either
        # a) we do not already have a main class from an ancestor
        #   then failure to get a main class from our own JSON is fatal
        # b) we do have a main class from an ancestor
        #   then we want to use our own main class if one exists
        #   but if we don't have our own, using the ancestor's is fine

        main_class = version_json.get(MAINCLASS_KEY)
        
        if not self.main_class:

            if main_class == None:
                raise ValueError("No key '{}' in file {} for version {}. Cannot get Main Class to launch Minecraft.".format(MAINCLASS_KEY, self.get_json_file(), self.version))

            if not isinstance(main_class, str):
                raise TypeError("Main Class for version {} in file {} was not a string. Instead it has type {} and looks like {}".format(self.version, self.get_json_file(), type(main_class), main_class))

            self.main_class = main_class

        elif main_class and isinstance(main_class, str):
            self.main_class = main_class

    """
    version_json: a dictionary, the top level of the data structure returned
        by parsing the JSON out of this Minecraft version's JSON file.
    This method finds all the jar files which need to be passed to Minecraft
    when launching it. It adds elements to the the 'jars' list attribute.
    These elements will either be DownloadFile instances if there's enough
    information to download the jarfile, or else strings if only the name/path
    of the file can be found.
    Returns nothing.
    """
    def read_jars(self, version_json):
        assert isinstance(version_json, dict), "Must pass a dictionary representing JSON to MCVersion.read_jars. Instead, got {}".format(type(version_json))

        jar_list = version_json.get(LIBRARIES_KEY)
        
        # While it is theoretically possible for a Minecraft version to have no jars,
        # practically it'll probably never happen so we raise an error if the key is missing.
        if jar_list == None:
            raise KeyError("Key '{}' was missing from JSON file {} for version {}. Could not get jar files for this version.".format(LIBRARIES_KEY, self.get_json_file(), self.version))

        if not isinstance(jar_list, list):
            raise TypeError("Object under key '{}' in JSON file {} for version {} is not a list (instead it's a {}). Could not get jar files for this version.".format(LIBRARIES_KEY, self.get_json_file(), self.version, type(jar_list)))

        for jar in jar_list:
            if not isinstance(jar, dict):
                raise TypeError("Object inside the jar files list in JSON file {} for version {} is not a dictionary. Instead it's {}.".format(self.get_json_file(), self.version, jar))
            
            this_jar = self.read_one_jar()
            if this_jar:
                self.jars.append(this_jar)

    """
    jar_dict: a dictionary, representing one jar file from the list of
        all jars/libraries needed by this version of Minecraft.
    This method interprets the dictionary and returns either a string
    (the absolute path to the jar), a DownloadFile (if there's enough
    information to be able to download it), or None (if something
    went wrong).
    """
    def read_one_jar(self, jar_dict):
        assert isinstance(jar_dict, dict), "Must pass a dictionary representing one jar file's part of the JSON to MCVersion.read_one_jar. Instead, got {}".format(type(jar_dict))

        jarname = jar_dict.get(NAME_KEY)

        # Even if this jar is invalid, we still want to go ahead and try the others
        # So we only return None, not raise an exception, when this dictionary is invalid
        if jarname == None or not isinstance(jarname, str):
            return None

        # See if there's a rule saying which OS this is for.
        # If there is a rule on which OS should use this,
        # and it's not the OS we're using, then skip this jar.
        # Otherwise proceed.
        rules_list = jar_dict.get(RULES_KEY)
        if isinstance(rules_list, list):
            for rule_dict in rules_list:
                if isinstance(rule_dict, dict):
                    action = rule_dict.get(ACTION_KEY)
                    if isinstance(action, str) and action == DESIRED_ACTION:
                        os_dict = rule_dict(OS_KEY)
                        if isinstance(os_dict, dict):
                            os_name = os_dict.get(NAME_KEY)
                            if os_name != DESIRED_OS:
                                return None

        # See if there's enough to make a DownloadFile instance
        downloads_dict = jar_dict.get(DOWNLOADS_KEY)
        if isinstance(downloads_dict, dict):
            artifact_dict = downloads_dict.get(ARTIFACT_KEY)
            if isinstance(artifact_dict, dict):
                download_path = artifact_dict.get(PATH_KEY)
                url = artifact_dict.get(URL_KEY)
                sha1 = artifact_dict.get(SHA1_KEY)

                if download_path and url and sha1:
                    download_fname = so.path.basename(download_path)
                    df = DownloadFile(url, sha1, name=download_fname)
                    return df

        # Otherwise we have to form a path using 'name'
        # Name tells us a path, but it starts under ~/.minecraft/<MC_DOWNLOAD_DIR>
        # (MC_DOWNLOAD_DIR is usually 'libraries')
        # and uses both colons and full stops to delimit directories instead of slashes
        # and doesn't give us the actual filename.
        # So we're going to just follow the path and add every .jar under it.

        name_parts = re.split(":|\.", name)

        dirpath = os.path.join(utils.get_minecraft_path(), MC_DOWNLOAD_DIR, name_parts)

        
        if not os.path.isdir(dirpath):
            raise FileNotFoundError("No directory at {} to get required jar files for version {} as specified in JSON file {}.".format(dirpath, self.version, self.get_json_file()))

        contents = os.listdir(dirpath)
        for name in contents:
            if name.endswith(".jar") and os.path.isfile(name):
                return os.path.join(dirpath, name)

        raise FileNotFoundError("No jar file in directory {} as expected by JSON file {} for version {}.".format(dirpath, self.get_json_file(), self.version))


    """
    Downloads the version-defining json file if it doesn't
    already exist.
    Note this uses the version manifest json file to do the downloading,
    which won't have entries for OptiFine. The OptiFine JSON needs
    to already exist, so this method will never be called.
    """
    def download_json_file(self):
        manifest = utils.get_version_manifest()
        with open(manifest, "r") as f:
            try:
                manifest_json = json.load(f)
            except JSONDecodeError as e:
                raise ValueError("Failed to parse json in {} at line {} col {} char {}"\
                        .format(filepath, e.lineno, e.colno, e.pos))
        
        versions_list = manifest_json.get(VERSIONS_KEY)
        if versions_list == None:
            raise KeyError("JSON in {} had no key '{}'; couldn't get information on Minecraft versions.".format(manifest, VERSIONS_KEY))

        for entry in versions_list:
            # We expect the versions list to contain dictionaries,
            # with keys 'id', 'type', 'url', and 'sha1'.
            # 'id' tells us the name of the version. We're looking
            # for an entry with the same id as the version we're trying
            # to process.
            # 'type' overwrites version_type if it's there
            # 'url' and 'sha1' go into downloading the file.
            # Anything that appears malformed we just skip; no need to raise
            # Exceptions.

            vers_id = entry.get(ID_KEY)
            if vers_id == None:
                continue

            if vers_id == self.version:
                # We've found the entry for our version
                # Wrong structure now is reason to raise an exception.

                vers_type = entry.get(TYPE_KEY)
                vers_sha1 = entry.get(SHA1_KEY)
                vers_url = entry.get(URL_KEY)
                
                if vers_type != None:
                    self.version_type = vers_type

                if vers_url == None:
                    raise KeyError("No key '{}' for version {} in manifest file {}; could not download missing JSON file for this version due to missing URL.".format(URL_KEY, vers_id, manifest))

                if vers_sha1 == None:
                    raise KeyError("No key '{}' for version {} in manifest file {}; could not download missing JSON file for this version due to missing hash.".format(SHA1_KEY, vers_id, manifest))

                # In a DownloadFile instance, the 'path' does not include
                # the file itself, just the directories leading to it.
                json_download_path = os.path.dirname(self.get_json_file())
                df = DownloadFile(vers_url, vers_sha1, name=vers_id, path=json_download_path)
                df.download()

                # If downloading succeeded, exit the loop
                return
    """
    Returns a boolean. True if the json file defining this Minecraft
    version exists; false if it doesn't.
    """
    def json_file_exists(self):
        return validity.is_valid_file(self.get_json_file())

    """
    Returns a string; the path to the file that tells us everything about
    this Minecraft version.
    Usually of the form
    /home/<username/.minecraft/versions/<version>/<version>.json
    """
    def get_json_file(self):
        # We don't bother looking up the manifest file
        # because it only includes the download link, not
        # the path for local storage.
        return os.path.join(self.game_dir, "versions", self.version, "{}.json".format(self.version))
    
    def get_version(self):
        return self.version

    def get_main_class(self):
        return self.main_class
    
    def get_jar_paths(self):
        jar_paths = []
        for jar in self.jars:
            if isinstance(jar, str):
                jar_paths.append(jar)
            if isinstance(jar, DownloadFile):
                jar_paths.append(jar.get_fullpath())
        return jar_paths
    
    def get_log_config_path(self):
        if isinstance(self.log_config, str):
            return self.log_config
        elif isinstance(self.log_config, DownloadFile):
            return self.log_config.get_fullpath()

    """
    Everything which can be a DownloadFile (jars, log_config)
    is checked. If not present and a DownloadFile, it is downloaded.
    If it's not a DownloadFile and not already installed, an Exception is raised.
    If this method completes without an Exception, all needed files should
    be installed.
    """
    def download_all(self):
        for jar in self.jars:
            if isinstance(jar, str):
                if not os.path.isfile(jar):
                    raise FileNotFoundError("Needed file {} for version {} does not exist and is not downloadable.".format(jar, self.version))
            elif isinstance(jar, DownloadFile):
                jar.download()
            else:
                raise TypeError("In version {} found jar of unexpected type: {}".format(self.version, type(jar)))

        if isinstance(self.log_config, str):
            if not os.path.isfile(self.log_config):
                raise FileNotFoundError("Needed file {} for version {} does not exist and is not downloadable.".format(jar, self.version))
        elif isinstance(self.log_config, DownloadFile):
            self.log_config.download()
        else:
            raise TypeError("In version {} found log config of unexpected type: {}".format(self.version, type(self.log_config)))


    """
    Returns a colon-concatenated string of absolute paths to all the jar files.
    """
    def get_cpjars(self):
        jarpaths = []
        for jar in self.jars:
            if isinstance(jar, str):
                jarpaths.append(jar)
            elif isinstance(jar, DownloadFile):
                jarpaths.append(jar.get_fullpath())
            else:
                raise TypeError("Entry in Jars list of unexpected type: {}".format(type(jar)))

        return CPJAR_SEPARATOR.join(jarpaths)

    """
    Launches an instance of Minecraft of the version
    stored in this class.
    """
    def launch(self):
        self.download_all()

        logc_path = ""
        if isinstance(self.log_config, str):
            logc_path = self.log_config
        elif isinstance(self.log_config, DownloadFile):
            logc_path = self.log_config.get_fullpath()
        else:
            raise TypeError("In version {} found log config of unexpected type: {}".format(self.version, type(self.log_config)))

        launch_command = "java -cp {} -Xmx2G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M -Dlog4j.configurationFile={} {} --username {} --version {} --gameDir {} --assetsDir {} --assetIndex 16 --uuid {} --accessToken {} --userType msa --versionType {}".format(
            self.get_cpjars(),
            logc_path,
            self.main_class,
            self.mc_account.get_username(),
            self.version,
            self.game_dir,
            self.assets_dir,
            self.mc_account.get_uuid(),
            self.mc_account.get_token(),
            self.version_type
        )

        launch_list = launch_command.split()
        subprocess.run(launch_list)

        # subprocess.run should block until the process finishes. So we'll return when
        # Minecraft is closed and we're ready to release the account.
