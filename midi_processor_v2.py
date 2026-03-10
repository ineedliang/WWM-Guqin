# ==========================================================
# midi_processor_v2.py — Enhanced MIDI Processing with Duration & Velocity
# ==========================================================
import io
import struct
import mido
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QColor

# Import mapping dependencies
try:
    from keyboard_map import midi_note_names, note_to_key, available_notes, MIN_MAPPED_NOTE, MAX_MAPPED_NOTE
except Exception:
    midi_note_names = [f"{p}{o}" for o in range(1, 10) for p in ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]]
    note_to_key = {}
    available_notes = set()
    MIN_MAPPED_NOTE = 36
    MAX_MAPPED_NOTE = 83

# Import sanitization functions from original
def _encode_vlq(v):
    buf = [v & 0x7F]
    v >>= 7
    while v:
        buf.insert(0, 0x80 | (v & 0x7F))
        v >>= 7
    return bytes(buf)

def _read_vlq(data_mv, pos):
    """Return (value, new_pos) or (None, fallback_pos) on malformed."""
    value = 0
    start = pos
    while pos < len(data_mv):
        b = data_mv[pos]
        pos += 1
        value = (value << 7) | (b & 0x7F)
        if b < 0x80:
            return value, pos
        if pos - start > 4:
            break
    return None, start + 1

def _fix_meta(event_type, length, payload_bytes):
    """Sanitize common meta-event payloads."""
    if event_type == 0x58:  # time signature
        if length < 4:
            return bytes([4, 2, 24, 8])
        return payload_bytes[:4]
    if event_type == 0x59:  # key signature
        if length < 2:
            return bytes([0, 0])
        return payload_bytes[:2]
    if event_type == 0x51:  # tempo
        if length < 3:
            return b'\x07\xa1\x20'
        return payload_bytes[:3]
    if event_type == 0x54:  # SMPTE offset
        if length < 5:
            return bytes([0,0,0,0,0])
        return payload_bytes[:5]
    return payload_bytes[:length]

def safe_load_midi(path):
    """Load MIDI from path, repairing malformed meta events and truncated chunks."""
    raw = open(path, 'rb').read()
    data_mv = memoryview(raw)
    sanitized = bytearray()

    if len(raw) < 14 or raw[0:4] != b'MThd':
        try:
            return mido.MidiFile(file=io.BytesIO(raw))
        except Exception:
            raise

    sanitized.extend(raw[0:14])
    pos = 14
    total_len = len(raw)

    while pos < total_len:
        if pos + 8 > total_len or raw[pos:pos+4] != b'MTrk':
            break
        sanitized.extend(raw[pos:pos+4])
        track_len = struct.unpack(">I", raw[pos+4:pos+8])[0]
        pos += 8
        track_end = pos + track_len
        if track_end > total_len:
            track_end = total_len

        track_out = bytearray()
        last_status = None

        while pos < track_end:
            delta, new_pos = _read_vlq(data_mv, pos)
            if delta is None:
                delta = 0
                pos = new_pos
            else:
                pos = new_pos
            track_out.extend(_encode_vlq(delta))

            if pos >= track_end:
                break

            status_b = data_mv[pos]
            if status_b >= 0x80:
                status = int(status_b)
                pos += 1
                last_status = status
            else:
                status = int(last_status) if last_status is not None else 0x90

            if status == 0xFF:
                if pos >= track_end:
                    break
                meta_type = int(data_mv[pos]); pos += 1
                meta_len, new_pos = _read_vlq(data_mv, pos)
                if meta_len is None:
                    meta_len = 0
                    pos = new_pos
                else:
                    pos = new_pos
                if pos + meta_len > total_len:
                    meta_len = max(0, total_len - pos)
                payload = data_mv[pos:pos+meta_len].tobytes()
                pos += meta_len
                payload = _fix_meta(meta_type, meta_len, payload)
                track_out.extend(b'\xFF')
                track_out.append(meta_type)
                track_out.extend(_encode_vlq(len(payload)))
                track_out.extend(payload)
                continue

            if status == 0xF0 or status == 0xF7:
                syx_len, new_pos = _read_vlq(data_mv, pos)
                if syx_len is None:
                    syx_len = 0
                    pos = new_pos
                else:
                    pos = new_pos
                if pos + syx_len > total_len:
                    syx_len = max(0, total_len - pos)
                track_out.append(status)
                track_out.extend(_encode_vlq(syx_len))
                track_out.extend(data_mv[pos:pos+syx_len].tobytes())
                pos += syx_len
                continue

            msg_type = status & 0xF0
            if msg_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                args = 2
            elif msg_type in (0xC0, 0xD0):
                args = 1
            else:
                args = 2

            if pos + args > total_len:
                break

            track_out.append(status)
            for i in range(args):
                track_out.append(int(data_mv[pos + i]))
            pos += args

        sanitized.extend(struct.pack(">I", len(track_out)))
        sanitized.extend(track_out)

    buf = io.BytesIO(bytes(sanitized))
    try:
        return mido.MidiFile(file=buf)
    except Exception:
        return mido.MidiFile(file=io.BytesIO(raw))

def reduce_chords_to_root(notes, chord_tolerance_ms=30):
    """Reduces chords to root note. Handles (time, note, track_idx, duration, velocity) tuples."""
    if not notes:
        return []
        
    reduced_notes = []
    i = 0
    chord_tolerance_seconds = chord_tolerance_ms / 1000.0

    while i < len(notes):
        chord_notes = [notes[i]]
        j = i + 1
        while j < len(notes) and (notes[j][0] - notes[i][0]) <= chord_tolerance_seconds:
            chord_notes.append(notes[j])
            j += 1
        
        if len(chord_notes) > 1:
            root_note = min(chord_notes, key=lambda note_tuple: note_tuple[1])
            reduced_notes.append(root_note)
        else:
            reduced_notes.append(chord_notes[0])
        
        i = j
        
    return reduced_notes


class MidiProcessorV2(QThread):
    """Enhanced MIDI processor with duration and velocity extraction."""
    
    progress = pyqtSignal(int)
    finished = pyqtSignal(list, list, list)  # viz_data, track_colors, full_note_data
    track_info = pyqtSignal(list)

    def __init__(self, path, track_settings=None, remap_mode="hybrid", start_time=0.0, 
                 end_time=999.0, chord_tolerance_ms=30, automap_out_of_range=False, 
                 time_ranges=None):
        super().__init__()
        self.path = path
        self.track_settings = track_settings or {}
        self.remap_mode = remap_mode.lower()
        self.start_time = start_time
        self.end_time = end_time
        self.chord_tolerance_ms = chord_tolerance_ms
        self.automap_out_of_range = automap_out_of_range
        self.time_ranges = time_ranges or {}
        
        self.note_to_key = note_to_key
        self.midi_note_names = midi_note_names
        self.key_mode_to_note = { (v[0], v[1]): k for k, v in note_to_key.items() }

    def run(self):
        try:
            mid = safe_load_midi(self.path)
        except Exception as e:
            print("SANITIZER FAILED:", e)
            self.finished.emit([], [], [])
            return

        ticks_per_beat = getattr(mid, 'ticks_per_beat', 480)
        tempo = 500000

        # Gather track info
        track_meta = []
        for ti, tr in enumerate(mid.tracks):
            if self.isInterruptionRequested():
                return
            name = f"Track {ti+1}"
            note_count = 0
            for msg in tr:
                if getattr(msg, 'type', None) == 'track_name':
                    try:
                        name = msg.name
                    except Exception:
                        pass
                if getattr(msg, 'type', None) == 'note_on' and getattr(msg, 'velocity', 0) > 0:
                    note_count += 1
            track_meta.append((ti, name, note_count))

        self.track_info.emit(track_meta)

        selected_tracks = set(self.track_settings.keys())
        print(f"[DEBUG] Processor will analyze tracks: {selected_tracks}")

        all_merged_notes = []
        total_msgs = sum(len(mid.tracks[ti]) for ti in selected_tracks)
        processed_msgs = 0
        notes_found = 0

        # Process each selected track
        for ti in selected_tracks:
            if self.isInterruptionRequested():
                return
            
            settings = self.track_settings.get(ti, {})
            octave_shift = settings.get('octave_shift', 0)
            semitone_shift = settings.get('semitone_shift', 0)
            reduce_to_root = settings.get('reduce_to_root', False)
            time_shift = settings.get('time_shift', 0.0)
            
            print(f"[DEBUG] Processing Track {ti}: octave={octave_shift}, semitone={semitone_shift}, reduce={reduce_to_root}, time={time_shift}s")
            
            abs_time = 0
            tr = mid.tracks[ti]
            track_notes = []
            active_notes = {}  # Track note_on to calculate duration
            
            for msg in tr:
                if self.isInterruptionRequested():
                    return
                processed_msgs += 1
                if total_msgs > 0:
                    try:
                        self.progress.emit(int(processed_msgs / total_msgs * 100))
                    except Exception:
                        pass
                        
                abs_time += getattr(msg, 'time', 0)
                if getattr(msg, 'type', None) == 'set_tempo':
                    tempo = getattr(msg, 'tempo', tempo)
                
                # Handle note_on events
                if getattr(msg, 'type', None) == 'note_on' and getattr(msg, 'velocity', 0) > 0:
                    note = getattr(msg, 'note', 0) + (octave_shift * 12) + semitone_shift
                    velocity = getattr(msg, 'velocity', 64)
                    
                    if 0 <= note < len(midi_note_names):
                        try:
                            seconds = mido.tick2second(abs_time, ticks_per_beat, tempo)
                            adjusted_seconds = seconds + time_shift
                            
                            # Check time ranges
                            if ti in self.time_ranges:
                                in_range = False
                                for start, end in self.time_ranges[ti]:
                                    if start <= adjusted_seconds <= end:
                                        in_range = True
                                if not in_range:
                                    continue
                            
                            if adjusted_seconds >= 0:
                                active_notes[note] = (adjusted_seconds, velocity, abs_time)
                        except Exception as e:
                            print(f"[DEBUG] ERROR in tick2second: {e}")
                
                # Handle note_off
                elif (getattr(msg, 'type', None) == 'note_off' or 
                      (getattr(msg, 'type', None) == 'note_on' and getattr(msg, 'velocity', 0) == 0)):
                    note = getattr(msg, 'note', 0) + (octave_shift * 12) + semitone_shift
                    
                    if note in active_notes:
                        start_time, velocity, start_ticks = active_notes[note]
                        try:
                            end_seconds = mido.tick2second(abs_time, ticks_per_beat, tempo) + time_shift
                            duration = max(0.01, end_seconds - start_time)
                            
                            track_notes.append((start_time, note, ti, duration, velocity))
                            notes_found += 1
                            del active_notes[note]
                        except Exception as e:
                            print(f"[DEBUG] ERROR calculating duration: {e}")
            
            # Handle notes without note_off (give default duration)
            for note, (start_time, velocity, _) in active_notes.items():
                track_notes.append((start_time, note, ti, 0.1, velocity))
                notes_found += 1
            
            if reduce_to_root:
                print(f"[DEBUG] Reducing chords in track {ti}...")
                track_notes.sort(key=lambda x: x[0])
                track_notes = reduce_chords_to_root(track_notes, self.chord_tolerance_ms)
                print(f"[DEBUG] Track {ti}: {len(track_notes)} notes after reduction")
            
            all_merged_notes.extend(track_notes)

        print(f"[DEBUG] Collected {notes_found} notes total")

        # Auto-Map
        if self.automap_out_of_range:
            print(f"[DEBUG] Applying Auto-Map...")
            automapped_notes = []
            for time, note_idx, track_idx, duration, velocity in all_merged_notes:
                if note_idx < MIN_MAPPED_NOTE:
                    shifts = ((MIN_MAPPED_NOTE - note_idx) // 12) + 1
                    new_note = note_idx + (shifts * 12)
                    automapped_notes.append((time, new_note, track_idx, duration, velocity))
                elif note_idx > MAX_MAPPED_NOTE:
                    shifts = ((note_idx - MAX_MAPPED_NOTE) // 12) + 1
                    new_note = note_idx - (shifts * 12)
                    automapped_notes.append((time, new_note, track_idx, duration, velocity))
                else:
                    automapped_notes.append((time, note_idx, track_idx, duration, velocity))
            all_merged_notes = automapped_notes

        # Filter by time frame
        final_notes = [n for n in all_merged_notes if self.start_time <= n[0] <= self.end_time]
        final_notes.sort(key=lambda x: x[0])
        print(f"[DEBUG] {len(final_notes)} notes after filtering")

        # Create visualization and full data
        visualization_data = []
        full_note_data = []
        
        for seconds, note_idx, track_idx, duration, velocity in final_notes:
            is_in_range = MIN_MAPPED_NOTE <= note_idx <= MAX_MAPPED_NOTE
            key = None
            mode = None
            
            if is_in_range:
                try:
                    name = midi_note_names[note_idx]
                    if name in note_to_key:
                        key, mode = note_to_key[name]
                except Exception:
                    pass
            
            visualization_data.append((seconds, note_idx, key, mode, is_in_range, track_idx))
            full_note_data.append((seconds, note_idx, key, mode, is_in_range, track_idx, duration, velocity))

        # Generate track colors
        track_colors = []
        num_tracks = len(track_meta)
        for i in range(num_tracks):
            hue = int((i / num_tracks) * 360)
            color = QColor.fromHsv(hue, 200, 200)
            track_colors.append(color)

        print(f"[DEBUG] Processing complete: {len(visualization_data)} notes")
        try: 
            self.progress.emit(100)
        except: 
            pass
            
        self.finished.emit(visualization_data, track_colors, full_note_data)


def export_to_midi(notes, output_path, tempo_bpm=120):
    """Export processed notes to MIDI file."""
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    tempo_us = mido.bpm2tempo(tempo_bpm)
    track.append(mido.MetaMessage('set_tempo', tempo=tempo_us))
    
    events = []
    for time_sec, note_idx, _, _, _, _, duration, velocity in notes:
        if MIN_MAPPED_NOTE <= note_idx <= MAX_MAPPED_NOTE:
            events.append((time_sec, 'note_on', note_idx, velocity))
            events.append((time_sec + duration, 'note_off', note_idx, 0))
    
    events.sort(key=lambda x: x[0])
    
    last_time = 0
    for event_time, event_type, note, velocity in events:
        delta_time = event_time - last_time
        delta_ticks = mido.second2tick(delta_time, mid.ticks_per_beat, tempo_us)
        
        if event_type == 'note_on':
            track.append(mido.Message('note_on', note=note, velocity=velocity, time=int(delta_ticks)))
        else:
            track.append(mido.Message('note_off', note=note, velocity=0, time=int(delta_ticks)))
        
        last_time = event_time
    
    mid.save(output_path)
    print(f"[MIDI Export] Saved to {output_path}")
