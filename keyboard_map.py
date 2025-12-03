# ==========================================================
# keyboard_map.py — Guqin Layout + Note Mappings (Explicit & Corrected)
# ==========================================================

# --- Keyboard Layout Definition ---
top_row_keys = ['q','w','e','r','t','y','u']
mid_row_keys = ['a','s','d','f','g','h','j']
bot_row_keys = ['z','x','c','v','b','n','m']
all_keys = top_row_keys + mid_row_keys + bot_row_keys

# --- Explicit Note-to-Key Mapping (CORRECTED) ---
# This dictionary now precisely matches your provided layout.
note_to_key = {
    # Natural Notes (Corrected Octaves)
    'C4': ('q', 'normal'), 'D4': ('w', 'normal'), 'E4': ('e', 'normal'), 'F4': ('r', 'normal'), 'G4': ('t', 'normal'), 'A4': ('y', 'normal'), 'B4': ('u', 'normal'),
    'C3': ('a', 'normal'), 'D3': ('s', 'normal'), 'E3': ('d', 'normal'), 'F3': ('f', 'normal'), 'G3': ('g', 'normal'), 'A3': ('h', 'normal'), 'B3': ('j', 'normal'),
    'C2': ('z', 'normal'), 'D2': ('x', 'normal'), 'E2': ('c', 'normal'), 'F2': ('v', 'normal'), 'G2': ('b', 'normal'), 'A2': ('n', 'normal'), 'B2': ('m', 'normal'),

    # Sharps (Shift) - Using '#' for sharps
    'C#4': ('q', 'shift'), 'F#4': ('r', 'shift'), 'G#4': ('t', 'shift'),
    'C#3': ('a', 'shift'), 'F#3': ('f', 'shift'), 'G#3': ('g', 'shift'),
    'C#2': ('z', 'shift'), 'F#2': ('v', 'shift'), 'G#2': ('b', 'shift'),

    # Flats (Ctrl) - Using 'b' for flats, as is standard in MIDI
    'Eb4': ('e', 'ctrl'), 'Bb4': ('u', 'ctrl'),
    'Eb3': ('d', 'ctrl'), 'Bb3': ('j', 'ctrl'),
    'Eb2': ('c', 'ctrl'), 'Bb2': ('m', 'ctrl'),
}

# --- Derived Properties ---
# Create a set of all available notes from the explicit map
available_notes = set(note_to_key.keys())

# MIDI number → name (Extended to C1-B8)
midi_note_names = [
    f"{p}{o}"
    for o in range(1, 10) # Octaves 1 through 9 (to include C8)
    for p in ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
]

# Define the mappable range by finding the min/max MIDI numbers from our explicit map
try:
    temp_midi_to_note = {name: i for i, name in enumerate(midi_note_names)}
    mappable_midi_numbers = [temp_midi_to_note[n] for n in available_notes if n in temp_midi_to_note]
    MIN_MAPPED_NOTE = min(mappable_midi_numbers)
    MAX_MAPPED_NOTE = max(mappable_midi_numbers)
except Exception:
    # Fallback in case of an error
    MIN_MAPPED_NOTE = 36 # C2
    MAX_MAPPED_NOTE = 83 # B5

print(f"[DEBUG] Mappable MIDI range: {MIN_MAPPED_NOTE} to {MAX_MAPPED_NOTE}")