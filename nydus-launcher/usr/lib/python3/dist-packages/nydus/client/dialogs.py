
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
    def __init__(self, msg_text, timeout=10):

        if not validity.is_nonempty_str(msg_text):
            raise ValueError("Nonempty string must be provided as Window message text. Was given '{}' of type {}".format(msg_text, type(msg_text)))

        super().__init__(text=INFO_TITLE, secondary_text=msg_text, image=None)

        if not isinstance(timeout, int) or timeout < 0:
            raise ValueError("Must be given a non-negative integer as timeout for a TimedInfoDialog. Was given '{}' of type {}".format(timeout, type(timeout)))

        self.timeout = timeout

    def get_timeout(self):
        return self.timeout


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
    InfoDialog("Requesting Minecraft credentials from server...", timeout=0),
    InfoDialog("Downloading files for Minecraft...", timeout=0),
    InfoDialog("Launching Minecraft..."),
    InfoDialog("Waiting for the grass to grow..."),
    InfoDialog("Spreading lava..."),
    InfoDialog("Making contact with the mothership..."),
    InfoDialog("Eroding a cliff-face..."),
    InfoDialog("The seconds are ticking by..."),
    InfoDialog("Circumnavigating the globe..."),
    InfoDialog("Crossing the desert on foot..."),
    InfoDialog("Journeying to the centre of the earth..."),
    InfoDialog("Watching trees grow..."),
    InfoDialog("Waiting for the sermon to be over..."),
    InfoDialog("Singing another chorus..."),
    InfoDialog("Following Pluto's orbit..."),
    InfoDialog("Stepping out of the time machine..."),
    InfoDialog("The elves are fading away..."),
    InfoDialog("Atlantis rises from the deeps..."),
    InfoDialog("Watching the years slip by..."),
    InfoDialog("Imminently expecting Jesus to return..."),
    InfoDialog("You have reached a state where time has no meaning...", timeout=0),
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

        # If the current message does not have a specific timeout,
        # advance as normal.
        # If it has a timeout, start the thread which proceeds through
        # timed messages.
        if curr_diag.get_timeout() == 0:
            curr_diag.show_all()
            dialog_idx += 1
        else:
            timed_diag_thread = threading.Thread(target=show_timed_dialogs)
            timed_diag_thread.start()


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


"""
Called when a series of status dialog boxes with timeouts are due to be shown.
This function keeps each window open for the right time, then closes it and
moves on to the next one. Terminates if gtk shuts down, if it's time to stop
showing dialogs (communicated by dialog_idx being set out of bounds) or
if we reach a dialog box with no timeout.
"""
def show_timed_dialogs():
    
    global dialog_idx
    # We will enter this function directly from
    # show_next_message which will have detected a
    # timed message and not shown it yet.
    # So we show the next message ourselves.

    # We use a while True to make it easy to lock inside
    # the loop only when needed
    while True:

        with DIAG_LOCK:

            # If Gtk is no longer running, exit immediately.
            # The function which exited gtk will have already closed any current
            # messages.
            if Gtk.main_level() < 1:
                break

            # If we've exceeded the list of messages, exit immediately
            if dialog_idx >= len(DIALOGS):
                break

            # Else proceed to next message.
            curr_diag = DIALOGS[dialog_idx]
            curr_diag.show_all()
            if dialog_idx > 0:
                DIALOGS[dialog_idx-1].close()

            timeout = curr_diag.get_timeout()

            dialog_idx += 1


        # Outside lock so timeout sleeping will not
        # occupy the lock.
        if timeout > 0:
            time.sleep(timeout)
        else:
            # If timeout <= 0, leave message indefinitely.
            break

