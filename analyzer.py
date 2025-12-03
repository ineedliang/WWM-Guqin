# ==========================================================
# midi_analyzer.py — A tool to find MIDI files best suited for your keyboard
# ==========================================================

import os
import sys
import mido

# --- Configuration ---
# The script needs to know your mappable range. We can import it from your keyboard_map file.
try:
    from keyboard_map import MIN_MAPPED_NOTE, MAX_MAPPED_NOTE
    print(f"[INFO] Using mappable range: {MIN_MAPPED_NOTE} to {MAX_MAPPED_NOTE}")
except ImportError:
    print("[WARNING] Could not import from keyboard_map.py. Using default range (C2-B5).")
    # Default range if keyboard_map.py is not found
    MIN_MAPPED_NOTE = 36  # C2
    MAX_MAPPED_NOTE = 83  # B5

# --- Analysis Logic ---

def analyze_midi_file(file_path):
    """
    Analyzes a single MIDI file and returns the count of total notes
    and in-range notes.
    """
    total_notes = 0
    in_range_notes = 0
    try:
        mid = mido.MidiFile(file_path)
        for track in mid.tracks:
            for msg in track:
                # We only care about 'note_on' messages with a velocity > 0
                if msg.type == 'note_on' and msg.velocity > 0:
                    total_notes += 1
                    if MIN_MAPPED_NOTE <= msg.note <= MAX_MAPPED_NOTE:
                        in_range_notes += 1
    except Exception as e:
        print(f"\n[ERROR] Could not parse {os.path.basename(file_path)}: {e}")
        return None, None

    return total_notes, in_range_notes

def find_midi_files(directory):
    """
    Recursively finds all .mid or .midi files in a directory.
    """
    midi_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.mid', '.midi')):
                midi_files.append(os.path.join(root, file))
    return midi_files

# --- Main Execution ---

def main():
    if len(sys.argv) < 2:
        print("Usage: python midi_analyzer.py <path_to_midi_directory>")
        sys.exit(1)

    target_directory = sys.argv[1]
    if not os.path.isdir(target_directory):
        print(f"Error: Directory not found at '{target_directory}'")
        sys.exit(1)

    midi_files = find_midi_files(target_directory)
    if not midi_files:
        print(f"No MIDI files found in '{target_directory}' or its subdirectories.")
        sys.exit(0)

    print(f"Found {len(midi_files)} MIDI files. Analyzing...\n")

    # Use tqdm for a progress bar if it's available
    try:
        from tqdm import tqdm
        file_iterator = tqdm(midi_files, desc="Analyzing files", unit="file")
    except ImportError:
        file_iterator = midi_files

    results = []
    for file_path in file_iterator:
        total, in_range = analyze_midi_file(file_path)
        if total is not None:
            percentage = (in_range / total) * 100 if total > 0 else 0
            results.append({
                'filename': os.path.basename(file_path),
                'percentage': percentage,
                'total': total,
                'in_range': in_range
            })

    # Sort results by percentage, in descending order
    results.sort(key=lambda x: x['percentage'], reverse=True)

    # --- Display Results ---
    print("\n--- Analysis Complete ---")
    print("Rank | Filename                 | In-Range % | Total Notes | In-Range Notes")
    print("-----|--------------------------|------------|-------------|----------------")
    for i, item in enumerate(results):
        # Format the output into a nice, aligned table
        print(f"{i+1:<4} | {item['filename'][:24]:<24} | {item['percentage']:<10.2f}% | {item['total']:<11} | {item['in_range']}")


if __name__ == "__main__":
    main()