import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, simpledialog
import ffmpeg

APP_NAME = "FreqShift Auto GUI"

# Engine + output format support
engine_formats = {
    "FFmpeg": ["mp3", "mp4", "wav", "ogg", "mkv", "flac", "mov", "webm", "gif"],
    "VGMStream": ["wav"],
    "TEX-Stripper": ["dds", "png"],
    "TEX-StreamInfo": ["txt"],
    "TEX-RES-Binder": ["meta"]
}

def get_script_path():
    return os.path.dirname(os.path.abspath(sys.argv[0]))

VGMS_CLI_PATH = os.path.join(get_script_path(), "vgmstream", "vgmstream-cli.exe")

def detect_engine(input_file):
    ext = os.path.splitext(input_file)[1].lower()
    try:
        with open(input_file, "rb") as f:
            head = f.read(16)
            if ext in [".wem", ".fsb", ".bnk"]:
                return "VGMStream"
            elif ext == ".tex":
                if head.startswith(b'DDS'):
                    return "TEX-Stripper"
                elif head.startswith(b'StreamInfo'):
                    return "TEX-StreamInfo"
                elif head.startswith(b'.CCH') or head.startswith(b'\x00'):
                    return "TEX-RES-Binder"
                else:
                    return "TEX-RES-Binder"
            elif ext in [".mp4", ".mp3", ".mkv", ".wav", ".mov", ".ogg"]:
                return "FFmpeg"
            else:
                return "Unknown"
    except Exception:
        return "Unknown"

def convert_file(engine, input_file, output_ext):
    base = os.path.splitext(input_file)[0]
    output_path = f"{base}.{output_ext}"

    try:
        if engine == "FFmpeg":
            ffmpeg.input(input_file).output(output_path).run(overwrite_output=True)

        elif engine == "VGMStream":
            subprocess.run([VGMS_CLI_PATH, input_file, "-o", output_path], check=True)

        elif engine == "TEX-Stripper":
            with open(input_file, "rb") as f:
                tex_data = f.read()
            if output_ext == "dds":
                with open(output_path, "wb") as out:
                    out.write(tex_data)
            elif output_ext == "png":
                dds_path = f"{base}.dds"
                with open(dds_path, "wb") as out:
                    out.write(tex_data)
                from PIL import Image
                img = Image.open(dds_path)
                img.save(output_path)

        elif engine == "TEX-StreamInfo":
            with open(input_file, "rb") as f:
                data = f.read()
            with open(output_path, "w", encoding="utf-8") as out:
                out.write(data.decode("utf-8", errors="ignore"))

        elif engine == "TEX-RES-Binder":
            with open(output_path, "w", encoding="utf-8") as out:
                out.write("This is a RES/IMG texture binder. No direct image data available.")

        else:
            raise ValueError("Unsupported engine or format.")

        messagebox.showinfo(f"{APP_NAME} - Success", f"File converted to: {output_path}")
    except Exception as e:
        messagebox.showerror(f"{APP_NAME} - Error", str(e))

def enhanced_engine_selector(input_file):
    def run_engine(engine_name):
        engine_window.destroy()
        process_file_with_engine(engine_name)

    def auto_detect_and_run():
        engine_window.destroy()
        detected = detect_engine(input_file)
        if detected in engine_formats:
            process_file_with_engine(detected)
        else:
            messagebox.showerror(f"{APP_NAME} - Auto Detect", f"Unable to detect engine for this file.")

    def process_file_with_engine(engine):
        root = tk.Tk()
        root.withdraw()
        formats = engine_formats.get(engine, [])
        fmt = simpledialog.askstring(f"{APP_NAME} - Output Format", f"Engine: {engine}\nChoose format: {', '.join(formats)}")
        root.destroy()
        if fmt in formats:
            convert_file(engine, input_file, fmt)
        else:
            messagebox.showerror(f"{APP_NAME} - Format Error", "Invalid format selected.")

    engine_window = tk.Tk()
    engine_window.title(f"{APP_NAME} - Select Engine")
    tk.Label(engine_window, text="Select conversion engine:").pack(pady=10)

    for engine in engine_formats:
        tk.Button(engine_window, text=engine, width=30, command=lambda e=engine: run_engine(e)).pack(pady=2)

    tk.Button(engine_window, text="🔍 Auto Detect Engine", width=30, bg="lightblue", command=auto_detect_and_run).pack(pady=10)
    engine_window.mainloop()

# Run
if __name__ == "__main__":
    if len(sys.argv) < 2:
        tk.Tk().withdraw()
        messagebox.showerror(APP_NAME, "Drag and drop a file onto this script.")
    else:
        enhanced_engine_selector(sys.argv[1])
