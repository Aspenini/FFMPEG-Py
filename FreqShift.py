import os
import sys
import subprocess
import tkinter as tk
from tkinter import simpledialog, messagebox
import ffmpeg

APP_NAME = "FreqShift"
output_formats = ["wav", "ogg", "mp3", "flac"]
converter_options = ["FFmpeg", "VGMStream"]

# Path to vgmstream
def get_script_path():
    return os.path.dirname(os.path.abspath(sys.argv[0]))

VGMS_CLI_PATH = os.path.join(get_script_path(), "vgmstream", "vgmstream-cli.exe")

def use_vgmstream(input_file, output_ext):
    base, _ = os.path.splitext(input_file)
    output_file = f"{base}.{output_ext}"
    try:
        subprocess.run(
            [VGMS_CLI_PATH, input_file, "-o", output_file],
            check=True
        )
        messagebox.showinfo(f"{APP_NAME} - VGMStream", f"Converted to: {output_file}")
    except Exception as e:
        messagebox.showerror(f"{APP_NAME} - VGMStream Error", str(e))

def use_ffmpeg(input_file, output_ext):
    base, _ = os.path.splitext(input_file)
    output_file = f"{base}.{output_ext}"
    try:
        (
            ffmpeg
            .input(input_file)
            .output(output_file)
            .run(overwrite_output=True)
        )
        messagebox.showinfo(f"{APP_NAME} - FFmpeg", f"Converted to: {output_file}")
    except Exception as e:
        messagebox.showerror(f"{APP_NAME} - FFmpeg Error", str(e))

def convert_smart(input_file):
    ext = os.path.splitext(input_file)[1].lower()

    root = tk.Tk()
    root.withdraw()

    # Ask for output format
    fmt = simpledialog.askstring(
        f"{APP_NAME} - Output Format",
        f"Convert to which format?\nOptions: {', '.join(output_formats)}"
    )
    if fmt not in output_formats:
        messagebox.showerror(f"{APP_NAME} - Invalid Format", f"'{fmt}' is not supported.")
        return

    # Ask for converter
    converter = simpledialog.askstring(
        f"{APP_NAME} - Converter",
        f"Use which converter?\nOptions: {', '.join(converter_options)}"
    )
    root.destroy()

    if converter not in converter_options:
        messagebox.showerror(f"{APP_NAME} - Invalid Converter", f"'{converter}' is not supported.")
        return

    if converter == "VGMStream":
        use_vgmstream(input_file, fmt)
    else:
        use_ffmpeg(input_file, fmt)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        tk.Tk().withdraw()
        messagebox.showerror(f"{APP_NAME} - Error", "Drag and drop a file onto this script to convert it.")
    else:
        convert_smart(sys.argv[1])
