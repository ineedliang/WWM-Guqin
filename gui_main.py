# ==========================================================
# gui_main.py — Main GUI Window (with Auto-Map)
# ==========================================================
import os
import json
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                             QFileDialog, QSlider, QLabel, QMessageBox, QComboBox, QCheckBox, QDoubleSpinBox, QSplitter)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from midi_processor import MidiProcessor
from track_mixer import TrackMixer
from note_widget import NoteWidget
from midi_player import MidiPlayer

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SuperQin — Guqin MIDI Mapper")
        self.resize(1200, 700)

        # Use a HORIZONTAL splitter for the main layout
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(main_splitter)

        # LEFT — Visualization + Buttons
        left_widget = QWidget()
        left = QVBoxLayout(left_widget)
        main_splitter.addWidget(left_widget)

        self.note = NoteWidget()
        left.addWidget(self.note, 1) # Give note widget all extra space

        # --- Main Action Buttons ---
        btn_row = QHBoxLayout()
        left.addLayout(btn_row)

        self.btn_load = QPushButton("Load MIDI")
        self.btn_load.clicked.connect(self.load_midi)
        btn_row.addWidget(self.btn_load)

        # Add save/load project buttons
        self.btn_save_project = QPushButton("Save Project")
        self.btn_save_project.clicked.connect(self.save_project)
        btn_row.addWidget(self.btn_save_project)

        self.btn_load_project = QPushButton("Load Project")
        self.btn_load_project.clicked.connect(self.load_project)
        btn_row.addWidget(self.btn_load_project)

        self.btn_play = QPushButton("Preview")
        self.btn_play.clicked.connect(self.preview)
        btn_row.addWidget(self.btn_play)
        
        self.btn_audio_play = QPushButton("Play Audio")
        self.btn_audio_play.clicked.connect(self.play_audio)
        btn_row.addWidget(self.btn_audio_play)
        
        self.btn_audio_stop = QPushButton("Stop Audio")
        self.btn_audio_stop.clicked.connect(self.stop_audio)
        self.btn_audio_stop.setEnabled(False)
        btn_row.addWidget(self.btn_audio_stop)

        self.btn_export = QPushButton("Export AHK")
        self.btn_export.clicked.connect(self.export_ahk)
        btn_row.addWidget(self.btn_export)

        # RIGHT — Mixer and Global Controls
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        main_splitter.addWidget(right_widget)
        
        self.mixer = TrackMixer()
        right_layout.addWidget(self.mixer)
        
        # Set the HORIZONTAL splitter to 50/50 (or adjust as needed)
        # This gives the right panel more horizontal space, which helps
        main_splitter.setSizes([600, 600])
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 0) # Right side doesn't need to stretch horizontally

        # Connect signals from the mixer's new controls
        self.mixer.btn_apply.clicked.connect(self.process_notes)
        self.mixer.combo_remap.currentTextChanged.connect(self.process_notes)
        self.mixer.chk_automap.stateChanged.connect(self.process_notes)
        self.mixer.sld_speed.valueChanged.connect(self.on_speed_changed)
        self.mixer.sld_tolerance.valueChanged.connect(self.on_tolerance_changed)
        self.mixer.btn_set_full_song.clicked.connect(self.set_time_frame_to_full_song)

        # Internal state
        self.midi_path = None
        self.current_notes = []
        self.playback_speed = 1.0
        self.total_duration = 0.1
        self.chord_tolerance_ms = 30
        
        # Initialize MIDI player
        self.midi_player = MidiPlayer()
        self.midi_player.playbackFinished.connect(self.on_audio_finished)
        
        if self.midi_player.player is None:
            QMessageBox.warning(self, "MIDI Error", "Could not find a default MIDI output device. \nAudio playback will be disabled. \n\nPlease ensure a MIDI synthesizer (like CoolSoft VirtualMIDISynth) is installed and enabled.")

        # Processor threads
        self.meta_processor = None
        self.note_processor = None

    def load_midi(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select MIDI", "", "MIDI (*.mid)")
        if not path:
            return
        self.midi_path = path
        
        self.stop_all_threads()
        self.stop_audio()
        self.mixer.clear()
        
        print("[DEBUG] Getting track info for new file...")
        self.meta_processor = MidiProcessor(self.midi_path)
        self.meta_processor.track_info.connect(self.populate_mixer_and_process_notes)
        self.meta_processor.start()

    def populate_mixer_and_process_notes(self, tracks):
        print("[DEBUG] Populating mixer with new track info...")
        self.mixer.populate(tracks)
        self.process_notes()

    def process_notes(self):
        if not self.midi_path:
            return

        if self.note_processor is not None:
            self.note_processor.requestInterruption()
            self.note_processor.wait()

        track_settings = self.mixer.get_track_settings()
        remap_mode = self.mixer.combo_remap.currentText().lower()
        start_time = self.mixer.spn_start_time.value()
        end_time = self.mixer.spn_end_time.value()
        
        # Get time ranges from the mixer
        time_ranges = getattr(self.mixer, 'track_time_ranges', {})
        
        print(f"[DEBUG] Re-processing notes. Mode: {remap_mode}, Track Settings: {track_settings}")
        print(f"[DEBUG] Time Frame: {start_time}s to {end_time}s, Chord Tolerance: {self.chord_tolerance_ms}ms")
        print(f"[DEBUG] Auto-Map enabled: {self.mixer.chk_automap.isChecked()}")
        print(f"[DEBUG] Time Ranges: {time_ranges}")

        self.note_processor = MidiProcessor(
            self.midi_path,
            track_settings=track_settings,
            remap_mode=remap_mode,
            start_time=start_time,
            end_time=end_time,
            chord_tolerance_ms=self.chord_tolerance_ms,
            automap_out_of_range=self.mixer.chk_automap.isChecked(),
            time_ranges=time_ranges  # Pass the time ranges
        )

        # MODIFIED: Disconnect any previous connections to prevent race conditions
        try:
            self.note_processor.finished.disconnect()
        except Exception:
            pass # It's okay if there was nothing to disconnect

        self.note_processor.finished.connect(self.finish_notes)
        print("[DEBUG] Starting note processor thread...")
        self.note_processor.start()
        
    def stop_all_threads(self):
        if self.meta_processor is not None:
            print("[DEBUG] Stopping meta processor...")
            self.meta_processor.requestInterruption()
            self.meta_processor.wait()
            self.meta_processor = None
            
        if self.note_processor is not None:
            print("[DEBUG] Stopping note processor...")
            self.note_processor.requestInterruption()
            self.note_processor.wait()
            self.note_processor = None

    # ==============================================================================
    # MODIFIED METHOD: This now handles the new data structure from MidiProcessor
    # ==============================================================================
    def finish_notes(self, viz_data, track_colors):
        # viz_data is the new list from the processor: (seconds, note_idx, key, mode, is_in_range, track_idx)
        if not viz_data:
            self.total_duration = 0.1
        else:
            self.total_duration = max(n[0] for n in viz_data)
        
        # 1. Pass the FULL data and colors to the visualizer
        self.note.load(viz_data, track_colors)
        print(f"[DEBUG] {len(viz_data)} notes loaded for visualization.")

        # 2. Create the list for AHK export (only mapped notes)
        self.current_notes = [(s, k, m) for s, _, k, m, is_r, _ in viz_data if k is not None]
        print(f"[DEBUG] {len(self.current_notes)} notes are mappable for AHK export.")

        # 3. MODIFIED: Create a list for MIDI player with ONLY in-range notes
        # This will make the audio preview match what the guqin can play.
        midi_notes = [(s, n) for s, n, _, _, is_in_range, _ in viz_data if is_in_range]
        print(f"[DEBUG] Loading {len(midi_notes)} in-range notes into MidiPlayer for preview.")
        self.midi_player.load_notes(midi_notes)
    # ==============================================================================

    def preview(self):
        self.note.update()
        
    def play_audio(self):
        if self.midi_player and self.midi_player.player:
            self.midi_player.set_speed(self.playback_speed)
            self.midi_player.play()
            self.btn_audio_play.setEnabled(False)
            self.btn_audio_stop.setEnabled(True)
        else:
            QMessageBox.information(self, "Cannot Play", "Audio playback is not available. Please check your MIDI device setup.")

    def stop_audio(self):
        if self.midi_player:
            self.midi_player.stop()
            self.btn_audio_play.setEnabled(True)
            self.btn_audio_stop.setEnabled(False)
            
    def on_audio_finished(self):
        self.btn_audio_play.setEnabled(True)
        self.btn_audio_stop.setEnabled(False)
        
    def on_speed_changed(self, value):
        self.playback_speed = value / 100.0
        self.mixer.lbl_speed.setText(f"{self.playback_speed:.2f}x")

    def on_tolerance_changed(self, value):
        self.chord_tolerance_ms = value
        self.mixer.lbl_tolerance.setText(f"{value}ms")

    def set_time_frame_to_full_song(self):
        self.mixer.spn_start_time.setValue(0.0)
        self.mixer.spn_end_time.setValue(self.total_duration)
        self.process_notes()

    def export_ahk(self):
        if not self.current_notes:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save AHK", "", "AHK (*.ahk)")
        if not path:
            return

        speed = self.playback_speed

        with open(path, 'w', encoding='utf8') as f:
            f.write("; Auto-generated by SuperQin\n")
            f.write(f"SendMode, Input\n")
            f.write(f"SetKeyDelay, 0, 0\n")
            f.write("Sleep, 2000\n")

            last = 0
            for t, k, m in self.current_notes:
                d = int((t - last) * 1000 / speed)
                f.write(f"Sleep, {d}\n")
                if m == 'normal': f.write(f"Send, {k}\n")
                if m == 'shift':  f.write(f"Send, {{Shift down}}{k}{{Shift up}}\n")
                if m == 'ctrl':   f.write(f"Send, {{Ctrl down}}{k}{{Ctrl up}}\n")
                last = t

        print("Saved:", path)

    def save_project(self):
        """Save the current project state to a JSON file."""
        if not self.midi_path:
            QMessageBox.warning(self, "No MIDI", "Please load a MIDI file first.")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "JSON (*.json)")
        if not path:
            return
            
        project_data = {
            "midi_path": self.midi_path,
            "playback_speed": self.playback_speed,
            "chord_tolerance_ms": self.chord_tolerance_ms,
            "start_time": self.mixer.spn_start_time.value(),
            "end_time": self.mixer.spn_end_time.value(),
            "remap_mode": self.mixer.combo_remap.currentText(),
            "automap_enabled": self.mixer.chk_automap.isChecked(),
            "track_settings": self.mixer.get_track_settings(),
            "global_controls": {
                "enable_all": self.mixer.chk_enable_all.isChecked(),
                "global_octave": self.mixer.sld_global_octave.value(),
                "global_semitone": self.mixer.sld_global_semitone.value(),
                "global_time": self.mixer.sld_global_time.value(),
                "global_reduce": self.mixer.chk_global_reduce.isChecked()
            },
            "time_ranges": getattr(self.mixer, 'track_time_ranges', {})  # Save time ranges
        }
        
        try:
            with open(path, 'w') as f:
                json.dump(project_data, f, indent=2)
            QMessageBox.information(self, "Success", f"Project saved to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project: {str(e)}")

    def load_project(self):
        """Load a project state from a JSON file."""
        path, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "JSON (*.json)")
        if not path:
            return
            
        try:
            with open(path, 'r') as f:
                project_data = json.load(f)
                
            # Check if MIDI file exists
            midi_path = project_data.get("midi_path")
            if not os.path.exists(midi_path):
                QMessageBox.warning(self, "MIDI Not Found", 
                                  f"The MIDI file from the project cannot be found:\n{midi_path}\n\n"
                                  "Please locate the file manually.")
                new_path, _ = QFileDialog.getOpenFileName(self, "Locate MIDI File", "", "MIDI (*.mid)")
                if not new_path:
                    return
                midi_path = new_path
                
            # Load the MIDI file
            self.midi_path = midi_path
            self.stop_all_threads()
            self.stop_audio()
            self.mixer.clear()
            
            # Load track info
            self.meta_processor = MidiProcessor(self.midi_path)
            self.meta_processor.track_info.connect(self.load_project_settings)
            self.meta_processor.start()
            
            # Store project data for later use
            self.pending_project_data = project_data
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project: {str(e)}")

    def load_project_settings(self, tracks):
        """Called after track info is loaded to apply project settings."""
        project_data = getattr(self, 'pending_project_data', None)
        if not project_data:
            return
            
        # Populate mixer with tracks
        self.mixer.populate(tracks)
        
        # Apply global settings
        self.playback_speed = project_data.get("playback_speed", 1.0)
        self.mixer.sld_speed.setValue(int(self.playback_speed * 100))
        
        self.chord_tolerance_ms = project_data.get("chord_tolerance_ms", 30)
        self.mixer.sld_tolerance.setValue(self.chord_tolerance_ms)
        
        self.mixer.spn_start_time.setValue(project_data.get("start_time", 0.0))
        self.mixer.spn_end_time.setValue(project_data.get("end_time", 10.0))
        
        remap_mode = project_data.get("remap_mode", "Hybrid")
        index = self.mixer.combo_remap.findText(remap_mode)
        if index >= 0:
            self.mixer.combo_remap.setCurrentIndex(index)
            
        self.mixer.chk_automap.setChecked(project_data.get("automap_enabled", False))
        
        # Apply global controls
        global_controls = project_data.get("global_controls", {})
        self.mixer.chk_enable_all.setChecked(global_controls.get("enable_all", True))
        self.mixer.sld_global_octave.setValue(global_controls.get("global_octave", 0))
        self.mixer.sld_global_semitone.setValue(global_controls.get("global_semitone", 0))
        self.mixer.sld_global_time.setValue(global_controls.get("global_time", 0))
        self.mixer.chk_global_reduce.setChecked(global_controls.get("global_reduce", False))
        
        # Apply track settings
        track_settings = project_data.get("track_settings", {})
        for cb, octave_slider, _, semitone_slider, _, reduce_cb, time_slider, _, ti in self.mixer.track_widgets:
            if ti in track_settings:
                settings = track_settings[ti]
                cb.setChecked(True)  # Enable the track if it has settings
                octave_slider.setValue(settings.get("octave_shift", 0))
                semitone_slider.setValue(settings.get("semitone_shift", 0))
                reduce_cb.setChecked(settings.get("reduce_to_root", False))
                time_slider.setValue(settings.get("time_shift", 0))
        
        # Load time ranges
        time_ranges = project_data.get("time_ranges", {})
        if time_ranges:
            self.mixer.track_time_ranges = time_ranges
        
        # Process notes with the new settings
        self.process_notes()
        
        # Clear pending project data
        self.pending_project_data = None
        
        QMessageBox.information(self, "Success", "Project loaded successfully")

    def closeEvent(self, event):
        self.stop_all_threads()
        if self.midi_player:
            self.midi_player.cleanup()
        print("[DEBUG] GUI closed cleanly.")
        event.accept()