# 🎼 SuperQin v2

### Advanced MIDI Player for Guqin (Where Winds Meet)

![Python](https://img.shields.io/badge/python-3.10+-blue)
![PyQt6](https://img.shields.io/badge/gui-PyQt6-green)
![MIDI](https://img.shields.io/badge/midi-supported-purple)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

**SuperQin v2** is an advanced **MIDI playback and automation tool** designed for the **Guqin instrument in *Where Winds Meet***.

It allows you to load MIDI files, analyze tracks, mix instruments, and automatically play them in-game using keyboard simulation.

This project expands on earlier Guqin tools by providing a **full graphical interface, MIDI processing engine, and playback control system.**

---

# ✨ Features

### 🎹 MIDI Playback

* Load and play standard `.mid` files
* Convert MIDI notes to Guqin key inputs
* Automatic timing synchronization

### 🖥 Modern GUI

* Built with **PyQt6**
* Real-time playback controls
* Track visualization widgets

### 🎛 Track Mixing

* Enable or disable individual MIDI tracks
* Adjust playback timing
* Control which instruments are mapped to Guqin

### 🎼 Note Visualization

* Visual display of note playback
* Timeline view for musical structure
* Useful for debugging MIDI files

### 📊 MIDI Analysis

* Inspect MIDI structure
* Analyze track timing and note data
* Identify playable note ranges

### ⚡ Real-Time Playback Engine

* Accurate event scheduling
* MIDI event processing
* Optimized timing for rhythm gameplay

---

# 🧠 How It Works

```
MIDI File
    ↓
MIDI Processor
    ↓
Track Mixer
    ↓
Key Mapping System
    ↓
Keyboard Input
    ↓
Where Winds Meet (Guqin)
```

SuperQin reads MIDI data, processes note events, converts them to Guqin key mappings, and sends keyboard inputs to the game.

---

# 📦 Project Structure

```
SuperQin/
│
├── main_v2.py              # Application launcher
├── gui_main_v2.py          # Main GUI interface
├── midi_player_v2.py       # Playback engine
├── midi_processor_v2.py    # MIDI parsing system
├── keyboard_map.py         # Guqin key mapping
├── track_mixer.py          # Track management
├── note_widget_v2.py       # Visual note display
├── analyzer.py             # MIDI analysis tools
└── track_time_dialog.py    # Track timing editor
```

---

# 🛠 Requirements

Install Python dependencies:

```
pip install PyQt6 mido python-rtmidi keyboard
```

You may also need:

```
pip install numpy
```

---

# ▶ Running the Program

Launch the application:

```
python main_v2.py
```

The GUI will open and allow you to load MIDI files.

---

# 🎮 Usage

1. Start **SuperQin v2**
2. Load a `.mid` file
3. Select active tracks
4. Start playback
5. Switch to the **Guqin instrument in Where Winds Meet**

The tool will automatically play the song.

---

# 🎵 Supported MIDI Features

* Multi-track MIDI
* Tempo changes
* Note timing synchronization
* Track filtering

Some extremely complex MIDI files may require track adjustment.

---

# ⚠ Notes

* The game must be in focus for keyboard playback.
* Some MIDI files may contain notes outside the Guqin range.
* Track filtering may be necessary for optimal playback.

---

# 💡 Future Improvements

Potential upgrades:

* MIDI → Guqin automatic conversion
* real-time MIDI keyboard support
* song library manager
* improved visual timeline
* exportable Guqin song format
* latency calibration system

---

# 📜 License

Open-source project for educational and personal use.

---

# 👤 Credits

Developed as an advanced tool for the **Where Winds Meet Guqin community**.

Inspired by earlier Guqin automation and MIDI playback projects.
