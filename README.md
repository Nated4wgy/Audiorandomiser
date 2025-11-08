
---
# 🎧 Audio Randomiser (Overlap + Crossfade)

A user-friendly **audio texture generator** built with Python and Tkinter.  
It takes a source WAV/AIFF file and creates a new output by layering randomly selected snippets with smooth crossfades — perfect for generating evolving ambience, textures, or creative glitch-style soundscapes.

---

## ✨ Features

- **Supports WAV and AIFF** formats (read & write)
- **Randomized snippet reassembly**
- **Overlap + crossfade** between snippets for smooth blending
- Choose between **Linear** or **Hann (cosine)** window shapes
- Adjustable:
  - Snippet size (ms)
  - Overlap/crossfade length (ms)
  - Output length (seconds)
  - Gain
- **Repeatable output option** — enter a “Repeat Code” to recreate the same result
- Simple **Tkinter GUI** — no coding required
- Written in pure Python using **NumPy** and **SoundFile**

---

## 🧰 Requirements

Python 3.8 or newer.

Install dependencies:
```bash
pip install numpy soundfile
````

*(No extra drivers or compilers required; `soundfile` includes libsndfile binaries on Windows.)*

---

## 🚀 Usage

1. Run the program:

   ```bash
   audioconv.py
   ```

2. In the window:

   * **Source file:** Choose a WAV or AIFF file to use as your input.
   * **Snippet size (ms):** Length of each extracted snippet.
   * **Overlap / Crossfade (ms):** Amount each snippet overlaps with the next.
   * **Output length (sec):** How long the final mix should be.
   * **Gain:** Volume multiplier (0.05–2.0).
   * **Window type:**

     * *Linear crossfade* – quick and simple fades.
     * *Hann (cosine)* – smoother, more musical blending.
   * *(Optional)* **Repeatable results:**

     * Tick the box and enter a number in “Repeat Code” to make results identical each time.
   * **Save format:** Choose WAV or AIFF and browse for an output location.

3. Click **Build Output** and wait for the progress bar to reach 100%.

4. Your new audio file will appear at the chosen location.

---

## 🎚️ Example Settings

| Purpose             | Snippet (ms) | Overlap (ms) | Output (sec) | Gain | Window |
| ------------------- | ------------ | ------------ | ------------ | ---- | ------ |
| Ambient texture     | 250          | 120          | 60           | 1.0  | Hann   |
| Glitchy rearrange   | 80           | 20           | 30           | 1.2  | Linear |
| Drone pad generator | 400          | 200          | 120          | 0.9  | Hann   |

---

## 🧠 How It Works

The script performs a simplified *granular / overlap-add* process:

1. The input audio is divided into small random “snippets.”
2. Each snippet is blended into the output buffer using a window (Linear or Hann) to avoid pops.
3. Overlaps are added together (crossfaded) to form a seamless texture.
4. Gain is applied and the result is written to disk.

---

## 🧩 Code Overview

* **`audioconv.py`**
  Main Python file with the full Tkinter GUI, processing logic, and audio builder functions.

* **Key functions:**

  * `make_linear_window()` – builds fade-in/out crossfades
  * `make_hann_window()` – builds cosine-shaped windows
  * `build_overlap_snippets()` – core overlap-add logic
  * `App()` – GUI class handling input, validation, threading, and progress updates

---

## 🔁 Repeatable Results

If you enable *“Make results repeatable”* and provide a **Repeat Code** (any number or text),
the same random snippet sequence is generated every time you run it with that code.

This is equivalent to setting a fixed random seed.

---

## 📦 coming soon

Planned updates:

* Normalize output to –0.1 dBFS
* Multi-file source blending
* Live preview or playback
* Additional window shapes (e.g., Blackman, Tukey)
* Command-line (headless) mode

---

## 🧑‍💻 Credits

**Developer:** Nate *(Nated4wgy)*
Based on earlier C++ experiments using Adam Stark’s [AudioFile.h](https://github.com/adamstark/AudioFile) library.
Rewritten in Python for accessibility and creative experimentation.

---

## ⚙️ License

MIT License — free to use, modify, and distribute with attribution.

---

### 💡 Tip

If you hear clipping or distortion:

* Try lowering **Gain**, or
* Use a **Hann window** with higher overlap (≈ 40–60% of the snippet length).

If the output sounds too repetitive:

* Increase **Snippet size** slightly, or
* Untick *“Make results repeatable”* for a fresh variation.

```

---

Would you like me to generate a **compact “Quick-Start.txt”** version too (for inclusion alongside the script in a zip or build folder)?
```
