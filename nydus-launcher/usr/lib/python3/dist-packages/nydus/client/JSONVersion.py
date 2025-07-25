
import json

# Class for storing all the information contained
# in a particular JSON version file

# In general, fields containing None or empty string did
# not appear in the json or have not yet been processed.
# Filled fields will be strings, lists with elements, or
# something else.
# This distinction is particularly useful when processing
# inheritance.

class JSONVersion:

    """
    Accepts a dictionary, the result of parsing a JSON version file,
    and extracts all the information about that version.
    Note this class does not process inheritance. It will find if this version inherits from another,
    but will not read the ancestor version's file and add that data to this instance of its own accord.
    """

    def __init__(self, verjson):

        if not isinstance(dict, verjson):
            raise TypeError("Must be given a dictionary of JSON data to instantiate JSONVersion")

        # Core fields
        self.game_args = []
        self.jvm_args = []

        # Need to rethink details of how this is stored
        self.asset_index = None

        self.id = None

        # Need to think carefully about details of how this is stored
        self.java_runtime = None

        self.jars = []

        # Need to think carefully about how this is stored
        self.logging = None
        self.main_class = None
        self.type = None
        self.inherits_from = None

        self.read_json(verjson)


    """
    version: string, Minecraft version validated by common.validity
    Returns a JSONVersion instance for the corresponding Minecraft version.
    Works by parsing the version file then calling the JSONVersion constructor.
    """
    def from_version(version):

        if not validity.is_valid_minecraft_version(version):
            raise ValueError("Must provide valid Minecraft version to JSONVersion.from_version. Was given {}".format(version))
        
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
