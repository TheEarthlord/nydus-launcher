
import gi
import threading
import time

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from nydus.common import validity

INFO_TITLE = "Nydus Launcher"
ERROR_TITLE = "Nydus Launcher Error"

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
    def __init__(self, msg_text):

        if not validity.is_nonempty_str(msg_text):
            raise ValueError("Nonempty string must be provided as Window message text. Was given '{}' of type {}".format(msg_text, type(msg_text)))

        super().__init__(text=INFO_TITLE, secondary_text=msg_text, image=None)

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



DIAG_LOCK = threading.Lock()

# Used to track which status dialog box we're up to
# showing as we work through the process of launching Minecraft.
# This is a global modified by several threads.
# Always use the DIAG_LOCK when touching it.
dialog_idx = 0

# The list of status dialog boxes in order, displaying
# stages in launching Minecraft.
# Those with timeouts of 0 will persist until the program
# reaches a new stage. The others swap out every few seconds
# to reassure the user the program is still running, should
# Minecraft take a while to appear on screen.
# Always use the DIAG_LOCK when opening or closing one of these windows.
DIALOGS = [
    InfoDialog("Requesting Minecraft credentials from server..."),
    InfoDialog("Downloading files for Minecraft..."),
    InfoDialog("Launching Minecraft..."),
]

"""
Advances to showing the next dialog box in line, closing the current one.
If the next is to be open indefinitely, this is simple.
If the next has a specific timeout, this function starts the show_timed_dialogs
function to manage keeping windows open for the right durations.
"""
def show_next_dialog():
    global dialog_idx

    with DIAG_LOCK:

        if dialog_idx > 0:
            prev_diag = DIALOGS[dialog_idx-1]
            prev_diag.close()

        curr_diag = DIALOGS[dialog_idx]
        curr_diag.show_all()

        dialog_idx += 1


"""
Closes all dialog boxes. Used if we're about to
shut down Gtk (Minecraft has finished opening) or
if we need to show an error dialog box.
"""
def close_all_dialogs():
    with DIAG_LOCK:
        for i in range(len(DIALOGS)):
            DIALOGS[i].close()


"""
Closes all dialog boxes and ends the Gtk main loop.
"""
def end_gtk():
    close_all_dialogs()
    # Give the Gtk main loop an iteration to process the window closures
    # before we quit the main loop.
    # But don't block if there's nothing to do
    Gtk.main_iteration_do(False)
    Gtk.main_quit()


"""
Displays an error dialog box and closes all others that might be open.
error_diag: string, the message to show in an error window.
"""
def show_error_dialog(error_diag):
    global dialog_idx

    win = ErrorDialog(error_diag)

    # Show error message until dismissed, then exit Gtk
    win.connect("destroy", Gtk.main_quit)

    with DIAG_LOCK:
        # Set to max so no more info messages appear
        dialog_idx = len(DIALOGS)

    close_all_dialogs()

    win.show_all()
