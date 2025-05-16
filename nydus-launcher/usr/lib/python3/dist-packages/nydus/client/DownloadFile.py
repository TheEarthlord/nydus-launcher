
from nydus.client import utils
import os
import requests
import hashlib
import hmac

"""
Class theory

This class will include all the info needed to actually download a file used in Minecraft
This includes
  * The position on the filesystem where it should go
  * The expected sha1 hash of the file
  * The url at which the file will be found

The class will also have the utilities needed to download the file.
When file download is requested, we need to
    1) Check if the file already exists
    2) If it exists, check if it has the right sha1 hash. If so, we're done -> Success
    3) If it has the wrong hash or doesn't exist, check if the path to the file's location exists
    4) If the path doesn't exist, make it
    5) Download the file from the interwebs and place it in the right spot.
    6) Check the newly downloaded file has the right hash. If so, we're done -> Success

Possible (unrecoverable) error cases:
    * existing file is missing/wrong hash and
        - path to file's location can't be created
        - url doesn't exist
        - connection gets interrupted
        - location to write the file is unwritable
        - file downloads fine but has the wrong hash

Is there any reason to delay downloading the file?
Should the class download the file as soon as it is instantiated?

TODO everything other than the download, create_path, and verify_file_hash
functions are easy to write unit tests for and should be tested
"""

DIR_MODE = 0o775
FILE_MODE = 0o664
MAX_MASK = 0o777
DIR_MASK = MAX_MASK - DIR_MODE

# Downloaded files usually appear inside this directory under .minecraft
MC_DOWNLOAD_DIR = "libraries"

class DownloadFile:

    """
    url: string, conforming to utils.is_download_url
    sha1: string, a sha1 hash of the file against which the file will be
        validated
    name: string, the filename which will be downloaded
    path: string, the path to where the file will be placed (not including
        the filename itself). Path need not exist but must be absolute.
    If path and name are not provided, they will be inferred from the path
        part of the url (by prepending the user's home and minecraft directories)
    """
    def __init__(self, url, sha1, name="", path=""):


        assert utils.is_download_url(url), "url provided to DownloadFile is not a valid file downloading url: {}".format(url)
        self.url = url

        assert utils.is_sha1(sha1), "file hash provided to DownloadFile does not look like a sha1 digest: {}".format(sha1)
        self.sha1 = sha1

        if self.is_download_filepath(path):
            self.path = path
        else:
            self.infer_path()

        if self.is_download_filename(name):
            self.name = name
        else:
            self.infer_name()

        self.fullpath = os.path.join(self.path, self.name)

    def get_url(self):
        return self.url

    def get_sha1(self):
        return self.sha1

    def get_path(self):
        return self.path
    
    def get_name(self):
        return self.name

    """
    Here a 'fullpath' is the path to the file plus the filename
    where 'path' just means the hierarchy of directories containing the file
    without including the filename
    """
    def get_fullpath(self):
        return self.fullpath

    """
    To be a valid path for a download file to be saved under, it has to be nonempty,
    absolute, and start with the user's .minecraft folder.
    Returns True if the given path is a valid one for a download file.
    """
    def is_download_filepath(self, filepath):

        if filepath == "":
            return False

        mc_path = utils.get_minecraft_path()

        if os.path.isabs(mc_path) and filepath.startswith(mc_path):
            return True
        return False

    """
    To be a valid filename to save a download file under, it must be nonempty,
    and not contain a / since those are part of paths.
    Returns True if the given name is valid for a download file.
    """
    def is_download_filename(self, filename):

        if filename == "":
            return False

        idx = filename.find("/")
        if idx == -1:
            return True
        return False

    """
    Only if the path at which the file should be stored is unknown, infer it
    using the path section of the download URL.
    The infered path is
    {user's minecraft path}/{MC_DOWNLOAD_DIR}/{path section of url}
    MC_DOWNLOAD_DIR is used because most downloaded files appear under somewhere inside
    the minecraft directory, but this position is not included in the url's path
    """
    def infer_path(self):
        url_path = utils.get_url_path(self.get_url())
        url_path = os.path.dirname(url_path)

        mc_path = utils.get_minecraft_path()

        final_path = os.path.join(mc_path, MC_DOWNLOAD_DIR, url_path)

        self.path = final_path
    
    """
    Only if the name of the file is unknown, infer it using the path section
    of the download URL
    """
    def infer_name(self):
        url_path = utils.get_url_path(self.get_url())
        self.name = os.path.basename(url_path)

    """
    Verify that the sha1 hash of the file self.name under self.path
    is the same as self.sha1
    Returns True if so, False if not
    """
    def verify_file_hash(self):
        with open(self.get_fullpath(), "rb") as f:
            digest = hashlib.file_digest(f, "sha1")

        hexhash = digest.hexdigest()

        # compare_digest requires the same type from both objects, but
        # .hexdigest() returns a string, so we have that
        return hmac.compare_digest(self.get_sha1(), hexhash)
    
    """
    Creates the path under which the downloaded file will be stored
    Returns nothing; failure raises errors
    """
    def create_path(self):
        mc_path = utils.get_minecraft_path()
        assert os.path.isdir(mc_path), "User's Minecraft directory does not exist: {}".format(mc_path)

        if os.path.isdir(self.get_path()):
            return

        # makedirs creates intermediate directories according to the umask
        # so we have to set the mode we want on the intermediate directories
        # then restore the original setting after
        old_umask = os.umask(DIR_MASK)
        os.makedirs(self.get_path(), DIR_MODE)
        os.umask(old_umask)

    """
    Master download function
    Returns nothing; when this is completes, the file has either been
    downloaded into the indicated location, or an error has been raised.
    1 - Check for file existence (and hash correctness if existing)
    2 - Check for path existence and create if missing
    3 - Download file into the right spot
    4 - Check newly downloaded file has correct hash
    """
    def download(self):

        if os.path.isfile(self.get_fullpath()):
            if self.verify_file_hash():
                return

        if not os.path.isdir(self.get_path()):
            self.create_path()

        # Need to do error handling here
        response = requests.get(self.get_url(), stream=True)

        with open(self.get_fullpath(), "wb") as f:
            for data in response.iter_content():
                f.write(data)

        os.chmod(self.get_fullpath(), FILE_MODE)


        if not self.verify_file_hash():
            raise ValueError("File downloaded from {} to {} failed sha1 hash verification."\
                    .format(self.get_url(), self.get_fullpath()))
