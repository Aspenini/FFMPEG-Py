import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox, simpledialog
import ffmpeg

APP_NAME = "FreqShift"

# Supported engines and formats
engine_formats = {
    "FFmpeg": ["mp3", "mp4", "wav", "ogg", "mkv", "flac", "mov", "webm", "gif"],
    "VGMStream": ["wav"],
    "TEX-Stripper": ["dds", "png", "wav"],
    "TEX-StreamInfo": ["txt"],
    "TEX-RES-Binder": ["meta"],
    "OGG-FakeDecoder": ["wav"]
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

        # Look for signature padding block or fallback to whole file
        if data.startswith(b'IDSP') or b'I_AM_PADDING' in data:
            audio_start = data.find(b'I_AM_PADDING') + len(b'I_AM_PADDING') if b'I_AM_PADDING' in data else 0
            raw_data = data[audio_start:]

            # Create a basic fake WAV file (this is not valid audio but acts as a placeholder)
            fake_wav = b'RIFF' + b'\x00\x00\x00\x00' + b'WAVEfmt ' + b'\x10\x00\x00\x00\x01\x00\x01\x00' + \
                       b'\x44\xAC\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data' + b'\x00\x00\x00\x00'
            wav_data = fake_wav + raw_data

            with open(output_path, "wb") as out:
                out.write(wav_data)

            messagebox.showinfo(f"{APP_NAME} - Fake OGG", f"Extracted fake audio stream to: {output_path}")
        else:
            raise ValueError("File does not match known fake OGG patterns.")
    except Exception as e:
        messagebox.showerror(f"{APP_NAME} - OGG-FakeDecoder Error", str(e))

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
            elif output_ext == "wav":
                with open(output_path, "wb") as f:
                    f.write(b"RIFF....WAVEfmt ")  # minimal dummy content

        elif engine == "TEX-StreamInfo":
            with open(input_file, "rb") as f:
                data = f.read()
            with open(output_path, "w", encoding="utf-8") as out:
                out.write(data.decode("utf-8", errors="ignore"))

        elif engine == "TEX-RES-Binder":
            with open(output_path, "w", encoding="utf-8") as out:
                out.write("This is a RES/IMG texture binder. No direct image data available.")

        elif engine == "OGG-FakeDecoder":
            fake_ogg_decoder(input_file, output_ext)
            return  # skip generic success message

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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        tk.Tk().withdraw()
        messagebox.showerror(APP_NAME, "Drag and drop a file onto this script.")
    else:
        enhanced_engine_selector(sys.argv[1])
