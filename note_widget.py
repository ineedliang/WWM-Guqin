# ==========================================================
# note_widget.py — Full Piano Roll Visualization Widget (with Track Colors)
# ==========================================================

from PyQt6.QtWidgets import QFrame
from PyQt6.QtGui import QColor, QPainter, QBrush, QFont, QPen
from PyQt6.QtCore import Qt
from keyboard_map import MIN_MAPPED_NOTE, MAX_MAPPED_NOTE, midi_note_names

class NoteWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.notes = []  # List of (time, note_idx, key, mode, is_in_range, track_idx)
        self.track_colors = [] # List of QColor objects for each track
        self.total_duration = 0.1
        self.min_note = 12  # Default C1
        self.max_note = 96  # Default C8
        self.note_height = 10

    def load(self, viz_data, track_colors):
        # viz_data is the new list from the processor: (seconds, note_idx, key, mode, is_in_range, track_idx)
        self.notes = viz_data
        self.track_colors = track_colors
        if not viz_data:
            self.total_duration = 0.1
        else:
            self.total_duration = max(n[0] for n in viz_data)
        
        # --- MODIFIED: Force the display to the full C1-C8 range ---
        # C1 is MIDI note 12, C8 is MIDI note 96
        self.min_note = 12  # C1
        self.max_note = 96  # C8
        # -----------------------------------------------------------------

        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        W = self.width()
        H = self.height()
        
        num_lanes = self.max_note - self.min_note + 1
        if num_lanes <= 0:
            num_lanes = 1
        self.note_height = H / num_lanes

        # --- Draw background and lanes ---
        white_key_color = QColor(250, 250, 250)
        black_key_color = QColor(220, 220, 220)
        mappable_range_color = QColor(230, 255, 230) # Light green

        for i in range(num_lanes):
            note_num = self.max_note - i
            note_name = midi_note_names[note_num]
            
            # --- CORRECTED: Use the dynamic range from the keyboard map ---
            # This ensures the green area always matches the playable notes defined in keyboard_map.py
            if MIN_MAPPED_NOTE <= note_num <= MAX_MAPPED_NOTE:
                p.fillRect(0, int(i * self.note_height), W, int(self.note_height), QBrush(mappable_range_color))
            elif '#' in note_name:
                p.fillRect(0, int(i * self.note_height), W, int(self.note_height), QBrush(black_key_color))
            else:
                p.fillRect(0, int(i * self.note_height), W, int(self.note_height), QBrush(white_key_color))

            p.setPen(QPen(QColor(180, 180, 180), 1))
            p.drawLine(0, int(i * self.note_height), W, int(i * self.note_height))

        # --- Draw note names on the left ---
        p.setFont(QFont("Arial", 8))
        p.setPen(QPen(QColor(100, 100, 100), 1))
        for i in range(0, num_lanes, 2):
            note_num = self.max_note - i
            note_name = midi_note_names[note_num]
            p.drawText(2, int(i * self.note_height + self.note_height - 2), note_name)

        # --- Draw the notes ---
        for t, note_idx, _, _, is_in_range, track_idx in self.notes:
            y = (self.max_note - note_idx) * self.note_height
            
            if self.total_duration > 0:
                x = int((t / self.total_duration) * W)
            else:
                x = 0
            
            # Get the base color for the track
            track_color = self.track_colors[track_idx]
            
            # Set opacity based on whether the note is in range
            if is_in_range:
                note_color = QColor(track_color)
                note_color.setAlpha(200) # Opaque
            else:
                note_color = QColor(track_color)
                note_color.setAlpha(80) # Transparent
            
            p.fillRect(x, int(y), 5, int(self.note_height), QBrush(note_color))

        p.end()