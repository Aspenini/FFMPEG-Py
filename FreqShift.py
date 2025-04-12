# Updated FreqShift script logic with engine first, then output format per engine

import os
import sys
import subprocess
import tkinter as tk
from tkinter import simpledialog, messagebox
import ffmpeg

APP_NAME = "FreqShift"

# Format lists per engine
ffmpeg_formats = ["mp3", "mp4", "wav", "ogg", "mkv", "flac", "mov", "webm", "gif"]
vgmstream_formats = ["wav"]  # safest bet

converter_options = {
    "FFmpeg": ffmpeg_formats,
    "VGMStream": vgmstream_formats
}

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

    # Ask for engine first
    engine = simpledialog.askstring(
        f"{APP_NAME} - Choose Engine",
        f"Which engine do you want to use?\nOptions: {', '.join(converter_options.keys())}"
    )
    if engine not in converter_options:
        messagebox.showerror(f"{APP_NAME} - Error", f"Invalid engine: {engine}")
        return

    # Show output formats valid for selected engine
    valid_formats = converter_options[engine]
    fmt = simpledialog.askstring(
        f"{APP_NAME} - Output Format",
        f"Convert to which format using {engine}?\nOptions: {', '.join(valid_formats)}"
    )
    root.destroy()

    if fmt not in valid_formats:
        messagebox.showerror(f"{APP_NAME} - Error", f"Format '{fmt}' not supported by {engine}.")
        return

    if engine == "VGMStream":
        use_vgmstream(input_file, fmt)
    else:
        use_ffmpeg(input_file, fmt)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        tk.Tk().withdraw()
        messagebox.showerror(f"{APP_NAME} - Error", "Drag and drop a file onto this script to convert it.")
    else:
        convert_smart(sys.argv[1])
