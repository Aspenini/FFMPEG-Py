import os
import sys
import subprocess
import re
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, ttk
import ffmpeg
from PIL import Image
from io import BytesIO
from pathlib import Path

APP_NAME = "FreqShift"
VGMS_CLI_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vgmstream", "vgmstream-cli.exe")

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
        raise ValueError("Not a known fake OGG")

def extract_assets_from_res(input_file):
    with open(input_file, "rb") as f:
        data = f.read()

    base = os.path.splitext(input_file)[0]

    markers = {
        "DDS": b"DDS ",
        "BMP": b"BM",
        "TTF": b"\x00\x01\x00\x00"
    }

    for label, sig in markers.items():
        pos = data.find(sig)
        if pos != -1:
            chunk = data[pos:]
            asset_file = f"{base}_{label}.bin"
            with open(asset_file, "wb") as out:
                out.write(chunk)

            # Try to convert to PNG or validate
            if label == "DDS":
                try:
                    image = Image.open(asset_file)
                    image.load()
                    image.save(f"{base}_{label}.png", "PNG")
                except Exception:
                    pass
            elif label == "BMP":
                try:
                    img = Image.open(BytesIO(chunk))
                    img.load()
                    img.save(f"{base}_{label}.png", "PNG")
                except Exception:
                    pass
            elif label == "TTF":
                pass  # Saved raw for external validation

    # Extract readable ASCII strings
    strings = []
    buffer = b""
    for byte in data:
        if 32 <= byte < 127:
            buffer += bytes([byte])
        else:
            if len(buffer) >= 4:
                strings.append(buffer.decode("utf-8", errors="ignore"))
            buffer = b""

    meta_file = f"{base}.meta"
    with open(meta_file, "w", encoding="utf-8") as out:
        out.write("===== Extracted RES Metadata =====\n")
        for s in strings:
            out.write(s + "\n")

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
            extract_assets_from_res(input_file)
        elif engine == "OGG-FakeDecoder":
            fake_ogg_decoder(input_file, output_ext)
        else:
            raise ValueError("Unsupported engine")
        if engine != "OGG-FakeDecoder" and engine != "TEX-RES-Binder":
            messagebox.showinfo(f"{APP_NAME} - Success", f"File converted to: {output_path}")
    except Exception as e:
        messagebox.showerror(f"{APP_NAME} - Error", str(e))

# GUI MODE
def browse_files():
    global dropped_files
    filenames = filedialog.askopenfilenames(title="Select files for FreqShift")
    dropped_files = list(filenames)
    file_label.config(text=f"{len(dropped_files)} file(s) selected.")

def start_conversion():
    if not dropped_files:
        messagebox.showwarning("FreqShift", "Please select some files first.")
        return
    progress["maximum"] = len(dropped_files)
    progress["value"] = 0
    root.update_idletask()

    successes = 0
    for i, file in enumerate(dropped_files):
        engine = detect_engine(file)
        formats = engine_formats.get(engine, [])
        fmt = formats[0] if formats else "txt"
        try:
            convert_file(engine, file, fmt)
            successes += 1
        except Exception as e:
            print(f"[Error] {file}: {e}")
        progress["value"] += 1
        root.update_idletask()
    messagebox.showinfo("FreqShift", f"Converted {successes} of {len(dropped_files)} files.")
    root.destroy()

def show_gui_window():
    global root, file_label, progress, dropped_files
    dropped_files = []
    root = tk.Tk()
    root.title("FreqShift - Drop Files to Convert")
    root.geometry("400x250")
    root.resizable(False, False)
    tk.Label(root, text="Drag and drop files or click browse", font=("Arial", 12)).pack(pady=10)
    tk.Button(root, text="Browse Files", command=browse_files).pack(pady=5)
    file_label = tk.Label(root, text="No files selected.", font=("Arial", 10))
    file_label.pack(pady=10)
    tk.Button(root, text="Convert", command=start_conversion, bg="green", fg="white", width=20).pack(pady=10)
    progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=300, mode='determinate')
    progress.pack(pady=10)
    root.mainloop()

# DRAG/DROP MODE
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

# ENTRY POINT
if __name__ == "__main__":
    if "--gui" in sys.argv or len(sys.argv) < 2:
        show_gui_window()
    else:
        batch_engine_selector(sys.argv[1:])
