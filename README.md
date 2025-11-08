# 🎧 Audio Randomiser (Overlap + Crossfade)

A user-friendly **audio texture generator** built with Python and Tkinter.  
It takes a source WAV/AIFF file and creates a new output by layering randomly selected snippets with smooth crossfades — perfect for generating evolving ambience, textures, or creative glitch-style soundscapes.

---

## ✨ Features

- **Supports WAV and AIFF** formats (read & write)
- **Randomised snippet reassembly**
- **Overlap + crossfade** between snippets for smooth blending
- Choose between **Linear** or **Hann (cosine)** window shapes
- Adjustable:
  - Snippet size (ms)
  - Overlap/crossfade length (ms)
  - Output length (seconds)
  - Gain
- **Repeatable output option** — enter a “Repeat Code” to recreate the same result - Randomiser seed remains static throughout
- Simple **Tkinter GUI** — no coding required
- Written in pure Python using **NumPy** and **SoundFile**

---

## 🧰 Requirements

Python 3.8 or newer.

Install dependencies:
```bash
pip install numpy soundfile
