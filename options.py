import tkinter as tk
from tkinter import ttk
from time import sleep
import subprocess
import os

window = None

def Enter(vars):
    window.destroy()
    
    params = " -configured"
    for var in vars:
        if var[1].get() == 1:
            params += f" -{var[0]}"
    
    DETACHED_PROCESS = 8
    subprocess.Popen(f'python "{os.getcwd()}/sim.py" {params}', creationflags=DETACHED_PROCESS, close_fds=True)

    sleep(0.5)
    os._exit(1)


def Window():
    global window

    window = tk.Tk()
    window.resizable(False, False)
    #popup.overrideredirect(True)

    width=300
    height=175

    window.geometry('%dx%d' % (width, height))
    window.wm_title("Startup Options")

    window.grid_columnconfigure(0, weight=1)
    window.grid_columnconfigure(1, weight=1)
    window.grid_columnconfigure(2, weight=1)
    window.grid_columnconfigure(3, weight=1)
    window.grid_columnconfigure(4, weight=1)

    intercollision = tk.IntVar()

    vars = [("intercollision", intercollision)]

    ttk.Label(window, text="", font=("Arial", 5)).grid(row=0, pady=0, column = 2)
    ttk.Label(window, text="Verlet.py", font=("Arial", 25)).grid(row=1, pady=0, column = 2)
    ttk.Label(window, text="Startup Config", font=("Arial", 15)).grid(row=2, pady=5, column = 2)

    tk.Checkbutton(window, text = "Inter-Collision (EXPERIMENTAL)", variable=intercollision).grid(row=3, pady=5, column=2)

    button = ttk.Button(window, text="Save", command=lambda: Enter(vars))
    button.grid(row=4, column=2)

    window.protocol('WM_DELETE_WINDOW', lambda: Enter(vars))
    window.mainloop()

Window()