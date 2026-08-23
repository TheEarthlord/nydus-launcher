
import gi
import threading
import time

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from nydus.common import validity

INFO_TITLE = "Nydus Launcher"
ERROR_TITLE = "Nydus Launcher Error"

class InfoMessage:

    def __init__(self, msg_text, timeout=10):

        if not validity.is_nonempty_str(msg_text):
            raise ValueError("Nonempty string must be provided as Window message text. Was given '{}' of type {}".format(msg_text, type(msg_text)))

        if not isinstance(timeout, int):
            raise TypeError("Timeout must be an int. Was given {} of type {}".format(timeout, type(timeout)))

        if timeout < 0:
            raise ValueError("Timeout must be a non-negative integer. Was given {}".format(timeout))

        self.text = msg_text
        self.timeout = timeout

    def get_text(self):
        return self.text

    def get_timeout(self):
        return self.timeout

    def __repr__(self):
        return self.text


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

# Used to track which info message we're up to showing as we
# work through the process of launching Minecraft.
# This is a global modified by several threads. Always
# use the DIAG_LOCK when touching it.
message_idx = 0

# The list of messages in order which will be displayed by the status
# dialog box.
# Those with timeouts of 0 will persist until the program reaches a
# new stage. The others are replaced by the next message in line when
# their timeouts expire to reassure the user the program is still running,
# should Minecraft take a while to appear on screen.
MESSAGES = [
    InfoMessage("Requesting Minecraft credentials from server...", timeout=0),
    InfoMessage("Downloading files for Minecraft...", timeout=0),
    InfoMessage("Launching Minecraft..."),
    InfoMessage("Waiting for the grass to grow..."),
    InfoMessage("Spreading lava..."),
    InfoMessage("Making contact with the mothership..."),
    InfoMessage("Eroding a cliff-face..."),
    InfoMessage("The seconds are ticking by..."),
    InfoMessage("Circumnavigating the globe..."),
    InfoMessage("Crossing the desert on foot..."),
    InfoMessage("Journeying to the centre of the earth..."),
    InfoMessage("Watching trees grow..."),
    InfoMessage("Waiting for the sermon to be over..."),
    InfoMessage("Singing another chorus..."),
    InfoMessage("Following Pluto's orbit..."),
    InfoMessage("Stepping out of the time machine..."),
    InfoMessage("The elves are fading away..."),
    InfoMessage("Atlantis rises from the deeps..."),
    InfoMessage("Watching the years slip by..."),
    InfoMessage("Imminently expecting Jesus to return..."),
    InfoMessage("You have reached a state where time has no meaning...", timeout=0),
]

# The window in which info messages will be placed.
# Always use the DIAG_LOCK when modifying it.
DIALOG_WINDOW = Gtk.MessageDialog(text=INFO_TITLE, image=None)

"""
Advances to showing the next info message box in line, overwriting the current
contents of the dialog box.
If the next is to remain indefinitely, this is simple.
If the next has a timeout, this function starts the show_timed_messages
function to manage keeping windows open for the right durations.
"""
def show_next_message():
    global message_idx

    with DIAG_LOCK:

        curr_msg = MESSAGES[message_idx]

        # If the current message does not have a specific timeout,
        # advance as normal.
        # If it has a timeout, start the thread which proceeds through
        # timed messages.
        if curr_msg.get_timeout() == 0:
            DIALOG_WINDOW.props.secondary_text = curr_msg.get_text()

            if message_idx == 0:
                DIALOG_WINDOW.show_all()

            message_idx += 1

        else:
            timed_diag_thread = threading.Thread(target=show_timed_messages)
            timed_diag_thread.start()


"""
Closes the dialog box. Used if we're about to
shut down Gtk (Minecraft has finished opening) or
if we need to show an error dialog box.
"""
def close_info_dialog():
    with DIAG_LOCK:
        DIALOG_WINDOW.close()


"""
Closes the info dialog box and ends the Gtk main loop.
"""
def end_gtk():
    close_info_dialog()
    # Give the Gtk main loop an iteration to process the window closures
    # before we quit the main loop.
    # But don't block if there's nothing to do
    Gtk.main_iteration_do(False)
    Gtk.main_quit()


"""
Displays an error dialog box and closes the info one.
error_diag: string, the message to show in an error window.
"""
def show_error_dialog(error_diag):
    global message_idx

    win = ErrorDialog(error_diag)

    # Show error message until dismissed, then exit Gtk
    win.connect("destroy", Gtk.main_quit)

    with DIAG_LOCK:
        # Set to max so no more info messages appear
        message_idx = len(MESSAGES)

    close_info_dialog()

    win.show_all()


"""
Called when a series of info messages with timeouts are due to be shown.
This function keeps each message up for the right time, then moves on to the
next one. Terminates if gtk shuts down, if it's time to stop
showing messages (communicated by message_idx being set out of bounds) or
if we reach a message with no timeout.
"""
def show_timed_messages():
    
    global message_idx
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
            if message_idx >= len(MESSAGES):
                break

            # Else proceed to next message.
            curr_msg = MESSAGES[message_idx]
            DIALOG_WINDOW.props.secondary_text = curr_msg.get_text()
            if message_idx == 0:
                DIALOG_WINDOW.show_all()

            timeout = curr_msg.get_timeout()

            message_idx += 1


        # Outside lock so timeout sleeping will not
        # occupy the lock.
        if timeout > 0:
            time.sleep(timeout)
        else:
            # If timeout <= 0, leave message indefinitely.
            break

