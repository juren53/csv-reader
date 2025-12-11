#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CSV Reader Application

A PyQt6-based application to view CSV files with data displayed vertically.
Features:
- Display CSV records vertically with header as labels
- Navigate records using left/right arrow keys
- Recent files menu
- Zoom functionality with Ctrl + mouse wheel
"""

import sys
import os
import csv
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QGridLayout, QLabel, QScrollArea, 
                           QFileDialog, QMessageBox, QMenu, QSizePolicy,
                           QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt, QSettings, QSize, QEvent
from PyQt6.QtGui import QFont, QKeySequence, QFontMetrics, QPalette, QAction

class TableView(QTableWidget):
    """Widget to display CSV data in a spreadsheet-like table format"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configure table properties
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Read-only
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setWordWrap(True)
        
        # Enable scrolling
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        
        # Configure headers
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setDefaultSectionSize(25)
        self.verticalHeader().setVisible(True)
        
        # Default font settings
        self.base_font_size = 10
        self.current_zoom_level = 100  # 100%
        self.updateFontSize()
        
        # Enable sorting
        self.setSortingEnabled(True)
        
    def updateFontSize(self):
        """Update the font size based on the current zoom level"""
        font_size = int(self.base_font_size * (self.current_zoom_level / 100))
        font = QFont()
        font.setPointSize(max(6, font_size))  # Ensure minimum readable size
        self.setFont(font)
        
        # Update row heights to match font
        self.verticalHeader().setDefaultSectionSize(max(25, font_size + 10))
        
    def zoom(self, delta):
        """Change zoom level by a percentage"""
        # Adjust zoom level with limits (40% to 300%)
        new_zoom = max(40, min(300, self.current_zoom_level + delta))
        if new_zoom != self.current_zoom_level:
            self.current_zoom_level = new_zoom
            print(f"Zoom level changed to {self.current_zoom_level}%")  # Debug output
            self.updateFontSize()
            return True
        return False
        
    def displayData(self, headers, data):
        """Display CSV data in the table"""
        if not headers or not data:
            self.clear()
            return
            
        # Set table dimensions
        self.setRowCount(len(data))
        self.setColumnCount(len(headers))
        
        # Set headers
        self.setHorizontalHeaderLabels(headers)
        
        # Populate table with data
        for row_idx, row_data in enumerate(data):
            # Ensure row has enough columns
            if len(row_data) < len(headers):
                row_data = row_data + [''] * (len(headers) - len(row_data))
                
            for col_idx, cell_value in enumerate(row_data):
                item = QTableWidgetItem(str(cell_value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                self.setItem(row_idx, col_idx, item)
        
        # Resize columns to content
        self.resizeColumnsToContents()
        
        # Update font size
        self.updateFontSize()

class RecordView(QScrollArea):
    """Widget to display a single CSV record vertically"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.setWidget(self.container)
        self.setWidgetResizable(True)
        
        # Set up the widget appearance
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Default font settings
        self.base_font_size = 10
        self.current_zoom_level = 100  # 100%
        self.updateFontSize()
        
        # Styling
        self.label_style = "font-weight: bold; padding-right: 10px;"

    def updateFontSize(self):
        """Update the font size based on the current zoom level"""
        font_size = int(self.base_font_size * (self.current_zoom_level / 100))
        font = QFont()
        font.setPointSize(max(6, font_size))  # Ensure minimum readable size
        
        # Apply font to all labels
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i).widget()
            if isinstance(item, QLabel):
                item.setFont(font)
                
        # Update the container to reflect the changes
        self.container.adjustSize()
        self.container.update()  # Force a visual update

    def zoom(self, delta):
        """Change zoom level by a percentage"""
        # Adjust zoom level with limits (40% to 300%)
        new_zoom = max(40, min(300, self.current_zoom_level + delta))
        if new_zoom != self.current_zoom_level:
            self.current_zoom_level = new_zoom
            print(f"Zoom level changed to {self.current_zoom_level}%")  # Debug output
            self.updateFontSize()
            # Force the scroll area to refresh
            self.setWidgetResizable(False)
            self.setWidgetResizable(True)
            return True
        return False
        
    def displayRecord(self, headers, record):
        """Display a record with headers as labels"""
        # Clear previous content
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        if not headers or not record:
            return
            
        # Display each field with its header
        for row, (header, value) in enumerate(zip(headers, record)):
            # Create label for header
            header_label = QLabel(header)
            header_label.setStyleSheet(self.label_style)
            header_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            
            # Create label for value
            value_label = QLabel(value)
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value_label.setWordWrap(True)
            value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            
            # Add to layout
            self.grid_layout.addWidget(header_label, row, 0)
            self.grid_layout.addWidget(value_label, row, 1)
            
        # Set column stretch
        self.grid_layout.setColumnStretch(0, 0)  # Header column
        self.grid_layout.setColumnStretch(1, 1)  # Value column
        
        # Update font size
        self.updateFontSize()

class CSVReaderApp(QMainWindow):
    """Main application window for CSV Reader"""
    
    MAX_RECENT_FILES = 10
    VERSION = "v0.0.1  2025-12-11  03:05"
    
    def __init__(self):
        super().__init__()
        
        # Application settings
        self.settings = QSettings("CSVReader", "csv-reader")
        
        # Initialize data structures
        self.csv_data = []
        self.headers = []
        self.current_record_index = 0
        self.current_file_path = None
        self.current_view_mode = "record"  # "record" or "table"
        
        # Set up the UI
        self.initUI()
        
        # Load recent files list
        self.updateRecentFilesMenu()
        
        # Install event filter for key events at application level
        QApplication.instance().installEventFilter(self)
        
        # Load the last viewed file if it exists
        self.loadLastViewedFile()
    
    def initUI(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("CSV Reader")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Create view toggle controls
        view_controls_layout = QHBoxLayout()
        
        # View mode buttons
        from PyQt6.QtWidgets import QPushButton
        self.record_view_btn = QPushButton("Record View")
        self.record_view_btn.setCheckable(True)
        self.record_view_btn.setChecked(True)
        self.record_view_btn.clicked.connect(self.switchToRecordView)
        
        self.table_view_btn = QPushButton("Table View")
        self.table_view_btn.setCheckable(True)
        self.table_view_btn.setChecked(False)
        self.table_view_btn.clicked.connect(self.switchToTableView)
        
        view_controls_layout.addWidget(self.record_view_btn)
        view_controls_layout.addWidget(self.table_view_btn)
        view_controls_layout.addStretch()
        
        main_layout.addLayout(view_controls_layout)
        
        # Create views container
        self.views_container = QWidget()
        self.views_layout = QVBoxLayout(self.views_container)
        
        # Create both views
        self.record_view = RecordView()
        self.table_view = TableView()
        
        # Connect table row click to record view
        self.table_view.cellClicked.connect(self.onTableCellClicked)
        
        # Initially show only record view
        self.views_layout.addWidget(self.record_view)
        self.views_layout.addWidget(self.table_view)
        self.table_view.hide()
        
        main_layout.addWidget(self.views_container)
        
        # Add navigation controls (only for record view)
        self.nav_widget = QWidget()
        nav_layout = QHBoxLayout(self.nav_widget)
        
        prev_btn_widget = QPushButton("< Previous")
        prev_btn_widget.clicked.connect(self.previousRecord)
        
        next_btn_widget = QPushButton("Next >")
        next_btn_widget.clicked.connect(self.nextRecord)
        
        nav_layout.addWidget(prev_btn_widget)
        
        # Add navigation info label
        self.nav_label = QLabel("No file loaded")
        self.nav_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.nav_label)
        
        nav_layout.addWidget(next_btn_widget)
        main_layout.addWidget(self.nav_widget)
        
        self.setCentralWidget(central_widget)
        
        # Create menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Open action
        open_action = QAction('&Open...', self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.openFile)
        file_menu.addAction(open_action)
        
        # Recent files submenu
        self.recent_files_menu = QMenu('&Recent Files', self)
        file_menu.addMenu(self.recent_files_menu)
        
        # Separator
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('&View')
        
        # Record view action
        record_view_action = QAction('&Record View', self)
        record_view_action.setCheckable(True)
        record_view_action.setChecked(True)
        record_view_action.setShortcut(QKeySequence('F1'))
        record_view_action.triggered.connect(self.switchToRecordView)
        view_menu.addAction(record_view_action)
        self.record_view_action = record_view_action
        
        # Table view action
        table_view_action = QAction('&Table View', self)
        table_view_action.setCheckable(True)
        table_view_action.setChecked(False)
        table_view_action.setShortcut(QKeySequence('F2'))
        table_view_action.triggered.connect(self.switchToTableView)
        view_menu.addAction(table_view_action)
        self.table_view_action = table_view_action
        
        # Separator
        view_menu.addSeparator()
        
        # Toggle view action
        toggle_view_action = QAction('&Toggle View', self)
        toggle_view_action.setShortcut(QKeySequence('Ctrl+T'))
        toggle_view_action.triggered.connect(self.toggleView)
        view_menu.addAction(toggle_view_action)
        
        # Status bar
        self.statusBar().showMessage(f'Ready | {self.VERSION}')
        
        # Center window on screen
        screen_size = QApplication.primaryScreen().size()
        self.move((screen_size.width() - self.width()) // 2,
                  (screen_size.height() - self.height()) // 2)
    
    def switchToRecordView(self):
        """Switch to record view mode"""
        if self.current_view_mode == "record":
            return
            
        self.current_view_mode = "record"
        self.record_view.show()
        self.table_view.hide()
        self.nav_widget.show()
        
        # Update UI state
        self.record_view_btn.setChecked(True)
        self.table_view_btn.setChecked(False)
        self.record_view_action.setChecked(True)
        self.table_view_action.setChecked(False)
        
        # Update status bar
        self.updateStatusBar()
        
        # Display current record if data is loaded
        if self.csv_data and self.headers:
            self.displayCurrentRecord()
    
    def switchToTableView(self):
        """Switch to table view mode"""
        if self.current_view_mode == "table":
            return
            
        self.current_view_mode = "table"
        self.record_view.hide()
        self.table_view.show()
        self.nav_widget.hide()
        
        # Update UI state
        self.record_view_btn.setChecked(False)
        self.table_view_btn.setChecked(True)
        self.record_view_action.setChecked(False)
        self.table_view_action.setChecked(True)
        
        # Update status bar
        self.updateStatusBar()
        
        # Display table data if data is loaded
        if self.csv_data and self.headers:
            self.table_view.displayData(self.headers, self.csv_data)
    
    def toggleView(self):
        """Toggle between record and table view"""
        if self.current_view_mode == "record":
            self.switchToTableView()
        else:
            self.switchToRecordView()
    
    def onTableCellClicked(self, row, column):
        """Handle table cell click - switch to record view for that row"""
        if not self.csv_data:
            return
            
        # Update current record index to the clicked row
        self.current_record_index = row
        
        # Switch to record view
        self.switchToRecordView()
    
    def updateStatusBar(self):
        """Update status bar with current view mode and statistics"""
        if not self.csv_data or not self.headers:
            self.statusBar().showMessage(f'Ready | {self.VERSION}')
            return
            
        if self.current_view_mode == "record":
            self.statusBar().showMessage(f"Record View - Record {self.current_record_index + 1} of {len(self.csv_data)} | {self.VERSION}")
        else:
            self.statusBar().showMessage(f"Table View - {len(self.csv_data)} rows, {len(self.headers)} columns | {self.VERSION}")
    
    def updateRecentFilesMenu(self):
        """Update the recent files menu with stored recent files"""
        self.recent_files_menu.clear()
        
        recent_files = self.settings.value("recentFiles", [])
        if not recent_files:
            recent_files = []
        
        for i, file_path in enumerate(recent_files):
            if i < self.MAX_RECENT_FILES and os.path.exists(file_path):
                action = QAction(f"&{i+1} {file_path}", self)
                action.setData(file_path)
                action.triggered.connect(lambda checked, file_path=file_path: self.openRecentFile(file_path))
                self.recent_files_menu.addAction(action)
                
        # Add clear action if there are recent files
        if self.recent_files_menu.actions():
            self.recent_files_menu.addSeparator()
            clear_action = QAction('&Clear Recent Files', self)
            clear_action.triggered.connect(self.clearRecentFiles)
            self.recent_files_menu.addAction(clear_action)
    
    def addToRecentFiles(self, file_path):
        """Add a file to the recent files list"""
        if not file_path:
            return
            
        recent_files = self.settings.value("recentFiles", [])
        if not recent_files:
            recent_files = []
            
        # Remove if already in the list
        if file_path in recent_files:
            recent_files.remove(file_path)
            
        # Add to the front of the list
        recent_files.insert(0, file_path)
        
        # Limit list size
        if len(recent_files) > self.MAX_RECENT_FILES:
            recent_files = recent_files[:self.MAX_RECENT_FILES]
            
        # Save updated list
        self.settings.setValue("recentFiles", recent_files)
        
        # Update the menu
        self.updateRecentFilesMenu()
    
    def clearRecentFiles(self):
        """Clear the recent files list"""
        self.settings.setValue("recentFiles", [])
        self.updateRecentFilesMenu()
    
    def loadLastViewedFile(self):
        """Load the last viewed CSV file on startup"""
        last_file = self.settings.value("lastViewedFile", "")
        if last_file and os.path.exists(last_file):
            self.loadCSVFile(last_file)
    
    def openRecentFile(self, file_path):
        """Open a file from the recent files menu"""
        if os.path.exists(file_path):
            self.loadCSVFile(file_path)
        else:
            QMessageBox.warning(self, "File Not Found", 
                               f"The file {file_path} does not exist.",
                               QMessageBox.StandardButton.Ok)
            
            # Remove from recent files
            recent_files = self.settings.value("recentFiles", [])
            if file_path in recent_files:
                recent_files.remove(file_path)
                self.settings.setValue("recentFiles", recent_files)
                self.updateRecentFilesMenu()
    
    def openFile(self):
        """Open a file dialog to select a CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.loadCSVFile(file_path)
    
    def loadCSVFile(self, file_path):
        """Load and parse a CSV file"""
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                # Use csv module to handle quotes and special characters
                reader = csv.reader(f)
                self.csv_data = list(reader)
            
            if not self.csv_data:
                raise Exception("File is empty")
                
            # Extract headers (first row)
            self.headers = self.csv_data[0]
            
            # Remove headers from data
            self.csv_data = self.csv_data[1:]
            
            if not self.csv_data:
                raise Exception("No data records found")
                
            # Reset current record index
            self.current_record_index = 0
            
            # Update UI
            self.current_file_path = file_path
            self.setWindowTitle(f"CSV Reader - {file_path}")
            
            # Display data based on current view mode
            if self.current_view_mode == "record":
                self.displayCurrentRecord()
            else:
                self.table_view.displayData(self.headers, self.csv_data)
            
            # Add to recent files
            self.addToRecentFiles(file_path)
            
            # Save as last viewed file
            self.settings.setValue("lastViewedFile", file_path)
            
            # Update status
            self.updateStatusBar()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to load CSV file: {str(e)}",
                               QMessageBox.StandardButton.Ok)
            self.statusBar().showMessage("Failed to load file")
    
    def displayCurrentRecord(self):
        """Display the current record or table based on view mode"""
        if not self.csv_data or not self.headers:
            self.nav_label.setText("No file loaded")
            return
            
        if self.current_view_mode == "record":
            # Display the current record
            record = self.csv_data[self.current_record_index]
            
            # Extend record if shorter than headers
            if len(record) < len(self.headers):
                record = record + [''] * (len(self.headers) - len(record))
                
            # Update the record view
            self.record_view.displayRecord(self.headers, record)
            
            # Update navigation label
            self.nav_label.setText(f"Record {self.current_record_index + 1} of {len(self.csv_data)}")
        else:
            # Update table view
            self.table_view.displayData(self.headers, self.csv_data)
        
        # Update status bar
        self.updateStatusBar()
    
    def previousRecord(self):
        """Go to the previous record"""
        if not self.csv_data:
            return
            
        if self.current_record_index > 0:
            self.current_record_index -= 1
            self.displayCurrentRecord()
    
    def nextRecord(self):
        """Go to the next record"""
        if not self.csv_data:
            return
            
        if self.current_record_index < len(self.csv_data) - 1:
            self.current_record_index += 1
            self.displayCurrentRecord()
    
    def keyPressEvent(self, event):
        """Handle key press events for navigation"""
        if not self.csv_data:
            return super().keyPressEvent(event)
            
        if event.key() == Qt.Key.Key_Left:
            # Go to previous record
            self.previousRecord()
            event.accept()
                
        elif event.key() == Qt.Key.Key_Right:
            # Go to next record
            self.nextRecord()
            event.accept()
                
        else:
            super().keyPressEvent(event)
            
    def eventFilter(self, obj, event):
        """Global event filter to capture key events regardless of focus"""
        if event.type() == QEvent.Type.KeyPress:
            # Handle left/right arrow keys for navigation in record view only
            if self.current_view_mode == "record":
                if event.key() == Qt.Key.Key_Left:
                    self.previousRecord()
                    return True
                elif event.key() == Qt.Key.Key_Right:
                    self.nextRecord()
                    return True
        elif event.type() == QEvent.Type.Wheel:
            # Handle wheel events with Ctrl for zooming
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                delta = 15 if event.angleDelta().y() > 0 else -15
                
                # Zoom the appropriate view
                if self.current_view_mode == "record":
                    if self.record_view.zoom(delta):
                        self.statusBar().showMessage(f"Zoom: {self.record_view.current_zoom_level}%", 2000)
                else:
                    if self.table_view.zoom(delta):
                        self.statusBar().showMessage(f"Zoom: {self.table_view.current_zoom_level}%", 2000)
                return True
                
        # Standard event processing
        return super().eventFilter(obj, event)
    
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming with Ctrl modifier"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Calculate zoom delta based on wheel direction (15% steps)
            delta = 15 if event.angleDelta().y() > 0 else -15
            
            # Apply zoom to appropriate view
            if self.current_view_mode == "record":
                if self.record_view.zoom(delta):
                    self.statusBar().showMessage(f"Zoom: {self.record_view.current_zoom_level}%", 2000)
            else:
                if self.table_view.zoom(delta):
                    self.statusBar().showMessage(f"Zoom: {self.table_view.current_zoom_level}%", 2000)
                
            # Accept the event
            event.accept()
            return  # Prevent further event processing
        else:
            # Default handling for normal scrolling
            super().wheelEvent(event)

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application name for settings
    app.setApplicationName("CSVReader")
    app.setOrganizationName("CSVReader")
    
    # Create and show the main window
    window = CSVReaderApp()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

