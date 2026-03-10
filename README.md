# 🎼 SuperQin v2

### Guqin MIDI Mapper • MIDI Toolkit • Automation Player

<img src="https://img.shields.io/badge/python-3.10+-blue">
<img src="https://img.shields.io/badge/gui-PyQt6-green">
<img src="https://img.shields.io/badge/midi-processing-purple">
<img src="https://img.shields.io/badge/platform-Windows-lightgrey">

</p>

<p align="center">
<b>Convert any MIDI song into playable Guqin music for <i>Where Winds Meet</i></b>
</p>

---

# 🎬 Overview

**SuperQin v2** is an advanced **MIDI processing and playback toolkit** designed for the **Guqin instrument in *Where Winds Meet*.**

The software allows you to take **any MIDI file** and automatically adapt it to fit within the playable range of the Guqin instrument.

It functions as a **mini MIDI DAW**, letting users:

* analyze MIDI songs
* modify tracks
* remove instruments
* transpose notes
* remove impossible chords
* remap notes into playable ranges
* export playable versions

Songs can then be exported as:

* **modified MIDI files**
* **AutoHotkey scripts** for automated playback in-game

---

# ✨ Core Features

### 🎹 MIDI → Guqin Conversion

Automatically adapts MIDI songs to the Guqin’s limited key range.

Features include:

* automatic note transposition
* octave shifting
* playable range fitting
* chord simplification

This allows **almost any MIDI file to be converted into something playable.**

---

### 🎛 MIDI Track Mixer

Each MIDI track can be individually controlled.

You can:

* enable / disable tracks
* remove percussion
* isolate melody instruments
* balance multiple tracks

Perfect for cleaning up complex MIDI files.

---

### 🎼 MIDI Editing Tools

SuperQin acts like a **lightweight MIDI editing environment**.

Editing tools include:

* note transposition
* octave shifting
* chord tolerance adjustment
* global time shifting
* note duration limiting
* track filtering

---

### 📊 MIDI Analysis

The built-in analyzer lets you inspect:

* note ranges
* track density
* playable regions
* instrument complexity

Useful when adapting difficult MIDI arrangements.

---

### 🎵 Playback Engine

Preview your modified MIDI directly in the application.

Includes:

* playback speed control
* visual note preview
* chord timing adjustments

---

### 📤 Export Options

After editing, songs can be exported as:

#### Modified MIDI

Export a cleaned or optimized MIDI file.

```id="midi"
song_optimized.mid
```

Useful for sharing playable Guqin arrangements.

---

#### AutoHotkey Script

Export a script that **automatically plays the song in-game**.

```id="ahk"
song_playback.ahk
```

When executed, the script simulates key presses to play the Guqin automatically.

---

# 🖥 Interface Overview

The interface includes several main sections:

### 🎹 Note Range Display

Shows the playable Guqin key range and highlights incoming MIDI notes.

Notes outside the range can be automatically remapped.

---

### 🎛 Track Mixer

Control which tracks are active and how they are processed.

---

### ⚙ Global Controls

Global transformations including:

* playback speed
* chord tolerance
* global octave shifting
* global semitone transposition
* time offsets

---

### 📤 Export Tools

Export your processed song as:

* optimized MIDI
* AutoHotkey playback script

---

# 🧠 How It Works

```id="pipeline"
MIDI File
    ↓
MIDI Analyzer
    ↓
Track Mixer
    ↓
Range Remapper
    ↓
Chord Simplifier
    ↓
Playback Engine
    ↓
Export
```

The system processes MIDI data and converts it into a format compatible with the Guqin's playable note range.

---

# 📦 Project Structure

```id="structure"
SuperQin/
│
├── main_v2.py
├── gui_main_v2.py
├── midi_player_v2.py
├── midi_processor_v2.py
├── track_mixer.py
├── keyboard_map.py
├── analyzer.py
├── note_widget_v2.py
└── track_time_dialog.py
```

---

# 🛠 Requirements

Install dependencies:

```id="deps"
pip install PyQt6 mido python-rtmidi keyboard numpy

SoundFont 2 File - ColomboGMGS2.sf2 Found HERE:
https://sourceforge.net/projects/colombogmgs2-sf2/
```

---

# ▶ Running the Application

Launch the GUI:

```id="run"
python main_v2.py
```

---

# 🎮 Typical Workflow

1. Load a MIDI file
2. Analyze note ranges
3. Disable unnecessary tracks
4. Auto-fit notes into the Guqin range
5. Adjust chord tolerance
6. Preview playback
7. Export MIDI or AutoHotkey script

---

# 🎵 Supported MIDI Features

* multi-track MIDI
* tempo changes
* chord handling
* note remapping
* instrument filtering

---

# 💡 Why This Tool Exists

The **Guqin instrument in Where Winds Meet** has a limited playable range.

Most MIDI songs exceed this range and become unplayable.

SuperQin automatically adapts these songs so they can be played on the Guqin.

---

# 🔮 Future Ideas

Potential upgrades:

* real-time MIDI keyboard input
* automatic melody detection
* AI-based chord reduction
* MIDI visualization timeline
* latency calibration
* standalone executable build

---

# 📜 License

Open source project for educational and community use.

---

# 👤 Credits

Created for the **Where Winds Meet Guqin music community**.
