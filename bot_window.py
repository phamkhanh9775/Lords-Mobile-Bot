import tkinter as tk
import threading
import time

from adb_controller import (
    ADBManager,
    ADBDevice
)

from detectTiles import scan_map
from shield_module import shield


# ==========================================================
# DEVICE LIST
# ==========================================================

selected_devices = {}


def refresh_devices():

    listbox.delete(
        0,
        tk.END
    )

    devices = ADBManager.get_devices()

    selected_devices.clear()

    for device in devices:

        size = device.size()

        label = (
            f"{device.serial}"
            f" | {size}"
        )

        listbox.insert(
            tk.END,
            label
        )

        selected_devices[
            listbox.size() - 1
        ] = device


# ==========================================================
# GET SELECTED DEVICES
# ==========================================================

def get_selected_devices():

    indexes = (
        listbox.curselection()
    )

    devices = []

    for index in indexes:

        device = selected_devices.get(
            index
        )

        if device:

            devices.append(device)

    return devices


# ==========================================================
# GATHER
# ==========================================================

def start_gathering():

    devices = (
        get_selected_devices()
    )

    if not devices:

        print(
            "Please select at least "
            "one ADB device."
        )

        return

    for device in devices:

        threading.Thread(
            target=scan_map,
            args=(device,),
            daemon=True
        ).start()

        print(
            f"Gather started: "
            f"{device.serial}"
        )


# ==========================================================
# SHIELD
# ==========================================================

def start_shielding():

    devices = (
        get_selected_devices()
    )

    if not devices:

        print(
            "Please select at least "
            "one ADB device."
        )

        return

    for device in devices:

        threading.Thread(
            target=shield,
            args=(device,),
            daemon=True
        ).start()

        print(
            f"Shield started: "
            f"{device.serial}"
        )


# ==========================================================
# ALL DEVICES
# ==========================================================

def select_all():

    listbox.selection_set(
        0,
        tk.END
    )


# ==========================================================
# EXIT
# ==========================================================

def close_bot():

    print(
        "Bot control window closed."
    )

    root.destroy()


# ==========================================================
# FLOATING WINDOW
# ==========================================================

root = tk.Tk()

root.title(
    "LordsBot ADB Control"
)

root.geometry(
    "400x360+100+100"
)

root.attributes(
    "-topmost",
    True
)

root.overrideredirect(
    True
)


# ==========================================================
# DRAG
# ==========================================================

def start_move(event):

    root.x = event.x
    root.y = event.y


def do_move(event):

    x = (
        root.winfo_x()
        +
        (
            event.x
            -
            root.x
        )
    )

    y = (
        root.winfo_y()
        +
        (
            event.y
            -
            root.y
        )
    )

    root.geometry(
        f"+{x}+{y}"
    )


# ==========================================================
# FRAME
# ==========================================================

frame = tk.Frame(
    root,
    bg="#222",
    bd=2
)

frame.pack(
    expand=True,
    fill="both"
)

frame.bind(
    "<Button-1>",
    start_move
)

frame.bind(
    "<B1-Motion>",
    do_move
)


# ==========================================================
# TITLE
# ==========================================================

title = tk.Label(
    frame,
    text="LordsBot - ADB Multi Device",
    bg="#222",
    fg="white"
)

title.pack(
    pady=5
)


# ==========================================================
# DEVICE LIST
# ==========================================================

listbox = tk.Listbox(
    frame,
    selectmode=tk.MULTIPLE,
    bg="#111",
    fg="white",
    height=8
)

listbox.pack(
    padx=10,
    pady=5,
    fill="both"
)


# ==========================================================
# BUTTONS
# ==========================================================

tk.Button(
    frame,
    text="Refresh ADB",
    command=refresh_devices
).pack(
    padx=10,
    pady=3,
    fill="x"
)


tk.Button(
    frame,
    text="Select All",
    command=select_all
).pack(
    padx=10,
    pady=3,
    fill="x"
)


tk.Button(
    frame,
    text="Gather",
    command=start_gathering,
    bg="green",
    fg="white"
).pack(
    padx=10,
    pady=3,
    fill="x"
)


tk.Button(
    frame,
    text="Apply Shield",
    command=start_shielding,
    bg="blue",
    fg="white"
).pack(
    padx=10,
    pady=3,
    fill="x"
)


tk.Button(
    frame,
    text="Exit",
    command=close_bot,
    bg="red",
    fg="white"
).pack(
    padx=10,
    pady=3,
    fill="x"
)


refresh_devices()

root.mainloop()