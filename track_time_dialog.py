# Create a new file called track_time_dialog.py:

# ==========================================================
# track_time_dialog.py — Dialog for managing track time ranges
# ==========================================================

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QTableWidget, QTableWidgetItem, QDoubleSpinBox,
                            QHeaderView, QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt

class TrackTimeDialog(QDialog):
    def __init__(self, track_info, time_ranges=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Track Time Ranges")
        self.resize(600, 400)
        
        self.track_info = track_info  # List of (track_index, name, note_count)
        self.time_ranges = time_ranges or {}  # Dict of track_index to list of (start, end) tuples
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("Set time ranges for each track. Tracks will only play during their enabled ranges.")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Table for time ranges
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Track", "Start Time (s)", "End Time (s)", "Actions"])
        
        # Make the table fill the dialog
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.table)
        
        # Populate table with track info
        self.populate_table()
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def populate_table(self):
        self.table.setRowCount(len(self.track_info))
        
        for row, (track_idx, name, count) in enumerate(self.track_info):
            # Track name
            self.table.setItem(row, 0, QTableWidgetItem(f"Track {track_idx+1} — {name} ({count})"))
            
            # Get existing time ranges for this track
            ranges = self.time_ranges.get(track_idx, [])
            
            # Create a container widget for the time ranges
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            
            # Add existing ranges
            for start, end in ranges:
                range_layout = QHBoxLayout()
                
                start_spin = QDoubleSpinBox()
                start_spin.setRange(0.0, 999.0)
                start_spin.setDecimals(1)
                start_spin.setValue(start)
                
                end_spin = QDoubleSpinBox()
                end_spin.setRange(0.0, 999.0)
                end_spin.setDecimals(1)
                end_spin.setValue(end)
                
                remove_btn = QPushButton("Remove")
                remove_btn.clicked.connect(lambda _, r=row, i=ranges.index((start, end)): self.remove_range(r, i))
                
                range_layout.addWidget(QLabel("Start:"))
                range_layout.addWidget(start_spin)
                range_layout.addWidget(QLabel("End:"))
                range_layout.addWidget(end_spin)
                range_layout.addWidget(remove_btn)
                
                container_layout.addLayout(range_layout)
            
            # Add button to add new range
            add_btn = QPushButton("Add Time Range")
            add_btn.clicked.connect(lambda _, r=row: self.add_range(r))
            container_layout.addWidget(add_btn)
            
            # Set the cell widget
            self.table.setCellWidget(row, 1, container)
            
            # Store the spinboxes for later retrieval
            self.table.setItem(row, 2, QTableWidgetItem(""))  # Placeholder
            self.table.setItem(row, 3, QTableWidgetItem(""))  # Placeholder
    
    def add_range(self, row):
        container = self.table.cellWidget(row, 1)
        layout = container.layout()
        
        # Create new range widgets
        range_layout = QHBoxLayout()
        
        start_spin = QDoubleSpinBox()
        start_spin.setRange(0.0, 999.0)
        start_spin.setDecimals(1)
        start_spin.setValue(0.0)
        
        end_spin = QDoubleSpinBox()
        end_spin.setRange(0.0, 999.0)
        end_spin.setDecimals(1)
        end_spin.setValue(10.0)
        
        # Find the current number of ranges to use as index
        count = layout.count() - 1  # Subtract 1 for the "Add" button
        
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda _, r=row, i=count: self.remove_range(r, i))
        
        range_layout.addWidget(QLabel("Start:"))
        range_layout.addWidget(start_spin)
        range_layout.addWidget(QLabel("End:"))
        range_layout.addWidget(end_spin)
        range_layout.addWidget(remove_btn)
        
        # Insert before the "Add" button
        layout.insertLayout(layout.count() - 1, range_layout)
    
    def remove_range(self, row, index):
        container = self.table.cellWidget(row, 1)
        layout = container.layout()
        
        # Remove the layout item at the specified index
        item = layout.itemAt(index)
        if item:
            widget = item.widget()
            if widget:
                widget.deleteLater()
            layout.removeItem(item)
    
    def get_time_ranges(self):
        """Extract the time ranges from the table."""
        time_ranges = {}
        
        for row, (track_idx, _, _) in enumerate(self.track_info):
            container = self.table.cellWidget(row, 1)
            layout = container.layout()
            
            ranges = []
            # Iterate through all layouts except the last one (which is the "Add" button)
            for i in range(layout.count() - 1):
                item = layout.itemAt(i)
                if item and item.layout():
                    # Get the spinboxes from the layout
                    start_spin = None
                    end_spin = None
                    
                    for j in range(item.layout().count()):
                        widget = item.layout().itemAt(j).widget()
                        if isinstance(widget, QDoubleSpinBox):
                            if start_spin is None:
                                start_spin = widget
                            else:
                                end_spin = widget
                    
                    if start_spin and end_spin:
                        start = start_spin.value()
                        end = end_spin.value()
                        if start < end:
                            ranges.append((start, end))
            
            if ranges:
                time_ranges[track_idx] = ranges
        
        return time_ranges