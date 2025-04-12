import os
import sys
import ffmpeg
import tkinter as tk
from tkinter import simpledialog, messagebox

# Supported output formats
output_formats = ["mp4", "mp3", "wav", "ogg", "gif", "mov", "webm", "mkv"]

def convert_file(input_path):
    # Ask user for output format
    root = tk.Tk()
    root.withdraw()
    selected_format = simpledialog.askstring(
        title="FFmpeg Converter",
        prompt=f"Convert to which format?\nOptions: {', '.join(output_formats)}"
    )
    root.destroy()

    if selected_format not in output_formats:
        messagebox.showerror("Error", "Unsupported or invalid format selected.")
        return

    base, _ = os.path.splitext(input_path)
    output_path = f"{base}.{selected_format}"

    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path)
            .run(overwrite_output=True)
        )
        messagebox.showinfo("Success", f"Converted to: {output_path}")
    except ffmpeg.Error as e:
        messagebox.showerror("Conversion Failed", f"FFmpeg error:\n{e.stderr.decode()}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        tk.Tk().withdraw()
        messagebox.showerror("No File", "Drag and drop a file onto this app to convert it.")
    else:
        convert_file(sys.argv[1])
