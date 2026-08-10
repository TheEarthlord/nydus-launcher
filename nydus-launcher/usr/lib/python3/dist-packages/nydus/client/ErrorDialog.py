
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from nydus.common import validity

ERROR_TITLE = "Nydus Launcher Error"

"""
Class for displaying error messages if the Nydus Client
runs into an exception or error which it can't handle.
"""
class ErrorDialog(Gtk.MessageDialog):

    """
    msg_text: string, the main message which will appear in the window.
    """
    def __init__(self, msg_text):

        if not validity.is_nonempty_str(msg_text):
            raise ValueError("Nonemptystring must be provided as Window message text. Was given '{}' of type {}".format(msg_text, type(msg_text)))

        super().__init__(text=ERROR_TITLE, secondary_text=msg_text, image=None)
