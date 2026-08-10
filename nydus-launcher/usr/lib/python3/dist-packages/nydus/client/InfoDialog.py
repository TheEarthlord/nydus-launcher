
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from nydus.common import validity

INFO_TITLE = "Nydus Launcher"

"""
Class for displaying informational messages as the Nydus Client
proceeds through the stages of launching Minecraft.
"""
class InfoDialog(Gtk.MessageDialog):

    """
    msg_text: string, the main message which will appear in the window.
    timeout: nonnegative integer, how many seconds the window should remain visible.
        If 0, the window should remain until the program advances to the next stage.
    """
    def __init__(self, msg_text, timeout=10):

        if not validity.is_nonempty_str(msg_text):
            raise ValueError("Nonempty string must be provided as Window message text. Was given '{}' of type {}".format(msg_text, type(msg_text)))

        super().__init__(text=INFO_TITLE, secondary_text=msg_text, image=None)

        if not isinstance(timeout, int) or timeout < 0:
            raise ValueError("Must be given a non-negative integer as timeout for a TimedInfoDialog. Was given '{}' of type {}".format(timeout, type(timeout)))

        self.timeout = timeout

    def get_timeout(self):
        return self.timeout

