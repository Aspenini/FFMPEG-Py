import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, simpledialog
import ffmpeg
from PIL import Image

APP_NAME = "FreqShift"

# Supported engines and their output format options
engine_formats = {
    "FFmpeg": ["mp3", "mp4", "wav", "ogg", "mkv", "flac", "mov", "webm", "gif"],
    "VGMStream": ["wav"],
    "TEX-Stripper": ["dds", "png", "wav"],
    "TEX-StreamInfo": ["txt"],
    "TEX-RES-Binder": ["meta"],
    "TEX-Script": ["txt"],
    "TEX-CharMap": ["txt"],
    "OGG-FakeDecoder": ["wav"]
}

def get_script_path():
    return os.path.dirname(os.path.abspath(sys.argv[0]))

VGMS_CLI_PATH = os.path.join(get_script_path(), "vgmstream", "vgmstream-cli.exe")

def detect_engine(input_file):
    ext = os.path.splitext(input_file)[1].lower()
    try:
        with open(input_file, "rb") as f:
            head = f.read(128)
            if ext in [".wem", ".fsb", ".bnk"]:
                return "VGMStream"
            elif ext == ".tex":
                if head.startswith(b'DDS'):
                    return "TEX-Stripper"
                elif head.startswith(b'StreamInfo'):
                    return "TEX-StreamInfo"
                elif head.startswith(b'Init();') or b'Init();' in head:
                    return "TEX-Script"
                elif b'SeamusMcFly' in head or b'Character "' in head:
                    return "TEX-CharMap"
                elif b'B0X' in head or b'HSER' in head:
                    return "TEX-RES-Binder"
                else:
                    return "TEX-RES-Binder"
            elif ext == ".ogg":
                return "OGG-FakeDecoder"
            elif ext in [".mp4", ".mp3", ".mkv", ".wav", ".mov", ".flac"]:
                return "FFmpeg"
            else:
                return "Unknown"
    except Exception:
        return "Unknown"

def fake_ogg_decoder(input_file, output_ext):
    base = os.path.splitext(input_file)[0]
    output_path = f"{base}.{output_ext}"
    try:
        with open(input_file, "rb") as f:
            data = f.read()
        if data.startswith(b'IDSP') or b'I_AM_PADDING' in data:
            audio_start = data.find(b'I_AM_PADDING') + len(b'I_AM_PADDING') if b'I_AM_PADDING' in data else 0
            raw_data = data[audio_start:]
            fake_wav = b'RIFF' + b'\x00\x00\x00\x00' + b'WAVEfmt ' + b'\x10\x00\x00\x00\x01\x00\x01\x00' + \
                       b'\x44\xAC\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data' + b'\x00\x00\x00\x00'
            wav_data = fake_wav + raw_data
            with open(output_path, "wb") as out:
                out.write(wav_data)
        else:
            raise ValueError("Not a known fake OGG type.")
    except Exception as e:
        raise RuntimeError(f"OGG-FakeDecoder Error: {e}")

def convert_file(engine, input_file, output_ext):
    base = os.path.splitext(input_file)[0]
    output_path = f"{base}.{output_ext}"
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
            img = Image.open(dds_path)
            img.save(output_path)
        elif output_ext == "wav":
            with open(output_path, "wb") as f:
                f.write(b"RIFF....WAVEfmt ")
    elif engine in ["TEX-StreamInfo", "TEX-CharMap", "TEX-Script"]:
        with open(input_file, "rb") as f:
            data = f.read()
        with open(output_path, "w", encoding="utf-8") as out:
            out.write(data.decode("utf-8", errors="ignore"))
    elif engine == "TEX-RES-Binder":
        with open(output_path, "w", encoding="utf-8") as out:
            out.write("RES/IMG binder or compressed asset. No direct image data available.")
    elif engine == "OGG-FakeDecoder":
        fake_ogg_decoder(input_file, output_ext)
    else:
        raise ValueError("Unsupported engine or format")

def batch_engine_selector(input_files):
    def run_engine(engine_name):
        engine_window.destroy()
        process_files_with_engine(engine_name)

    def auto_detect_and_run():
        engine_window.destroy()
        detected_engines = [detect_engine(f) for f in input_files]
        if len(set(detected_engines)) == 1 and detected_engines[0] in engine_formats:
            process_files_with_engine(detected_engines[0])
        else:
            messagebox.showerror(APP_NAME, "Files are not of the same or supported engine type.")

    def process_files_with_engine(engine):
        root = tk.Tk()
        root.withdraw()
        formats = engine_formats.get(engine, [])
        fmt = simpledialog.askstring(APP_NAME, f"Engine: {engine}\nChoose format: {', '.join(formats)}")
        root.destroy()
        if fmt in formats:
            successes = 0
            for f in input_files:
                try:
                    convert_file(engine, f, fmt)
                    successes += 1
                except Exception as e:
                    print(f"[Error] {f}: {e}")
            messagebox.showinfo(APP_NAME, f"Converted {successes} of {len(input_files)} files.")
        else:
            messagebox.showerror(APP_NAME, "Invalid format selected.")

    engine_window = tk.Tk()
    engine_window.title(f"{APP_NAME} - Batch Mode")
    tk.Label(engine_window, text="Choose conversion engine:").pack(pady=10)
    for engine in engine_formats:
        tk.Button(engine_window, text=engine, width=30, command=lambda e=engine: run_engine(e)).pack(pady=2)
    tk.Button(engine_window, text="🔍 Auto Detect Engine", width=30, bg="lightblue", command=auto_detect_and_run).pack(pady=10)
    engine_window.mainloop()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        tk.Tk().withdraw()
        messagebox.showerror(APP_NAME, "Drag and drop one or more files onto this script.")
    else:
        batch_engine_selector(sys.argv[1:])
