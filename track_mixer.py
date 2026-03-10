# ==========================================================
# track_mixer.py — Right Sidebar Track Selector (with Global Controls)
# ==========================================================

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QCheckBox, 
                            QLabel, QPushButton, QSlider, QHBoxLayout, QComboBox, QDoubleSpinBox, QGroupBox, QDialog)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor

class TrackMixer(QWidget):
    # Signal to emit when track settings change
    settingsChanged = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        # REMOVED: Fixed width constraint to make the widget resizable
        # self.setFixedWidth(270)

        # Store tuples of (checkbox, octave_slider, octave_label, semitone_slider, semitone_label, reduce_cb, time_slider, time_label, track_index)
        self.track_widgets = []
        self.track_colors = [] # Store colors for each track

        # --- Track List ---
        self.list_area = QScrollArea()
        self.list_area.setWidgetResizable(True)
        
        self.inner = QWidget()
        self.inner_layout = QVBoxLayout(self.inner)
        self.list_area.setWidget(self.inner)

        self.layout.addWidget(QLabel("Track Mixer"))
        # MODIFIED: Added stretch factor to make the track list expand vertically
        self.layout.addWidget(self.list_area, 1)

        # --- Global Controls ---
        self.global_controls_group = QGroupBox("Global Controls")
        global_layout = QVBoxLayout()

        # Global Enable/Disable All
        global_enable_layout = QHBoxLayout()
        self.chk_enable_all = QCheckBox("Enable All Tracks")
        self.chk_enable_all.setChecked(True)
        self.chk_enable_all.stateChanged.connect(self.toggle_all_tracks)
        global_enable_layout.addWidget(self.chk_enable_all)
        global_layout.addLayout(global_enable_layout)
        
        # Auto-Fit Button
        auto_fit_layout = QHBoxLayout()
        self.btn_auto_fit = QPushButton("🎯 Auto-Fit Notes to Range")
        self.btn_auto_fit.clicked.connect(self.auto_fit_notes)
        self.btn_auto_fit.setToolTip(
            "Automatically adjust octave and semitone shifts to maximize playable notes.\n"
            "Finds the best global semitone shift, then optimizes each track's octave individually."
        )
        self.btn_auto_fit.setStyleSheet("font-weight: bold; padding: 8px;")
        auto_fit_layout.addWidget(self.btn_auto_fit)
        global_layout.addLayout(auto_fit_layout)
        
        # Auto-Disable Drums Button
        drums_layout = QHBoxLayout()
        self.btn_disable_drums = QPushButton("🥁 Auto-Disable Drums")
        self.btn_disable_drums.clicked.connect(self.auto_disable_drums)
        self.btn_disable_drums.setToolTip(
            "Automatically disable tracks that appear to be drums.\n"
            "Looks for keywords: 'drum', 'percussion', 'perc'"
        )
        drums_layout.addWidget(self.btn_disable_drums)
        global_layout.addLayout(drums_layout)

        # Remap Mode Dropdown
        global_layout.addWidget(QLabel("Remap Mode"))
        self.combo_remap = QComboBox()
        self.combo_remap.addItems(["Hybrid", "Simple", "Chord"])
        global_layout.addWidget(self.combo_remap)

        # Auto-Map Out of Range Checkbox
        self.chk_automap = QCheckBox("Auto-Map Out of Range Notes")
        self.chk_automap.setChecked(False)
        global_layout.addWidget(self.chk_automap)

        # Speed Control
        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("Playback Speed:"))
        self.sld_speed = QSlider(Qt.Orientation.Horizontal)
        self.sld_speed.setMinimum(25)
        self.sld_speed.setMaximum(200)
        self.sld_speed.setValue(100)
        self.sld_speed.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sld_speed.setTickInterval(25)
        self.lbl_speed = QLabel("1.00x")
        self.lbl_speed.setFixedWidth(40)
        speed_row.addWidget(self.sld_speed)
        speed_row.addWidget(self.lbl_speed)
        global_layout.addLayout(speed_row)

        # Chord Tolerance Control
        tolerance_row = QHBoxLayout()
        tolerance_row.addWidget(QLabel("Chord Tolerance:"))
        self.sld_tolerance = QSlider(Qt.Orientation.Horizontal)
        self.sld_tolerance.setMinimum(0)
        self.sld_tolerance.setMaximum(100)
        self.sld_tolerance.setValue(30)
        self.sld_tolerance.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sld_tolerance.setTickInterval(10)
        self.lbl_tolerance = QLabel("30ms")
        self.lbl_tolerance.setFixedWidth(40)
        tolerance_row.addWidget(self.sld_tolerance)
        tolerance_row.addWidget(self.lbl_tolerance)
        global_layout.addLayout(tolerance_row)

        # Global Octave Shift
        global_octave_layout = QHBoxLayout()
        global_octave_layout.addWidget(QLabel("Global Octave:"))
        self.sld_global_octave = QSlider(Qt.Orientation.Horizontal)
        self.sld_global_octave.setMinimum(-4)
        self.sld_global_octave.setMaximum(4)
        self.sld_global_octave.setValue(0)
        self.sld_global_octave.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sld_global_octave.setTickInterval(1)
        self.lbl_global_octave = QLabel("0")
        self.lbl_global_octave.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_global_octave.setFixedWidth(20)
        self.sld_global_octave.valueChanged.connect(lambda v: self.lbl_global_octave.setText(str(v)))
        global_octave_layout.addWidget(self.sld_global_octave)
        global_octave_layout.addWidget(self.lbl_global_octave)
        btn_apply_octave = QPushButton("Apply to All")
        btn_apply_octave.clicked.connect(self.apply_global_octave)
        global_octave_layout.addWidget(btn_apply_octave)
        global_layout.addLayout(global_octave_layout)

        # Global Semitone Shift
        global_semitone_layout = QHBoxLayout()
        global_semitone_layout.addWidget(QLabel("Global Semitone:"))
        self.sld_global_semitone = QSlider(Qt.Orientation.Horizontal)
        self.sld_global_semitone.setMinimum(-11)
        self.sld_global_semitone.setMaximum(11)
        self.sld_global_semitone.setValue(0)
        self.sld_global_semitone.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sld_global_semitone.setTickInterval(1)
        self.lbl_global_semitone = QLabel("0")
        self.lbl_global_semitone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_global_semitone.setFixedWidth(20)
        self.sld_global_semitone.valueChanged.connect(lambda v: self.lbl_global_semitone.setText(str(v)))
        global_semitone_layout.addWidget(self.sld_global_semitone)
        global_semitone_layout.addWidget(self.lbl_global_semitone)
        btn_apply_semitone = QPushButton("Apply to All")
        btn_apply_semitone.clicked.connect(self.apply_global_semitone)
        global_semitone_layout.addWidget(btn_apply_semitone)
        global_layout.addLayout(global_semitone_layout)

        # Global Time Shift
        global_time_layout = QHBoxLayout()
        global_time_layout.addWidget(QLabel("Global Time Shift:"))
        self.sld_global_time = QSlider(Qt.Orientation.Horizontal)
        self.sld_global_time.setMinimum(-300) # -5 minutes
        self.sld_global_time.setMaximum(300)  # +5 minutes
        self.sld_global_time.setValue(0)
        self.sld_global_time.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sld_global_time.setTickInterval(60) # Every minute
        self.lbl_global_time = QLabel("0.0s")
        self.lbl_global_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_global_time.setFixedWidth(55)
        self.sld_global_time.valueChanged.connect(lambda v: self.lbl_global_time.setText(f"{v:.1f}s"))
        global_time_layout.addWidget(self.sld_global_time)
        global_time_layout.addWidget(self.lbl_global_time)
        btn_apply_time = QPushButton("Apply to All")
        btn_apply_time.clicked.connect(self.apply_global_time)
        global_time_layout.addWidget(btn_apply_time)
        global_layout.addLayout(global_time_layout)

        # Global Reduce to Root
        global_reduce_layout = QHBoxLayout()
        self.chk_global_reduce = QCheckBox("Global Reduce to Root")
        self.chk_global_reduce.stateChanged.connect(self.apply_global_reduce)
        global_reduce_layout.addWidget(self.chk_global_reduce)
        global_layout.addLayout(global_reduce_layout)

        # Time Frame Selection
        time_frame_group = QHBoxLayout()
        time_frame_group.addWidget(QLabel("Time Frame (s):"))
        
        self.spn_start_time = QDoubleSpinBox()
        self.spn_start_time.setRange(0.0, 7200.0)  # Up to 2 hours
        self.spn_start_time.setSuffix(" s")
        self.spn_start_time.setValue(0.0)
        self.spn_start_time.setSingleStep(0.1)
        self.spn_start_time.setDecimals(1)
        time_frame_group.addWidget(self.spn_start_time)
        
        time_frame_group.addWidget(QLabel("to"))
        
        self.spn_end_time = QDoubleSpinBox()
        self.spn_end_time.setRange(0.1, 7200.0)  # Up to 2 hours
        self.spn_end_time.setSuffix(" s")
        self.spn_end_time.setValue(3600.0)  # Default to 1 hour instead of 10s
        self.spn_end_time.setSingleStep(0.1)
        self.spn_end_time.setDecimals(1)
        time_frame_group.addWidget(self.spn_end_time)

        global_layout.addLayout(time_frame_group)
        
        # Full song button with duration label
        full_song_layout = QHBoxLayout()
        self.btn_set_full_song = QPushButton("Set to Full Song")
        full_song_layout.addWidget(self.btn_set_full_song)
        
        self.lbl_song_duration = QLabel("Song: --:--")
        self.lbl_song_duration.setStyleSheet("font-weight: bold; color: #0066cc;")
        full_song_layout.addWidget(self.lbl_song_duration)
        full_song_layout.addStretch()
        
        global_layout.addLayout(full_song_layout)
        
        self.global_controls_group.setLayout(global_layout)
        self.layout.addWidget(self.global_controls_group)

        # NEW: Track Time Ranges Button
        self.btn_time_ranges = QPushButton("Set Track Time Ranges")
        self.btn_time_ranges.clicked.connect(self.open_time_ranges_dialog)
        self.layout.addWidget(self.btn_time_ranges)

        self.btn_apply = QPushButton("Apply Changes")
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        self.layout.addWidget(self.btn_apply)
        
        self.layout.addStretch()

    def generate_track_colors(self, num_tracks):
        """Generates a list of visually distinct colors for the tracks."""
        self.track_colors = []
        if num_tracks == 0:
            return
        
        # Generate hues across the spectrum
        for i in range(num_tracks):
            hue = int((i / num_tracks) * 360)
            # Use high saturation and value for vibrant colors
            color = QColor.fromHsv(hue, 200, 200)
            self.track_colors.append(color)

    def clear(self):
        """Clears all current widgets from the UI."""
        for i in reversed(range(self.inner_layout.count())):
            w = self.inner_layout.itemAt(i).widget()
            if w and w != self.btn_apply:
                w.deleteLater()
        self.track_widgets = []
        self.track_colors = []

    def populate(self, tracks):
        """Populates the mixer with new tracks."""
        self.clear()
        self.generate_track_colors(len(tracks))
        
        # Store track names for renaming
        self.track_names = {}
        
        for ti, name, count in tracks:
            track_widget = QWidget()
            track_layout = QVBoxLayout(track_widget)
            
            # Use the generated color for the track label
            color = self.track_colors[ti]
            
            # Check if track is likely drums (channel 10 or has "drum" in name)
            is_drums = "drum" in name.lower() or "percussion" in name.lower() or "perc" in name.lower()
            drum_marker = " 🥁" if is_drums else ""
            
            track_label = QLabel(f"Track {ti+1} — {name}{drum_marker} ({count})")
            track_label.setStyleSheet(f"color: {color.name()}; font-weight: bold;")
            track_label.setObjectName(f"track_label_{ti}")
            track_layout.addWidget(track_label)
            
            # Store original name
            self.track_names[ti] = name
            
            # Add rename button
            rename_layout = QHBoxLayout()
            cb = QCheckBox("Enabled")
            cb.setChecked(count > 0 and not is_drums)  # Auto-disable drums
            rename_layout.addWidget(cb)
            
            btn_rename = QPushButton("✏️")
            btn_rename.setMaximumWidth(30)
            btn_rename.setToolTip("Rename track")
            btn_rename.clicked.connect(lambda checked, idx=ti: self.rename_track(idx))
            rename_layout.addWidget(btn_rename)
            
            track_layout.addLayout(rename_layout)
            
            # Octave shift controls
            octave_layout = QHBoxLayout()
            octave_layout.addWidget(QLabel("Octave:"))
            octave_slider = QSlider()
            octave_slider.setMinimum(-4)
            octave_slider.setMaximum(4)
            octave_slider.setValue(0)
            octave_slider.setOrientation(Qt.Orientation.Horizontal)
            octave_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            octave_slider.setTickInterval(1)
            octave_value = QLabel("0")
            octave_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            octave_value.setFixedWidth(20)
            octave_slider.valueChanged.connect(lambda v, label=octave_value: label.setText(str(v)))
            octave_layout.addWidget(octave_slider)
            octave_layout.addWidget(octave_value)
            track_layout.addLayout(octave_layout)

            # NEW: Semitone shift controls
            semitone_layout = QHBoxLayout()
            semitone_layout.addWidget(QLabel("Semitone:"))
            semitone_slider = QSlider()
            semitone_slider.setMinimum(-11)
            semitone_slider.setMaximum(11)
            semitone_slider.setValue(0)
            semitone_slider.setOrientation(Qt.Orientation.Horizontal)
            semitone_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            semitone_slider.setTickInterval(1)
            semitone_value = QLabel("0")
            semitone_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            semitone_value.setFixedWidth(20)
            semitone_slider.valueChanged.connect(lambda v, label=semitone_value: label.setText(str(v)))
            semitone_layout.addWidget(semitone_slider)
            semitone_layout.addWidget(semitone_value)
            track_layout.addLayout(semitone_layout)

            # Chord reduction checkbox
            reduce_cb = QCheckBox("Reduce to Root Note")
            reduce_cb.setChecked(False)
            track_layout.addWidget(reduce_cb)

            # Time shift controls
            time_layout = QHBoxLayout()
            time_layout.addWidget(QLabel("Time Shift (s):"))
            time_slider = QSlider()
            time_slider.setMinimum(-300) # Represents -300.0s (-5 minutes)
            time_slider.setMaximum(300)  # Represents +300.0s (+5 minutes)
            time_slider.setValue(0)
            time_slider.setOrientation(Qt.Orientation.Horizontal)
            time_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
            time_slider.setTickInterval(60) # Ticks every 60 seconds (1 minute)
            time_value = QLabel("0.0s")
            time_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            time_value.setFixedWidth(55)
            time_slider.valueChanged.connect(lambda v, label=time_value: label.setText(f"{v:.1f}s"))
            time_layout.addWidget(time_slider)
            time_layout.addWidget(time_value)
            track_layout.addLayout(time_layout)
            
            line = QLabel("-" * 30)
            track_layout.addWidget(line)
            
            self.inner_layout.addWidget(track_widget)
            
            # Store the track widgets
            self.track_widgets.append((cb, octave_slider, octave_value, semitone_slider, semitone_value, reduce_cb, time_slider, time_value, ti))

        self.inner_layout.addStretch()
        
    def on_apply_clicked(self):
        """Emit the signal when the apply button is clicked."""
        self.settingsChanged.emit()

    def get_track_settings(self):
        """Returns a dictionary of track indices to their settings."""
        settings = {}
        for cb, octave_slider, _, semitone_slider, semitone_value, reduce_cb, time_slider, time_value, ti in self.track_widgets:
            # Process all tracks, not just the checked ones.
            is_active = cb.isChecked()
            
            if not any(cb.isChecked() for cb, _, _, _, _, _, _, _, _ in self.track_widgets):
                is_active = True

            if is_active:
                settings[ti] = {
                    'octave_shift': octave_slider.value(),
                    'semitone_shift': semitone_slider.value(),
                    'reduce_to_root': reduce_cb.isChecked(),
                    'time_shift': time_slider.value() / 1.0
                }
        return settings

    # --- NEW: Global Control Methods ---
    def toggle_all_tracks(self, state):
        """Enable or disable all tracks based on the global checkbox state."""
        is_checked = state == Qt.CheckState.Checked.value
        for cb, _, _, _, _, _, _, _, _ in self.track_widgets:
            cb.setChecked(is_checked)
        self.settingsChanged.emit()

    def apply_global_octave(self):
        """Apply the global octave shift to all tracks."""
        value = self.sld_global_octave.value()
        for _, octave_slider, _, _, _, _, _, _, _ in self.track_widgets:
            octave_slider.setValue(value)
        self.settingsChanged.emit()

    def apply_global_semitone(self):
        """Apply the global semitone shift to all tracks."""
        value = self.sld_global_semitone.value()
        for _, _, _, semitone_slider, _, _, _, _, _ in self.track_widgets:
            semitone_slider.setValue(value)
        self.settingsChanged.emit()

    def apply_global_time(self):
        """Apply the global time shift to all tracks."""
        value = self.sld_global_time.value()
        for _, _, _, _, _, _, time_slider, _, _ in self.track_widgets:
            time_slider.setValue(value)
        self.settingsChanged.emit()

    def apply_global_reduce(self, state):
        """Apply the global reduce to root setting to all tracks."""
        is_checked = state == Qt.CheckState.Checked.value
        for _, _, _, _, _, reduce_cb, _, _, _ in self.track_widgets:
            reduce_cb.setChecked(is_checked)
        self.settingsChanged.emit()

    # --- NEW: Track Time Ranges Method ---
    def open_time_ranges_dialog(self):
        """Open the dialog to set time ranges for each track."""
        # Import here to avoid circular imports
        from track_time_dialog import TrackTimeDialog
        
        # Get current track info
        track_info = []
        for cb, _, _, _, _, _, _, _, ti in self.track_widgets:
            # Get the track name from the label
            label = self.inner_layout.itemAt(ti).widget().findChild(QLabel)
            name = label.text().split(" — ")[1].rsplit(" (", 1)[0] if label else f"Track {ti+1}"
            
            # Get the note count
            count = 0
            if label:
                count_str = label.text().rsplit(" (", 1)[1].rstrip(")")
                try:
                    count = int(count_str)
                except:
                    pass
            
            track_info.append((ti, name, count))
        
        # Create and show dialog
        dialog = TrackTimeDialog(track_info, getattr(self, 'track_time_ranges', {}), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.track_time_ranges = dialog.get_time_ranges()
            self.settingsChanged.emit()
    
    def rename_track(self, track_idx):
        """Allow user to rename a track."""
        from PyQt6.QtWidgets import QInputDialog
        
        current_name = self.track_names.get(track_idx, f"Track {track_idx+1}")
        
        new_name, ok = QInputDialog.getText(
            self, 
            "Rename Track",
            f"Enter new name for Track {track_idx+1}:",
            text=current_name
        )
        
        if ok and new_name:
            self.track_names[track_idx] = new_name
            
            # Update the label
            for cb, _, _, _, _, _, _, _, ti in self.track_widgets:
                if ti == track_idx:
                    # Find the label widget
                    label = self.inner_layout.itemAt(track_idx).widget().findChild(QLabel, f"track_label_{ti}")
                    if label:
                        # Get note count from current label
                        old_text = label.text()
                        count_part = old_text.split("(")[-1].rstrip(")")
                        
                        # Check if it's marked as drums
                        is_drums = "🥁" in old_text
                        drum_marker = " 🥁" if is_drums else ""
                        
                        color = self.track_colors[ti]
                        label.setText(f"Track {ti+1} — {new_name}{drum_marker} ({count_part})")
                        label.setStyleSheet(f"color: {color.name()}; font-weight: bold;")
                    break
    
    def auto_disable_drums(self):
        """Automatically disable tracks that appear to be drums."""
        from PyQt6.QtWidgets import QMessageBox
        
        disabled_count = 0
        
        for cb, _, _, _, _, _, _, _, ti in self.track_widgets:
            # Find the label
            label = self.inner_layout.itemAt(ti).widget().findChild(QLabel, f"track_label_{ti}")
            if label and "🥁" in label.text():
                if cb.isChecked():
                    cb.setChecked(False)
                    disabled_count += 1
        
        if disabled_count > 0:
            QMessageBox.information(
                self,
                "Drums Disabled", 
                f"Automatically disabled {disabled_count} drum track(s).\n\n"
                "Drum tracks are detected by name keywords:\n"
                "'drum', 'percussion', 'perc'\n\n"
                "You can re-enable them manually if needed."
            )
            self.settingsChanged.emit()
        else:
            QMessageBox.information(self, "No Drums Found", "No drum tracks were detected.")
    
    def auto_fit_notes(self):
        """Ultra-smart auto-fit that avoids unmappable sharps/flats."""
        from PyQt6.QtWidgets import QMessageBox
        
        if not hasattr(self, 'raw_track_notes') or not self.raw_track_notes:
            QMessageBox.warning(self, "No Data", 
                "Please load a MIDI file first.\n"
                "Auto-fit needs note data to analyze.")
            return
        
        from keyboard_map import midi_note_names, note_to_key, MIN_MAPPED_NOTE, MAX_MAPPED_NOTE
        
        # Get enabled tracks
        enabled_tracks = []
        for cb, octave_slider, _, semitone_slider, _, _, _, _, ti in self.track_widgets:
            if cb.isChecked() and ti in self.raw_track_notes:
                enabled_tracks.append(ti)
        
        if not enabled_tracks:
            QMessageBox.warning(self, "No Tracks", "Please enable at least one track.")
            return
        
        print("[Auto-Fit] ============ ULTRA-SMART AUTO-FIT v3 ============")
        
        # Collect notes
        all_notes = []
        track_note_ranges = {}
        
        for ti in enabled_tracks:
            track_notes = self.raw_track_notes[ti]
            all_notes.extend(track_notes)
            if track_notes:
                track_note_ranges[ti] = (min(track_notes), max(track_notes))
        
        if not all_notes:
            QMessageBox.warning(self, "No Notes", "No notes found.")
            return
        
        # STEP 1: WEIGHTED SEMITONE SCORING
        # Prefer semitones that maximize MAPPABLE notes (not just in-range)
        print("[Auto-Fit] Testing semitone shifts with weighted scoring...")
        
        best_semitone = 0
        best_score = -999999
        semitone_results = []
        
        for semitone in range(-11, 12):
            mappable_count = 0
            unmappable_count = 0
            natural_count = 0
            
            for note in all_notes:
                shifted = note + semitone
                
                if MIN_MAPPED_NOTE <= shifted <= MAX_MAPPED_NOTE:
                    try:
                        note_name = midi_note_names[shifted]
                        
                        if note_name in note_to_key:
                            mappable_count += 1
                            # Bonus for natural notes (no sharps/flats)
                            if '#' not in note_name and 'b' not in note_name:
                                natural_count += 1
                        else:
                            # HEAVY PENALTY for unmappable notes in range
                            unmappable_count += 1
                    except:
                        pass
            
            # Weighted scoring:
            # +10 per mappable note
            # +2 bonus per natural note
            # -50 penalty per unmappable note (HEAVY!)
            score = (mappable_count * 10) + (natural_count * 2) - (unmappable_count * 50)
            
            semitone_results.append((semitone, score, mappable_count, unmappable_count))
            
            if score > best_score:
                best_score = score
                best_semitone = semitone
        
        # Show top 3 candidates
        semitone_results.sort(key=lambda x: x[1], reverse=True)
        print("[Auto-Fit] Top 3 semitone candidates:")
        for sem, score, mapp, unmapp in semitone_results[:3]:
            print(f"  {sem:+3d}: score={score:6d}, mappable={mapp:4d}, unmappable={unmapp:4d}")
        
        print(f"[Auto-Fit] ✅ Selected semitone: {best_semitone:+d}")
        
        # STEP 2: TEST IF REDUCE-TO-ROOT HELPS
        # Count unique notes vs total notes
        unique_notes = len(set(all_notes))
        total_notes = len(all_notes)
        
        # If there's significant chord activity (many duplicate notes)
        use_reduce = (unique_notes / total_notes) < 0.7
        
        print(f"[Auto-Fit] Chord analysis: {unique_notes} unique / {total_notes} total")
        print(f"[Auto-Fit] Reduce to root: {'YES' if use_reduce else 'NO'}")
        
        # STEP 3: SMART PER-TRACK OCTAVE OPTIMIZATION
        print("[Auto-Fit] Optimizing octave for each track...")
        
        track_adjustments = {}
        
        for ti in enabled_tracks:
            track_notes = self.raw_track_notes[ti]
            if not track_notes:
                continue
            
            best_octave = 0
            best_octave_score = -999999
            octave_results = []
            
            for octave in range(-4, 5):
                mappable = 0
                unmappable = 0
                natural = 0
                
                for note in track_notes:
                    shifted = note + best_semitone + (octave * 12)
                    
                    if MIN_MAPPED_NOTE <= shifted <= MAX_MAPPED_NOTE:
                        try:
                            note_name = midi_note_names[shifted]
                            if note_name in note_to_key:
                                mappable += 1
                                if '#' not in note_name and 'b' not in note_name:
                                    natural += 1
                            else:
                                unmappable += 1
                        except:
                            pass
                
                # Same weighted scoring
                score = (mappable * 10) + (natural * 2) - (unmappable * 50)
                octave_results.append((octave, score, mappable, unmappable))
                
                if score > best_octave_score:
                    best_octave_score = score
                    best_octave = octave
            
            track_adjustments[ti] = (best_octave, mappable, len(track_notes), unmappable)
            
            # Show top 2 for this track
            octave_results.sort(key=lambda x: x[1], reverse=True)
            print(f"  Track {ti+1}: {best_octave:+d} oct (mappable={mappable}/{len(track_notes)}, unmappable={unmappable})")
        
        # APPLY SETTINGS
        self.sld_global_semitone.setValue(best_semitone)
        self.chk_global_reduce.setChecked(use_reduce)
        
        for cb, octave_slider, _, semitone_slider, _, reduce_cb, _, _, ti in self.track_widgets:
            if ti in track_adjustments:
                octave_shift, mappable, total, unmappable = track_adjustments[ti]
                octave_slider.setValue(octave_shift)
                semitone_slider.setValue(best_semitone)
                reduce_cb.setChecked(use_reduce)
        
        # CALCULATE FINAL RESULTS
        total_notes = len(all_notes)
        total_mappable = sum(mappable for _, mappable, _, _ in track_adjustments.values())
        total_unmappable = sum(unmappable for _, _, _, unmappable in track_adjustments.values())
        fit_percentage = (total_mappable / total_notes * 100) if total_notes > 0 else 0
        
        # BUILD RESULT MESSAGE
        result_msg = "✅ Ultra-Smart Auto-Fit Complete!\n\n"
        result_msg += f"🎵 Global Semitone: {best_semitone:+d}\n"
        result_msg += f"🎹 Reduce to Root: {'Enabled' if use_reduce else 'Disabled'}\n\n"
        result_msg += "📊 Per-Track Results:\n"
        
        for ti, (octave, mappable, total, unmappable) in sorted(track_adjustments.items()):
            pct = (mappable / total * 100) if total > 0 else 0
            status = "✅" if unmappable == 0 else "⚠️"
            result_msg += f"  {status} Track {ti+1}: {octave:+d} oct → {mappable}/{total} ({pct:.0f}%)"
            if unmappable > 0:
                result_msg += f" ⚠️ {unmappable} unmappable!"
            result_msg += "\n"
        
        result_msg += f"\n📈 TOTAL: {total_mappable}/{total_notes} mappable ({fit_percentage:.1f}%)\n"
        
        if total_unmappable > 0:
            result_msg += f"\n⚠️ WARNING: {total_unmappable} notes will land on missing sharps/flats!\n"
            result_msg += "💡 Try enabling 'Auto-Map Out of Range' or '21-Key Mode'\n"
        else:
            result_msg += "\n🎉 Perfect! All notes are mappable!\n"
        
        QMessageBox.information(self, "Auto-Fit Results", result_msg)
        
        self.settingsChanged.emit()