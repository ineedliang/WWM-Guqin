# ==========================================================
# note_widget_v2.py — Interactive Piano Roll with Note Editing
# ==========================================================

from PyQt6.QtWidgets import QFrame, QMenu
from PyQt6.QtGui import QColor, QPainter, QBrush, QFont, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from keyboard_map import MIN_MAPPED_NOTE, MAX_MAPPED_NOTE, midi_note_names, note_to_key

class NoteWidget(QFrame):
    """Enhanced piano roll with interactive note editing and better visual feedback."""
    
    noteDeleted = pyqtSignal(int)  # Emits index of deleted note
    noteMoved = pyqtSignal(int, float, int)  # Emits index, new_time, new_note
    playheadPosition = pyqtSignal(float)  # Current playback position
    
    def __init__(self):
        super().__init__()
        self.notes = []  # List of (time, note_idx, key, mode, is_in_range, track_idx)
        self.track_colors = []
        self.total_duration = 0.1
        self.min_note = 12  # C1
        self.max_note = 96  # C8
        self.note_height = 10
        self.playhead_pos = 0.0  # Current playback position
        self.selected_note_idx = None
        self.dragging_note = False
        self.drag_start_pos = None
        
        # Enable mouse tracking and context menu
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def load(self, viz_data, track_colors):
        """Load visualization data and track colors."""
        self.notes = list(viz_data)  # Make a copy so we can modify it
        self.track_colors = track_colors
        if not viz_data:
            self.total_duration = 0.1
        else:
            self.total_duration = max(n[0] for n in viz_data)
        
        self.min_note = 12  # C1
        self.max_note = 96  # C8
        self.update()

    def set_playhead(self, position):
        """Update playhead position for real-time visualization."""
        self.playhead_pos = position
        self.update()

    def get_note_at_position(self, pos):
        """Find note index at mouse position."""
        W = self.width()
        H = self.height()
        num_lanes = self.max_note - self.min_note + 1
        if num_lanes <= 0:
            return None
        
        note_height = H / num_lanes
        
        for idx, (t, note_idx, _, _, _, _) in enumerate(self.notes):
            y = (self.max_note - note_idx) * note_height
            x = int((t / self.total_duration) * W) if self.total_duration > 0 else 0
            
            # Check if click is within note bounds (with some tolerance)
            if (x - 3 <= pos.x() <= x + 8 and 
                y <= pos.y() <= y + note_height):
                return idx
        
        return None

    def mousePressEvent(self, event):
        """Handle mouse press for note selection and dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            note_idx = self.get_note_at_position(event.pos())
            if note_idx is not None:
                self.selected_note_idx = note_idx
                self.dragging_note = True
                self.drag_start_pos = event.pos()
                self.update()

    def mouseMoveEvent(self, event):
        """Handle mouse move for note dragging."""
        if self.dragging_note and self.selected_note_idx is not None:
            # Calculate new position
            W = self.width()
            H = self.height()
            num_lanes = self.max_note - self.min_note + 1
            note_height = H / num_lanes
            
            # Calculate new time
            new_time = (event.pos().x() / W) * self.total_duration
            new_time = max(0, min(new_time, self.total_duration))
            
            # Calculate new note
            lane = int(event.pos().y() / note_height)
            new_note = self.max_note - lane
            new_note = max(self.min_note, min(new_note, self.max_note))
            
            # Update the note
            old_note = self.notes[self.selected_note_idx]
            self.notes[self.selected_note_idx] = (
                new_time, new_note, old_note[2], old_note[3], 
                MIN_MAPPED_NOTE <= new_note <= MAX_MAPPED_NOTE, 
                old_note[5]
            )
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to finalize note movement."""
        if self.dragging_note and self.selected_note_idx is not None:
            note = self.notes[self.selected_note_idx]
            self.noteMoved.emit(self.selected_note_idx, note[0], note[1])
            self.dragging_note = False
            self.drag_start_pos = None

    def show_context_menu(self, pos):
        """Show context menu for note operations."""
        note_idx = self.get_note_at_position(pos)
        if note_idx is None:
            return
        
        self.selected_note_idx = note_idx
        note = self.notes[note_idx]
        
        menu = QMenu(self)
        
        # Note info
        note_name = midi_note_names[note[1]] if 0 <= note[1] < len(midi_note_names) else "Unknown"
        info_action = menu.addAction(f"Note: {note_name} at {note[0]:.2f}s")
        info_action.setEnabled(False)
        
        menu.addSeparator()
        
        # Check if note is mappable
        if note[4]:  # is_in_range
            key, mode = note[2], note[3]
            if key and mode:
                key_info = menu.addAction(f"Maps to: {key.upper()} ({mode})")
                key_info.setEnabled(False)
        else:
            unmapped_action = menu.addAction("⚠ Note not mappable")
            unmapped_action.setEnabled(False)
        
        menu.addSeparator()
        
        # Actions
        delete_action = menu.addAction("Delete Note")
        delete_action.triggered.connect(lambda: self.delete_note(note_idx))
        
        menu.exec(self.mapToGlobal(pos))

    def delete_note(self, idx):
        """Delete a note by index."""
        if 0 <= idx < len(self.notes):
            del self.notes[idx]
            self.noteDeleted.emit(idx)
            self.selected_note_idx = None
            self.update()

    def paintEvent(self, e):
        """Paint the piano roll with enhanced visual feedback."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        W = self.width()
        H = self.height()
        
        num_lanes = self.max_note - self.min_note + 1
        if num_lanes <= 0:
            num_lanes = 1
        self.note_height = H / num_lanes

        # Draw background and lanes
        white_key_color = QColor(250, 250, 250)
        black_key_color = QColor(220, 220, 220)
        mappable_range_color = QColor(230, 255, 230)  # Light green
        unmappable_highlight = QColor(255, 230, 230)  # Light red for sharps/flats not in map

        for i in range(num_lanes):
            note_num = self.max_note - i
            note_name = midi_note_names[note_num] if 0 <= note_num < len(midi_note_names) else ""
            
            # Check if this note is in the mappable range
            if MIN_MAPPED_NOTE <= note_num <= MAX_MAPPED_NOTE:
                # Check if this specific note has a mapping
                if note_name in note_to_key:
                    p.fillRect(0, int(i * self.note_height), W, int(self.note_height), QBrush(mappable_range_color))
                else:
                    # In range but not mapped (missing sharp/flat)
                    p.fillRect(0, int(i * self.note_height), W, int(self.note_height), QBrush(unmappable_highlight))
            elif '#' in note_name or 'b' in note_name:
                p.fillRect(0, int(i * self.note_height), W, int(self.note_height), QBrush(black_key_color))
            else:
                p.fillRect(0, int(i * self.note_height), W, int(self.note_height), QBrush(white_key_color))

            p.setPen(QPen(QColor(180, 180, 180), 1))
            p.drawLine(0, int(i * self.note_height), W, int(i * self.note_height))

        # Draw note names on the left
        p.setFont(QFont("Arial", 8))
        p.setPen(QPen(QColor(100, 100, 100), 1))
        for i in range(0, num_lanes, 2):
            note_num = self.max_note - i
            if 0 <= note_num < len(midi_note_names):
                note_name = midi_note_names[note_num]
                p.drawText(2, int(i * self.note_height + self.note_height - 2), note_name)

        # Draw the notes
        for idx, (t, note_idx, key, mode, is_in_range, track_idx) in enumerate(self.notes):
            y = (self.max_note - note_idx) * self.note_height
            
            if self.total_duration > 0:
                x = int((t / self.total_duration) * W)
            else:
                x = 0
            
            # Get the base color for the track
            track_color = self.track_colors[track_idx] if track_idx < len(self.track_colors) else QColor(100, 100, 200)
            
            # Visual feedback for different note states
            if idx == self.selected_note_idx:
                # Highlight selected note
                note_color = QColor(255, 200, 0)
                note_color.setAlpha(255)
                note_width = 8
            elif is_in_range and key and mode:
                # Mappable note - full opacity
                note_color = QColor(track_color)
                note_color.setAlpha(200)
                note_width = 5
            elif is_in_range and not key:
                # In range but missing sharp/flat - red outline
                note_color = QColor(255, 100, 100)
                note_color.setAlpha(200)
                note_width = 5
            else:
                # Out of range - transparent
                note_color = QColor(track_color)
                note_color.setAlpha(80)
                note_width = 5
            
            p.fillRect(x, int(y), note_width, int(self.note_height), QBrush(note_color))
            
            # Draw warning icon for unmappable notes
            if is_in_range and not key:
                p.setPen(QPen(QColor(255, 0, 0), 2))
                p.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                p.drawText(x + note_width + 2, int(y + self.note_height - 2), "⚠")

        # Draw playhead
        if self.playhead_pos > 0 and self.total_duration > 0:
            playhead_x = int((self.playhead_pos / self.total_duration) * W)
            p.setPen(QPen(QColor(255, 0, 0), 2))
            p.drawLine(playhead_x, 0, playhead_x, H)

        p.end()
