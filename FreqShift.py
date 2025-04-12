import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, simpledialog
import ffmpeg

APP_NAME = "FreqShift GUI"
engines = ["FFmpeg", "VGMStream", "TEX-Stripper"]
engine_formats = {
    "FFmpeg": ["mp3", "mp4", "wav", "ogg", "mkv", "flac", "mov", "webm", "gif"],
    "VGMStream": ["wav"],
    "TEX-Stripper": ["dds", "png"]
}

def get_script_path():
    return os.path.dirname(os.path.abspath(sys.argv[0]))

VGMS_CLI_PATH = os.path.join(get_script_path(), "vgmstream", "vgmstream-cli.exe")

def use_vgmstream(input_file, output_ext):
    output_file = f"{os.path.splitext(input_file)[0]}.{output_ext}"
    try:
        subprocess.run([VGMS_CLI_PATH, input_file, "-o", output_file], check=True)
        messagebox.showinfo(f"{APP_NAME} - VGMStream", f"Converted to: {output_file}")
    except Exception as e:
        messagebox.showerror(f"{APP_NAME} - VGMStream Error", str(e))

def use_ffmpeg(input_file, output_ext):
    output_file = f"{os.path.splitext(input_file)[0]}.{output_ext}"
    try:
        ffmpeg.input(input_file).output(output_file).run(overwrite_output=True)
        messagebox.showinfo(f"{APP_NAME} - FFmpeg", f"Converted to: {output_file}")
    except Exception as e:
        messagebox.showerror(f"{APP_NAME} - FFmpeg Error", str(e))

def use_tex_stripper(input_file, output_ext):
    base = os.path.splitext(input_file)[0]
    dds_path = f"{base}.dds"
    try:
        with open(input_file, "rb") as f:
            tex_data = f.read()
        if tex_data[:3] != b'DDS':
            raise ValueError("Not a valid embedded DDS file.")
        with open(dds_path, "wb") as dds_out:
            dds_out.write(tex_data)
        if output_ext == "dds":
            messagebox.showinfo(f"{APP_NAME} - TEX Extract", f"Extracted: {dds_path}")
        elif output_ext == "png":
            from PIL import Image
            img = Image.open(dds_path)
            img.save(f"{base}.png")
            messagebox.showinfo(f"{APP_NAME} - TEX Convert", f"Converted to PNG: {base}.png")
    except Exception as e:
        messagebox.showerror(f"{APP_NAME} - TEX-Stripper Error", str(e))

def process_file(engine, input_file):
    fmt = simpledialog.askstring(
        f"{APP_NAME} - Output Format",
        f"Convert to which format?\nOptions: {', '.join(engine_formats[engine])}"
    )
    if fmt not in engine_formats[engine]:
        messagebox.showerror(f"{APP_NAME} - Invalid Format", f"{fmt} is not valid for {engine}.")
        return
    if engine == "FFmpeg":
        use_ffmpeg(input_file, fmt)
    elif engine == "VGMStream":
        use_vgmstream(input_file, fmt)
    elif engine == "TEX-Stripper":
        use_tex_stripper(input_file, fmt)

def engine_selector(input_file):
    def create_engine_button(engine_name):
        return tk.Button(engine_window, text=engine_name, width=20,
                         command=lambda: [engine_window.destroy(), process_file(engine_name, input_file)])

    engine_window = tk.Tk()
    engine_window.title(f"{APP_NAME} - Choose Engine")
    tk.Label(engine_window, text="Select conversion engine:").pack(pady=10)
    for engine in engines:
        create_engine_button(engine).pack(pady=5)
    engine_window.mainloop()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        tk.Tk().withdraw()
        messagebox.showerror(f"{APP_NAME}", "Drag and drop a file onto this script.")
    else:
        engine_selector(sys.argv[1])
