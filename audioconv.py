import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import soundfile as sf


def load_audio(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    info = sf.info(path)
    data, sr = sf.read(path, dtype="float32", always_2d=True)  # [S, C]
    subtype = info.subtype or "PCM_16"
    return data, sr, data.shape[1], subtype


def make_linear_window(clip_len: int, overlap_len: int) -> np.ndarray:
    """
    Linear fade-in/sustain/fade-out of length clip_len.
    overlap_len is the crossfade length at both ends.
    """
    clip_len = max(1, int(clip_len))
    overlap_len = max(0, int(overlap_len))
    if overlap_len == 0:
        return np.ones(clip_len, dtype=np.float32)

    fade = np.linspace(0.0, 1.0, overlap_len, dtype=np.float32)
    sustain_len = max(0, clip_len - 2 * overlap_len)
    sustain = np.ones(sustain_len, dtype=np.float32)
    win = np.concatenate([fade, sustain, fade[::-1]]).astype(np.float32)

    # Pad/trim to exact length (defensive)
    if win.shape[0] < clip_len:
        win = np.pad(win, (0, clip_len - win.shape[0]), constant_values=1.0)
    elif win.shape[0] > clip_len:
        win = win[:clip_len]
    return win


def make_hann_window(clip_len: int) -> np.ndarray:
    """
    Cosine (Hann) window across the entire snippet.
    Works well with ~50% overlap, but we allow user-chosen overlap.
    """
    clip_len = max(1, int(clip_len))
    if clip_len == 1:
        return np.ones(1, dtype=np.float32)
    return np.hanning(clip_len).astype(np.float32)


def build_overlap_snippets(src: np.ndarray,
                           out_len: int,
                           clip_len: int,
                           overlap_len: int,
                           window_type: str,
                           rng: np.random.Generator) -> np.ndarray:
    """
    Overlap-Add of random snippets with crossfade.
    src: [S, C] float32 in [-1,1]
    Returns out: [out_len, C]
    """
    S, C = src.shape
    clip_len = max(1, int(clip_len))
    overlap_len = max(0, int(overlap_len))
    if clip_len > S:
        raise ValueError("Snippet length cannot exceed source length.")

    # Validation per window type
    if window_type == "Linear crossfade":
        if 2 * overlap_len >= clip_len:
            raise ValueError("For Linear, Overlap must be less than half the snippet size.")
        win = make_linear_window(clip_len, overlap_len)
    else:  # Hann (cosine)
        if overlap_len >= clip_len:
            raise ValueError("For Hann, Overlap must be less than the snippet size.")
        win = make_hann_window(clip_len)

    hop = clip_len - overlap_len
    if hop <= 0:
        # extreme case: force at least 1-sample hop
        hop = 1
        overlap_len = clip_len - 1

    win = win[:, None]  # [clip_len, 1] for broadcasting
    out = np.zeros((out_len, C), dtype=np.float32)

    max_start = S - clip_len
    pos = 0
    while pos < out_len:
        start = int(rng.integers(0, max_start + 1)) if max_start > 0 else 0
        this_chunk = min(clip_len, out_len - pos)

        src_chunk = src[start:start + this_chunk, :]                 # [this_chunk, C]
        if this_chunk == clip_len:
            win_chunk = win
        else:
            win_chunk = win[:this_chunk, :]

        out[pos:pos + this_chunk, :] += src_chunk * win_chunk
        pos += hop

    return out


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Conv tool by Nate Wilcox")
        self.geometry("720x590")
        self.minsize(700, 560)

        # Vars
        self.src_path = tk.StringVar()
        self.dst_path = tk.StringVar()
        self.clip_ms = tk.StringVar(value="250")          # snippet size
        self.overlap_ms = tk.StringVar(value="100")       # crossfade/overlap
        self.out_sec = tk.StringVar(value="30")           # output length
        self.gain = tk.StringVar(value="1.0")             # gain
        self.format_choice = tk.StringVar(value="WAV")    # WAV/AIFF
        self.window_choice = tk.StringVar(value="Linear crossfade")  # Linear/Hann

        # Repeatability controls (user-friendly)
        self.repeatable = tk.BooleanVar(value=False)
        self.repeat_code = tk.StringVar(value="12345")    # optional number

        self.src_info = tk.StringVar(value="No file loaded.")
        self.status = tk.StringVar(value="Idle.")
        self.progress_val = tk.DoubleVar(value=0.0)

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # Source
        frm_src = ttk.LabelFrame(self, text="Source file")
        frm_src.pack(fill="x", **pad)
        ttk.Entry(frm_src, textvariable=self.src_path).pack(side="left", fill="x", expand=True, padx=(10, 6), pady=10)
        ttk.Button(frm_src, text="Browse…", command=self.choose_src).pack(side="left", padx=(0, 10), pady=10)

        ttk.Label(self, textvariable=self.src_info).pack(fill="x", **pad)

        # Parameters
        frm_params = ttk.LabelFrame(self, text="Parameters")
        frm_params.pack(fill="x", **pad)
        grid = ttk.Frame(frm_params)
        grid.pack(fill="x", padx=10, pady=10)

        r = 0
        ttk.Label(grid, text="Snippet size (ms):").grid(row=r, column=0, sticky="e")
        ttk.Entry(grid, width=10, textvariable=self.clip_ms).grid(row=r, column=1, sticky="w", padx=(6, 16))

        ttk.Label(grid, text="Overlap / Crossfade (ms):").grid(row=r, column=2, sticky="e")
        ttk.Entry(grid, width=10, textvariable=self.overlap_ms).grid(row=r, column=3, sticky="w", padx=(6, 16))

        ttk.Label(grid, text="Output length (sec):").grid(row=r, column=4, sticky="e")
        ttk.Entry(grid, width=10, textvariable=self.out_sec).grid(row=r, column=5, sticky="w", padx=(6, 16))

        r += 1
        ttk.Label(grid, text="Gain (0.05–2.0):").grid(row=r, column=0, sticky="e", pady=(8, 0))
        ttk.Entry(grid, width=10, textvariable=self.gain).grid(row=r, column=1, sticky="w", padx=(6, 16), pady=(8, 0))

        ttk.Label(grid, text="Save format:").grid(row=r, column=2, sticky="e", pady=(8, 0))
        ttk.Combobox(grid, width=10, state="readonly",
                     textvariable=self.format_choice, values=("WAV", "AIFF")).grid(row=r, column=3, sticky="w", padx=(6, 16), pady=(8, 0))

        ttk.Label(grid, text="Window type:").grid(row=r, column=4, sticky="e", pady=(8, 0))
        ttk.Combobox(grid, width=16, state="readonly",
                     textvariable=self.window_choice, values=("Linear crossfade", "Hann (cosine)")).grid(row=r, column=5, sticky="w", padx=(6, 0), pady=(8, 0))

        # Repeatability
        frm_rep = ttk.LabelFrame(self, text="Repeatable results (optional)")
        frm_rep.pack(fill="x", **pad)
        rep_row = ttk.Frame(frm_rep)
        rep_row.pack(fill="x", padx=10, pady=10)
        chk = ttk.Checkbutton(rep_row, text="Make results repeatable", variable=self.repeatable, command=self._toggle_repeat_code)
        chk.pack(side="left")
        ttk.Label(rep_row, text="Repeat code:").pack(side="left", padx=(16, 6))
        self.repeat_entry = ttk.Entry(rep_row, width=14, textvariable=self.repeat_code, state="disabled")
        self.repeat_entry.pack(side="left")

        # Destination
        frm_dst = ttk.LabelFrame(self, text="Destination file")
        frm_dst.pack(fill="x", **pad)
        ttk.Entry(frm_dst, textvariable=self.dst_path).pack(side="left", fill="x", expand=True, padx=(10, 6), pady=10)
        ttk.Button(frm_dst, text="Browse…", command=self.choose_dst).pack(side="left", padx=(0, 10), pady=10)

        # Actions
        frm_actions = ttk.Frame(self)
        frm_actions.pack(fill="x", **pad)
        self.btn_run = ttk.Button(frm_actions, text="Build Output", command=self.run_clicked)
        self.btn_run.pack(side="left", padx=(10, 6))
        self.pbar = ttk.Progressbar(frm_actions, variable=self.progress_val, maximum=100)
        self.pbar.pack(side="left", fill="x", expand=True, padx=(6, 10))

        ttk.Label(self, textvariable=self.status).pack(fill="x", **pad)

        footer = ttk.Label(
            self,
            anchor="center",
            text="Overlap-add random snippets • Linear / Hann windows • WAV/AIFF via libsndfile",
        )
        footer.pack(fill="x", pady=(8, 12))

    # ---- UI callbacks ----
    def _toggle_repeat_code(self):
        self.repeat_entry.config(state=("normal" if self.repeatable.get() else "disabled"))

    def choose_src(self):
        path = filedialog.askopenfilename(
            title="Choose source audio",
            filetypes=[("Audio", "*.wav *.aiff *.aif *.aifc *.AIFF *.WAV"), ("All files", "*.*")]
        )
        if path:
            self.src_path.set(path)
            try:
                data, sr, ch, subtype = load_audio(path)
                dur = data.shape[0] / sr
                self.src_info.set(f"{os.path.basename(path)} — {sr} Hz, {ch} ch, {dur:.2f} s, subtype {subtype}")
            except Exception as e:
                self.src_info.set(f"Error: {e}")

    def choose_dst(self):
        init_ext = ".wav" if self.format_choice.get().upper() == "WAV" else ".aiff"
        path = filedialog.asksaveasfilename(
            title="Save output audio",
            defaultextension=init_ext,
            filetypes=[("WAV", "*.wav"), ("AIFF", "*.aiff *.aif")]
        )
        if path:
            self.dst_path.set(path)

    def run_clicked(self):
        try:
            params = self._validate_params()
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return

        self.btn_run.config(state="disabled")
        self.status.set("Working…")
        self.progress_val.set(0)

        t = threading.Thread(target=self._worker, args=(params,))
        t.daemon = True        # keep UI responsive
        t.start()

    def _validate_params(self):
        src = self.src_path.get().strip()
        dst = self.dst_path.get().strip()
        if not src:
            raise ValueError("Please choose a source file.")
        if not os.path.isfile(src):
            raise ValueError("Source file path is not valid.")
        if not dst:
            raise ValueError("Please choose a destination path.")

        # Numbers
        try:
            clip_ms = float(self.clip_ms.get())
        except ValueError:
            raise ValueError("Snippet size must be a number (ms).")
        if clip_ms <= 0:
            raise ValueError("Snippet size must be > 0 ms.")

        try:
            overlap_ms = float(self.overlap_ms.get())
        except ValueError:
            raise ValueError("Overlap must be a number (ms).")
        if overlap_ms < 0:
            raise ValueError("Overlap must be ≥ 0 ms.")

        try:
            out_sec = float(self.out_sec.get())
        except ValueError:
            raise ValueError("Output length must be a number (sec).")
        if out_sec <= 0:
            raise ValueError("Output length must be > 0 s.")

        try:
            gain = float(self.gain.get())
        except ValueError:
            raise ValueError("Gain must be a number.")
        if not (0.05 <= gain <= 2.0):
            raise ValueError("Gain must be between 0.05 and 2.0.")

        fmt = self.format_choice.get().upper()
        if fmt not in ("WAV", "AIFF"):
            fmt = "WAV"

        window_type = self.window_choice.get()
        # Window-specific overlap rule checked later with sample units.

        # Repeatability
        seed = None
        if self.repeatable.get():
            txt = self.repeat_code.get().strip()
            if txt == "":
                raise ValueError("Enter a repeat code or untick 'Make results repeatable'.")
            try:
                seed = int(txt)
            except ValueError:
                # Friendly: derive a stable int from text
                seed = abs(hash(txt)) % (2**32)

        return {
            "src": src, "dst": dst, "clip_ms": clip_ms, "overlap_ms": overlap_ms,
            "out_sec": out_sec, "gain": gain, "format": fmt,
            "window_type": window_type, "seed": seed
        }

    def _worker(self, p):
        try:
            data, sr, ch, _ = load_audio(p["src"])
            self._set_status(f"Loaded {os.path.basename(p['src'])}: {sr} Hz, {ch} ch")

            total_samples = int(round(p["out_sec"] * sr))
            clip_len = max(1, int(round((p["clip_ms"] / 1000.0) * sr)))
            overlap_len = max(0, int(round((p["overlap_ms"] / 1000.0) * sr)))

            # Window-specific validation in samples
            if p["window_type"] == "Linear crossfade":
                if 2 * overlap_len >= clip_len:
                    raise ValueError("For Linear, Overlap must be less than half the snippet size.")
            else:  # Hann
                if overlap_len >= clip_len:
                    raise ValueError("For Hann, Overlap must be less than the snippet size.")

            # RNG
            rng = np.random.default_rng(p["seed"]) if p["seed"] is not None else np.random.default_rng()

            # Build in steps so we can update progress
            out = np.zeros((total_samples, ch), dtype=np.float32)
            hop = max(1, clip_len - overlap_len)
            max_start = data.shape[0] - clip_len
            if max_start < 0:
                raise ValueError("Snippet size is longer than the source audio.")

            # Precompute window for progress loop
            if p["window_type"] == "Linear crossfade":
                base_win = make_linear_window(clip_len, overlap_len)[:, None]
            else:
                base_win = make_hann_window(clip_len)[:, None]

            pos = 0
            last_percent = -1
            while pos < total_samples:
                start = int(rng.integers(0, max_start + 1)) if max_start > 0 else 0
                this_chunk = min(clip_len, total_samples - pos)
                src_chunk = data[start:start + this_chunk, :]
                win_chunk = base_win if this_chunk == clip_len else base_win[:this_chunk, :]
                out[pos:pos + this_chunk, :] += src_chunk * win_chunk
                pos += hop

                percent = int((pos / total_samples) * 80)
                if percent != last_percent:
                    self._set_progress(percent)
                    last_percent = percent

            # Apply gain + safety clip
            self._set_status("Applying gain…")
            out *= p["gain"]
            np.clip(out, -1.0, 1.0, out=out)
            self._set_progress(90)

            # Save
            self._set_status(f"Saving {p['format']}…")
            subtype = "PCM_16" if p["format"] == "WAV" else None
            sf.write(p["dst"], out, sr, format=p["format"], subtype=subtype)
            self._set_progress(100)
            self._set_status(f"Done: {os.path.basename(p['dst'])}")
        except Exception as e:
            self._set_status(f"Error: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.btn_run.config(state="normal")

    # thread-safe UI helpers
    def _set_status(self, text):
        def _():
            self.status.set(text)
        self.after(0, _)

    def _set_progress(self, value):
        value = max(0, min(100, value))
        def _():
            self.progress_val.set(value)
        self.after(0, _)


if __name__ == "__main__":
    App().mainloop()
