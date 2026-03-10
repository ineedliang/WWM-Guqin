# ==========================================================
# midi_player_v2.py — Enhanced MIDI Playback with Octave Shift & Duration
# ==========================================================

import threading
import time
import pygame.midi
import platform
from PyQt6.QtCore import QObject, pyqtSignal

class MidiPlayer(QObject):
    """
    Enhanced MIDI player with octave transposition and note duration support.
    Emits signals for playback status and progress.
    """
    playbackFinished = pyqtSignal()
    playbackProgress = pyqtSignal(float)  # Emits current time in seconds
    
    def __init__(self):
        super().__init__()
        self.player = None
        self.thread = None
        self.stop_flag = False
        self.notes = []  # Will store (time_in_seconds, midi_note_number, duration, velocity)
        self.speed = 1.0
        self.is_playing = False
        self.octave_shift = 0  # NEW: Octave shift for playback
        self.max_duration = None  # NEW: Optional max duration cap in seconds
        
        try:
            pygame.midi.init()
            print(f"[MidiPlayer] Pygame MIDI initialized.")
            
            # Get the default output device ID
            output_id = pygame.midi.get_default_output_id()
            print(f"[MidiPlayer] Default MIDI Output ID: {output_id}")

            if output_id < 0:
                if platform.system() == "Windows":
                    print("[MidiPlayer] ERROR: No default MIDI output device found.")
                    print("[MidiPlayer] On Windows, you may need to install a MIDI synthesizer like CoolSoft VirtualMIDISynth.")
                else:
                    print("[MidiPlayer] ERROR: No MIDI output device found.")
                self.player = None
            else:
                self.player = pygame.midi.Output(output_id)
                self.player.set_instrument(0)  # Piano
                print(f"[MidiPlayer] Successfully opened MIDI output device ID {output_id}.")

        except Exception as e:
            print(f"[MidiPlayer] FATAL ERROR initializing pygame.midi: {e}")
            self.player = None
        
    def load_notes(self, notes, octave_shift=0):
        """
        Load notes for playback with optional octave transposition.
        Args:
            notes: List of (time, note, duration, velocity) tuples where time is in seconds.
            octave_shift: Number of octaves to shift playback (positive = higher, negative = lower)
        """
        self.notes = notes
        self.octave_shift = octave_shift
        print(f"[MidiPlayer] Loaded {len(self.notes)} notes for playback with {octave_shift} octave shift.")
        
    def set_speed(self, speed):
        """Set playback speed multiplier (1.0 = normal speed)."""
        self.speed = speed
        
    def set_max_duration(self, max_duration):
        """Set maximum note duration cap in seconds."""
        self.max_duration = max_duration
        print(f"[MidiPlayer] Max duration set to {max_duration}s")
        
    def play(self):
        """Start playback in a separate thread."""
        if not self.player:
            print("[MidiPlayer] Cannot play: MIDI player not initialized.")
            return
            
        if not self.notes:
            print("[MidiPlayer] Cannot play: No notes loaded.")
            return
            
        if self.is_playing:
            print("[MidiPlayer] Already playing.")
            return
            
        self.stop_flag = False
        self.is_playing = True
        print("[MidiPlayer] Starting playback...")
        self.thread = threading.Thread(target=self._playback_thread)
        self.thread.start()
        
    def stop(self):
        """Stop playback."""
        if not self.is_playing:
            return
            
        print("[MidiPlayer] Stopping playback...")
        self.stop_flag = True
        if self.thread and self.thread.is_alive():
            self.thread.join()
        self.is_playing = False
        # Ensure all notes are turned off
        if self.player:
            for _, note, _, _ in self.notes:
                shifted_note = note + (self.octave_shift * 12)
                if 0 <= shifted_note <= 127:
                    self.player.note_off(shifted_note, 0)

    def _playback_thread(self):
        """Main playback loop with note duration and velocity support."""
        last_time = 0
        active_notes = {}  # Track which notes are currently playing
        
        # Create a timeline of all note on/off events
        events = []
        for time_sec, note, duration, velocity in self.notes:
            shifted_note = note + (self.octave_shift * 12)
            if 0 <= shifted_note <= 127:
                # Apply max duration cap if set
                actual_duration = duration
                if self.max_duration is not None and duration > self.max_duration:
                    actual_duration = self.max_duration
                
                events.append((time_sec, 'on', shifted_note, velocity))
                events.append((time_sec + actual_duration, 'off', shifted_note, 0))
        
        # Sort events by time
        events.sort(key=lambda x: x[0])
        
        for event_time, event_type, note, velocity in events:
            if self.stop_flag:
                break
                
            sleep_time = (event_time - last_time) / self.speed
            if sleep_time > 0:
                time.sleep(sleep_time)
                
            if self.player:
                if event_type == 'on':
                    self.player.note_on(note, velocity)
                    active_notes[note] = True
                else:
                    self.player.note_off(note, 0)
                    active_notes.pop(note, None)
                    
            last_time = event_time
            
            # Emit progress signal
            try:
                self.playbackProgress.emit(event_time)
            except:
                pass
            
        # Turn off any remaining active notes
        if self.player:
            for note in active_notes:
                self.player.note_off(note, 0)
            
        self.is_playing = False
        print("[MidiPlayer] Playback finished.")
        self.playbackFinished.emit()
        
    def cleanup(self):
        """Clean up resources when the application closes."""
        print("[MidiPlayer] Cleaning up...")
        self.stop()
        if self.player:
            self.player.close()
        pygame.midi.quit()
