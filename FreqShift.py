# Full updated FreqShift script with custom TEX-Stripper engine
import os
import sys
import subprocess
import tkinter as tk
from tkinter import simpledialog, messagebox
import ffmpeg

APP_NAME = "FreqShift"

# Engine-specific format lists
engine_formats = {
    "FFmpeg": ["mp3", "mp4", "wav", "ogg", "mkv", "flac", "mov", "webm", "gif"],
    "VGMStream": ["wav"],
    "TEX-Stripper": ["dds", "png"]
}

# Determine current script location
def get_script_path():
    return os.path.dirname(os.path.abspath(sys.argv[0]))

VGMS_CLI_PATH = os.path.join(get_script_path(), "vgmstream", "vgmstream-cli.exe")

def use_vgmstream(input_file, output_ext):
    base, _ = os.path.splitext(input_file)
    output_file = f"{base}.{output_ext}"
    try:
        subprocess.run([VGMS_CLI_PATH, input_file, "-o", output_file], check=True)
        messagebox.showinfo(f"{APP_NAME} - VGMStream", f"Converted to: {output_file}")
    except Exception as e:
        messagebox.showerror(f"{APP_NAME} - VGMStream Error", str(e))

def use_ffmpeg(input_file, output_ext):
    base, _ = os.path.splitext(input_file)
    output_file = f"{base}.{output_ext}"
    try:
        ffmpeg.input(input_file).output(output_file).run(overwrite_output=True)
        messagebox.showinfo(f"{APP_NAME} - FFmpeg", f"Converted to: {output_file}")
    except Exception as e:
        messagebox.showerror(f"{APP_NAME} - FFmpeg Error", str(e))

def use_tex_stripper(input_file, output_ext):
    base, _ = os.path.splitext(input_file)
    output_path = f"{base}.{output_ext}"

    try:
        with open(input_file, "rb") as f:
            tex_data = f.read()

        if tex_data[:3] != b'DDS':
            raise ValueError("Not a valid embedded DDS file.")

        dds_path = f"{base}.dds"
        with open(dds_path, "wb") as dds_out:
            dds_out.write(tex_data)

        if output_ext == "dds":
            messagebox.showinfo(f"{APP_NAME} - TEX Extract", f"Extracted to: {dds_path}")
        elif output_ext == "png":
            from PIL import Image
            import io
            try:
                img = Image.open(dds_path)
                img.save(output_path)
                messagebox.showinfo(f"{APP_NAME} - TEX Convert", f"Saved PNG to: {output_path}")
            except Exception as e:
                raise RuntimeError(f"Could not convert DDS to PNG: {e}")

    except Exception as e:
        messagebox.showerror(f"{APP_NAME} - TEX-Stripper Error", str(e))

def convert_smart(input_file):
    root = tk.Tk()
    root.withdraw()

    engine = simpledialog.askstring(f"{APP_NAME} - Choose Engine", f"Which engine?\nOptions: {', '.join(engine_formats)}")
    if engine not in engine_formats:
        messagebox.showerror(f"{APP_NAME} - Error", f"Invalid engine: {engine}")
        return

    formats = engine_formats[engine]
    fmt = simpledialog.askstring(f"{APP_NAME} - Output Format", f"Convert to which format?\nOptions: {', '.join(formats)}")
    root.destroy()

    if fmt not in formats:
        messagebox.showerror(f"{APP_NAME} - Error", f"Format '{fmt}' is not valid for {engine}")
        return

    if engine == "VGMStream":
        use_vgmstream(input_file, fmt)
    elif engine == "FFmpeg":
        use_ffmpeg(input_file, fmt)
    elif engine == "TEX-Stripper":
        use_tex_stripper(input_file, fmt)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        tk.Tk().withdraw()
        messagebox.showerror(f"{APP_NAME} - Error", "Drag and drop a file onto this script.")
    else:
        convert_smart(sys.argv[1])
