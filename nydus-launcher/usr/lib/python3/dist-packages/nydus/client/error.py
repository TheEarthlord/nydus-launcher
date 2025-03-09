
import tkinter as tk
from tkinter import ttk
import traceback

WINDOW_NAME = "Nydus Launcher"

# If any unrecoverable errors occur, this module reports
# the error message to the user with a graphical window.

def report_fatal_errors(msg):
    root = tk.Tk(className=WINDOW_NAME)
    frame = ttk.Frame(root, padding=10)
    frame.grid()
    ttk.Label(frame, text=msg).grid(column=0, row=0)
    root.mainloop()
