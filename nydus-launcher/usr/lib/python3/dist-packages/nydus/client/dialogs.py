
import gi
import threading
import time

gi.require_version("Gtk", "3.0")
gi.require_version("Wnck", "3.0")

from gi.repository import Gtk
from gi.repository import Wnck
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
    quit_on_close: if True, Gtk will exit when this window is closed.
        Use for the final window in a sequence of timed ones.
    """
    def __init__(self, msg_text, timeout=10, quit_on_close=False):

        if not validity.is_nonempty_str(msg_text):
            raise ValueError("Nonempty string must be provided as Window message text. Was given '{}' of type {}".format(msg_text, type(msg_text)))

        super().__init__(text=INFO_TITLE, secondary_text=msg_text, image=None)

        if not isinstance(timeout, int) or timeout < 0:
            raise ValueError("Must be given a non-negative integer as timeout for an InfoDialog. Was given '{}' of type {}".format(timeout, type(timeout)))

        self.timeout = timeout

        if quit_on_close:
            self.connect("destroy", Gtk.main_quit)

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

        # The error message will show until dismissed, then exit Gtk
        self.connect("destroy", Gtk.main_quit)



DIAG_LOCK = threading.Lock()

# Used to track which status dialog box we're up to
# showing as we work through the process of launching Minecraft.
# This is a global modified by several threads.
# Always use the DIAG_LOCK when touching it.
dialog_idx = 0

# The list of status dialog boxes in order, displaying
# stages in launching Minecraft.
# By default a dialog box will persist until the program
# reaches a new stage and manually triggers the next one.
# You can make a box disappear automatically after a set time
# by giving it a nonzero timeout value.
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
    InfoDialog("You have reached a state where time has no meaning...", timeout=0, quit_on_close=True),
]

"""
Uses Wnck to detect whether a Minecraft window has become visible
on the screen.
version: numeric Minecraft version we expect, in string form.
    Note this is the base Minecraft version, it does not include
    any reference to any mods that may be active. For instance,
    the word 'Optifine' should not appear in this version even if
    Optifine is in use.
"""
def is_minecraft_visible(version):
    progname = "Minecraft"
    vanilla_title = "{} {}".format(progname, version)
    modded_title = "{}* {}".format(progname, version)

    screen = Wnck.Screen.get_default()
    windows = screen.get_windows()
    for window in windows:
        title = window.get_name()
        if title == vanilla_title or title == modded_title:
            return True

    return False

"""
Advances to showing the next dialog box in line, closing the current one.
If the next is to be open indefinitely, this is simple.
If the next has a specific timeout, this function starts the show_timed_dialogs
function to manage keeping windows open for the right durations.
mc_version can be passed, and should be passed if timed dialogs
will be shown, because the Minecraft version is used to detect
when Minecraft has launched and it's time to stop showing timed
dialogs.
"""
def show_next_dialog(mc_version=""):
    global dialog_idx

    with DIAG_LOCK:

        if dialog_idx > 0:
            prev_diag = DIALOGS[dialog_idx-1]
            prev_diag.close()

        curr_diag = DIALOGS[dialog_idx]

        # If the current message does not have a timeout,
        # advance as normal. If it has a timeout, start
        # the thread which proceeds through timed messages.
        if curr_diag.get_timeout() == 0:
            curr_diag.show_all()
            dialog_idx += 1
        else:
            if not is_valid_minecraft_version(mc_version):
                raise ValueError("Can only begin showing timed dialogs if we have a valid Minecraft version to detect when the Minecraft window appears. Was given version '{}'".format(mc_version))

            timed_diag_thread = threading.Thread(target=show_timed_dialogs, args=(mc_version,))
            timed_diag_thread.start()


"""
Closes all dialog boxes. Used if we're about to
shut down Gtk (Minecraft has finished opening) or
if we need to show an error dialog box.
Does not acquire the DIAG_LOCK itself, but the caller
must do this before calling close_all_dialogs.
"""
def close_all_dialogs():
    for i in range(len(DIALOGS)):
        DIALOGS[i].close()


"""
Closes all dialog boxes and ends the Gtk main loop.
"""
def end_gtk():
    with DIAG_LOCK:
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

    with DIAG_LOCK:
        # Set to max so no more info messages appear
        dialog_idx = len(DIALOGS)
        close_all_dialogs()

    win.show_all()

"""
Manages showing and removing of messages which should only
be visible for a fixed time frame.
mc_version: string, numeric part of the Minecraft version we're
    launching while all this is happening.
"""
def show_timed_dialogs(mc_version):

    global dialog_idx
    # We will enter this function directly from
    # show_next_dialog which will have detected a
    # timed message and not shown it yet.
    # So we show the next message ourselves.

    # We use a while True to make it easy to lock inside
    # the loop only when needed
    
    while True:
        with DIAG_LOCK:

            # If Gtk is no longer running, exit immediately.
            if Gtk.main_level() < 1:
                break

            # If we've exceeded the list of messages, exit immediately.
            if dialog_idx >= len(DIALOGS):
                break

            # Close previous message
            if dialog_idx > 0:
                DIALOGS[dialog_idx-1].close()

            # If Minecraft has appeared on screen, it's time to stop
            # We don't use end_gtk because it grabs DIAG_LOCK and we
            # already have it.
            if is_minecraft_visible(mc_version):

                close_all_dialogs()
                # Give the Gtk main loop an iteration to process
                # window closures.
                Gtk.main_iteration_do(False)
                Gtk.main_quit()
                break

            # Else proceed to the next message
            else:
                curr_diag = DIALOGS[dialog_idx]
                curr_diag.show_all()
                timeout = curr_diag.get_timeout()
                dialog_idx += 1

        # Outside lock so timeout sleeping will not
        # occupy the lock
        if timeout > 0:
            time.sleep(timeout)
        else:
            # if timeout <= 0, leave message indefinitely
            break

