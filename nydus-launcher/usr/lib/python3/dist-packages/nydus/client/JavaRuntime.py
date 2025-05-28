import os
import json
from json.decoder import JSONDecodeError
from nydus.common import validity
from nydus.client.DownloadFile import DownloadFile

MANIFEST_KEY = "manifest"
DESIRED_OS = "linux"
SHA1_KEY = "sha1"
URL_KEY = "url"
FILES_KEY = "files"
TYPE_KEY = "type"
DOWNLOADS_KEY = "downloads"
RAW_KEY = "raw"
EXECUTABLE_KEY = "executable"
TARGET_KEY = "target"

EXEC_MODE = 0o775

# The json at ~/.minecraft/versions/jre_manifest.json
# contains the key "manifest". The corresponding dictionary
# has keys for different operating systems (we want "linux")
# and under those information for different java runtimes
# used by Minecraft. The file download information there
# only gives you that specific runtime's manifest file,
# a json file which tells you all the other materials
# you need for that particular java runtime and where to
# download them from.
# Runtimes are placed at
# ~/.minecraft/runtime/<runtime-name>/<os-name>/<runtime-name>/<path-from-manifest>
# The runtime manifest file doesn't seem to be stored anywhere
# under ~/.minecraft. So we'll probably put it in the directory
# under ~/.minecraft/runtime/<runtime-name>/<os-name> then get rid of it when finished.

# Which Java runtime you need for a specific Minecraft version is
# in that version's json file under javaVersion -> component.
# That's handled by MCVersion.

# Class to interpret individual files from the Java runtime manifest

class JavaRuntimeFile:

    """
    fname: string. The key in the runtime manifest for this file, which is also the
        filename/path to the file under the runtime's directory.
    fdata: dictionary. The json under this file's key in the runtime manifest.
    runtime_dir: string. The absolute path to where all of the files for this runtime
        should be stored. Probably of the form
        /home/<username>/.minecraft/runtime/<runtime-name>/<os-name>/<runtime-name>
    There are three types of files present in java runtime manifests: files, directories,
    and links.
    Files need to be downloaded. For this purpose a DownloadFile instance will be created
    containing the url, sha1, etc. Files might need to be marked executable.
    Directories need nothing done; the files inside them will cause them to be created
    when the relevant DownloadFile instances get used.
    Links need to be created but require no downloads to do so.
    Instantiating this class doesn't affect the Minecraft environment; only calling
    the "install" method will actually download data, create files, change permissions, etc.
    """
    def __init__(self, fname, fdata, runtime_dir):

        assert os.path.isabs(runtime_dir), "Runtime directory must be an absolute path. Instead, got {}".format(runtime_dir)

        assert isinstance(fdata, dict), "Data given to JavaRuntimeFile must be a dictionary. Instead, got {}".format(type(fdata))

        assert isinstance(fname, str), "Filename key given to JavaRuntimeFile must be a string. Instead, got {} containing {}".format(type(fname), fname)

        self.TYPE_FILE = "file"
        self.TYPE_DIRECTORY = "directory"
        self.TYPE_LINK = "link"

        self.FILETYPES = [
            self.TYPE_FILE,
            self.TYPE_DIRECTORY,
            self.TYPE_LINK
        ]

        self.path = os.path.join(runtime_dir, fname)
        self.runtime_dir = runtime_dir
        self.executable = False
        self.type = self.FILETYPES[0]
        self.downloadfile = None
        self.target = ""

        self.read_data(fdata)

    """
    Reads the dictionary of json given at instantiation and
    fills out member variables accordingly
    """
    def read_data(self, fdata):
        self.read_type(fdata)

        if self.type == self.TYPE_FILE:
            self.read_type_file(fdata)
        elif self.type == self.TYPE_DIRECTORY:
            self.read_type_directory(fdata)
        elif self.type == self.TYPE_LINK:
            self.read_type_link(fdata)
        else:
            raise ValueError("JavaRuntimeFile with path {} had unrecognised type '{}'. Recognised types are {}".format(self.path, self.type, self.FILETYPES))
    
    """
    Finds the type of this file and sets it in the type field
    """
    def read_type(self, fdata):
        ftype = fdata.get(TYPE_KEY)
        if ftype == None:
            raise KeyError("No type specified for file with path {} in runtime manifest; key {} is absent from JSON".format(self.path, TYPE_KEY))

        if ftype in self.FILETYPES:
            self.type = ftype
        else:
            raise ValueError("File with path {} was given invalid type {} in runtime manifest. Recognised types are {}".format(self.path, self.FILETYPES))

    """
    Fills out data for a JavaRuntimeFile of type file
    """
    def read_type_file(self, fdata):
        
        downloads = fdata.get(DOWNLOADS_KEY)

        if downloads == None or not isinstance(downloads, dict):
            raise ValueError("JavaRuntimeFile with type file, path {} cannot be created; the runtime manifest JSON does not contain a dictionary under the key '{}'".format(self.path, DOWNLOADS_KEY))

        raw_downloads = downloads.get(RAW_KEY)
        if raw_downloads == None or not isinstance(raw_downloads, dict):
            raise ValueError("JavaRuntimeFile with type file, path {} cannot be created; the runtime manifest JSON does not contain a dictionary under the key '{}'".format(self.path, RAW_KEY))
        
        url = raw_downloads.get(URL_KEY)
        sha1 = raw_downloads.get(SHA1_KEY)
        
        dirpath = os.path.dirname(self.path)
        fname = os.path.basename(self.path)
        df = DownloadFile(url, sha1, name=fname, path=dirpath)
        self.downloadfile = df
        
        execval = fdata.get(EXECUTABLE_KEY)
        if not isinstance(execval, bool):
            raise ValueError("JavaRuntimeFile with type file, path {} cannot be created; the runtime manifest JSON does not contain a boolean under the key '{}'".format(self.path, EXECUTABLE_KEY))

        self.executable = execval

    """
    Fills out data for a JavaRuntimeFile of type directory
    """
    def read_type_directory(self, fdata):
        # Nothing to do
        pass

    """
    Fills out data for a JavaRuntimeFile of type link
    """
    def read_type_link(self, fdata):
        target = fdata.get(TARGET_KEY)

        if target == None:
            raise KeyError("JavaRuntimeFile with type link, path {}, has no target; key {} is absent from runtime manifest JSON.".format(self.path, TARGET_KEY))
        if not validity.is_nonempty_str(target):
            raise ValueError("JavaRuntimeFile with type link, path {}, has an invalid target '{}'; it should be a nonempty string.".format(self.path, target))

        self.target = target
    
    """
    Downloads and sets up the file in question.
    The main task is to download the DownloadFile instance which
    is created inside this class, but some files also need to be
    marked as executable, which this method will do.
    Returns nothing. Throws exceptions if something goes wrong.
    """
    def install(self):
        if self.type == self.TYPE_FILE:
            self.downloadfile.download()
            if self.executable:
                os.chmod(self.path, EXEC_MODE)
        elif self.type == self.TYPE_DIRECTORY:
            pass
        elif self.type == self.TYPE_LINK:
            os.symlink(self.target, self.path)
        else:
            raise ValueError("JavaRuntimeFile with path {} had unrecognised type '{}'. Recognised types are {}".format(self.path, self.type, self.FILETYPES))


# Class for downloading Java runtimes to use in
# launching Minecraft.

class JavaRuntime:

    """
    Accepts a Java runtime name.
    """
    def __init__(self, runtime):

        if not validity.is_valid_java_runtime(runtime):
            raise ValueError("Must provide valid Java Runtime name to JavaRuntime constructor. Was given {}".format(runtime))
        
        self.name = runtime
        self.game_dir = utils.get_minecraft_path()
        self.runtime_dir = self.get_runtime_dir()
        self.runtime_files = []

        self.download_runtime_manifest()
        self.read_runtime_manifest()
        self.delete_runtime_manifest()

    """
    Returns a string: the path to the jre manifest file
    which tells us how to download the manifests for
    different java runtimes.
    Usually of the form
    /home/<username>/.minecraft/versions/jre_manifest.json
    """
    def get_jre_manifest(self):
        return os.path.join(self.game_dir, "versions", "jre_manifest.json")

    """
    Returns a boolean. True if the jre manifest file exists; False if it
    doesn't.
    """
    def jre_manifest_exists(self):
        return validity.is_valid_file(self.get_jre_manifest())

    """
    Returns the location where all runtimes go.
    This is usually /home/<username>/.minecraft/runtime
    """
    def get_base_runtime_dir(self):
        return os.path.join(self.game_dir, "runtime")

    """
    Returns the directory where the data and files for the runtime
    represented by this specific instance of the JavaRuntime class will go.
    This is the root directory for everything the runtime's manifest tells
    you to download.
    Usually of the form
    /home/<username>/.minecraft/runtime/<runtime-name>/<os-name>/<runtime-name>
    """
    def get_runtime_dir(self):
        return os.path.join(self.get_base_runtime_dir(), self.name, DESIRED_OS, self.name)

    """
    Returns a path of the form
    /home/<username>/.minecraft/runtime/<runtime-name>/<os-name>/manifest.json
    This is where we'll put the runtime's manifest file while downloading everything.
    We'll delete it when finished.
    This path is totally custom to the Nydus Launcher; the Minecraft launcher seems
    not to save the runtime manifest anywhere as a file.
    """
    def get_runtime_manifest_path(self):
        return os.path.join(self.get_base_runtime_dir(), self.name, DESIRED_OS, "manifest.json")

    """
    Uses get_runtime_manifest to download the manifest file
    to where we will read it from and use it.
    """
    def download_runtime_manifest(self):
        jre_fname = self.get_jre_manifest()
        with open(jre_fname, "r") as f:
            try:
                jre_json = json.load(f)
            except JSONDecodeError as e:
                raise ValueError("Failed to parse json in {} at line {} col {} char {}"\
                    .format(jre_fname, e.lineno, e.colno, e.pos))

        df = self.get_runtime_manifest(jre_json)
        if isinstance(df, DownloadFile):
            df.download()
        else:
            raise ValueError("Could not extract enough information about runtime {} on platform {} from file {} to download the manifest."\
                .format(self.name, DESIRED_OS, jre_fname))
    
    """
    jre_json: dictionary, the JSON from the jre_manifest json file.
    Returns a DownloadFile containing the information to download
    the manifest for the current java runtime.
    Information is taken from jre_manifest.json.
    The path to which the file should be downloaded will be set as
    ~/.minecraft/runtime/<runtime-name>
    because it isn't normally cached, so there's no correct place
    to put it.
    Raises exceptions or returns None if the desired runtime can't be found.
    """
    def get_runtime_manifest(self, jre_json):

        assert isinstance(jre_json, dict), "Must pass a dictionary containing JSON to JavaRuntime.get_runtime_manifest. Instead, got {}".format(type(jre_json))

        jre_content = jre_json.get(MANIFEST_KEY)
        if jre_content == None:
            raise KeyError("Jre manifest file {} contained no key {}; could not get manifest for runtime {}".format(jre_fname, MANIFEST_KEY, self.name))
        if not isinstance(jre_content, dict):
            raise TypeError("Contents of key {} in file {} was not a dict; could not get manifest for runtime {}".format(MANIFEST_KEY, jre_fname, self.name))

        os_runtimes = jre_content.get(DESIRED_OS)

        if os_runtimes == None:
            raise KeyError("Jre manifest file {} contained no runtimes for desired OS '{}'; could not get manifest for runtime {}".format(jre_fname, DESIRED_OS, self.name))

        if not isinstance(os_runtimes, dict):
            raise TypeError("Contents of desired OS key '{}' in file {} was not a dict; could not get manifest for runtime {}".format(DESIRED_OS, jre_fname, self.name))

        runtime_data = os_runtimes.get(self.name)

        if runtime_data == None:
            raise KeyError("Jre manifest file {} contained no runtime named '{}' for desired OS '{}'; could not proceed.".format(jre_fname, self.name, DESIRED_OS))

        if not isinstance(runtime_data, dict):
            raise TypeError("Contents of key '{}' for OS '{}' in file {} was not a dict; could not get runtime information.".format(self.name, DESIRED_OS, jre_fname))

        runtime_manifest = runtime_data.get(MANIFEST_KEY)

        if runtime_manifest == None:
            raise KeyError("Jre manifest file {} contained no key {} under {}; could not get manifest for runtime {}".format(jre_fname, MANIFEST_KEY, self.name, self.name))
        if not isinstance(runtime_manifest, dict):
            raise TypeError("Contents of key {} under {} in file {} was not a dict; could not get manifest for runtime {}".format(MANIFEST_KEY, self.name, jre_fname, self.name))

        sha1 = runtime_manifest.get(SHA1_KEY)
        url = runtime_manifest.get(URL_KEY)
        if url == None or sha1 == None:
            return

        fpath = self.get_runtime_manifest_path()
        fname = os.path.basename(fpath)
        path = os.path.dirname(fpath)
        
        df = DownloadFile(url, sha1, name=fname, path=path)
        return df
    
    """
    Intended to be called after download_runtime_manifest; reads the manifest
    for this Java runtime and learns everything needed from it.
    """
    def read_runtime_manifest(self):
        manifest = self.get_runtime_manifest_path()

        with open(manifest, "r") as f:
            try:
                manifest_json = json.load(f)
            except JSONDecodeError as e:
                raise ValueError("Failed to parse json in {} at line {} col {} char {}"\
                    .format(manifest, e.lineno, e.colno, e.pos))

        files_dict = manifest_json.get(FILES_KEY)

        if files_dict == None:
            raise KeyError("Runtime manifest file contained no key {}; could not get files for runtime {}".format(FILES_KEY, self.name))

        if not isinstance(files_dict, dict):
            raise TypeError("Contents of key {} in manifest file was not a dictionary; could not get files for runtime {}".format(FILES_KEY, self.name))

        # The runtime manifest files dictionary is made up
        # of keys containing dictionaries. The key tells
        # you the file name (under the runtime's general directory)
        # and the dictionary tells you the rest of the information.
        for fname in files_dict:
            jrf = JavaRuntimeFile(fname, files_dict[fname], self.runtime_dir)

            if jrf != None:
                self.runtime_files.append(jrf)

    """
    Deletes the runtime manifest file; Minecraft launcher doesn't seem
    to leave it on the disk, so we won't either.
    """
    def delete_runtime_manifest(self):
        os.remove(self.get_runtime_manifest_path())

    """
    Downloads/creates all the files for this runtime, using all the info
    set up by read_runtime_manifest
    """
    def setup_runtime(self):
        for jrf in self.runtime_files:
            jrf.install()

