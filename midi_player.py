# ==========================================================
# midi_player.py — MIDI Playback Component
# ==========================================================

import threading
import time
import pygame.midi
import platform
from PyQt6.QtCore import QObject, pyqtSignal

class MidiPlayer(QObject):
    """
    A simple MIDI player using pygame.
    Emits a signal when playback is finished.
    """
    # Signal to emit when playback finishes
    playbackFinished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.player = None
        self.thread = None
        self.stop_flag = False
        self.notes = []  # Will store (time_in_seconds, midi_note_number)
        self.speed = 1.0
        self.is_playing = False
        
        try:
            pygame.midi.init()
            print(f"[MidiPlayer] Pygame MIDI initialized.")
            
            # Get the default output device ID
            output_id = pygame.midi.get_default_output_id()
            print(f"[MidiPlayer] Default MIDI Output ID: {output_id}")

            if output_id < 0:
                # This is common on modern Windows. We'll print a more helpful error.
                if platform.system() == "Windows":
                    print("[MidiPlayer] ERROR: No default MIDI output device found.")
                    print("[MidiPlayer] On Windows, you may need to install a MIDI synthesizer like CoolSoft VirtualMIDISynth.")
                else:
                    print("[MidiPlayer] ERROR: No MIDI output device found.")
                self.player = None # Ensure player is None
            else:
                self.player = pygame.midi.Output(output_id)
                print(f"[MidiPlayer] Successfully opened MIDI output device ID {output_id}.")

        except Exception as e:
            print(f"[MidiPlayer] FATAL ERROR initializing pygame.midi: {e}")
            self.player = None
        
    def load_notes(self, notes):
        """
        Load notes for playback.
        Args:
            notes: List of (time, note) tuples where time is in seconds.
        """
        self.notes = notes
        print(f"[MidiPlayer] Loaded {len(self.notes)} notes for playback.")
        
    def set_speed(self, speed):
        """
        Set playback speed.
        Args:
            speed: Playback speed multiplier (1.0 = normal speed).
        """
        self.speed = speed
        
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
            for _, note in self.notes:
                self.player.note_off(note, 0)

    def _playback_thread(self):
        """The main loop for playing notes, runs in a separate thread."""
        last_time = 0
        
        for time_sec, note in self.notes:
            if self.stop_flag:
                break
                
            sleep_time = (time_sec - last_time) / self.speed
            if sleep_time > 0:
                time.sleep(sleep_time)
                
            # Play the note (MIDI note on, velocity 100)
            if self.player:
                self.player.note_on(note, 100)
            last_time = time_sec
            
        # After the loop, turn off all notes that were played
        if self.player:
            for _, note in self.notes:
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