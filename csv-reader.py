#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CSV Reader Application

A PyQt6-based application to view CSV and XLSX files with data displayed vertically.
Features:
- Display CSV/XLSX records vertically with header as labels
- Navigate records using left/right arrow keys
- Recent files menu
- Zoom functionality with Ctrl + mouse wheel
- Support for Excel files (.xlsx) using openpyxl

Changelog:
v0.1.9a 2026-11-27 07:52 CST - Batch launcher uses the project venv; run.ps1 pip upgrade fix
v0.1.9 2026-11-26 20:33 CST - Multi-sheet XLSX (sheet tabs), in-place XLSX save, read-only formulas, CSV export
v0.1.8a 2026-11-11 11:02 CST - Changelog falls back to GitHub when CHANGELOG.md is not local (EXE)
v0.1.8 2026-11-11 10:48 CST - Fixed H/arrow keys intercepted while editing Record View fields
v0.1.7 2026-05-26 CST - Added data edit feature: inline table editing, record edit mode, Save/Save As
v0.1.6 2026-02-18 09:44 CST - Integrated pyqt-app-info into Help/About dialog
v0.1.5 2026-02-18 09:27 CST - Synced run.ps1/run.sh from Python-venv generic template
v0.1.4 2026-02-17 CST - Added broken venv detection (Test-VenvValid) to run.ps1
v0.1.3 2026-02-17 CST - Added smart Python discovery (Find-Python) to run.ps1
v0.1.2 2026-02-16 16:39 CST - Added Edit menu with Search (Ctrl+F) shortcut
v0.1.1 2026-02-01 18:42 CST - Integrated Icon Manager Module for cross-platform icon support
v0.1.0 2026-01-17 14:30 CST - Added scroll position lock and scrollable Quick Reference
v0.0.5 2026-01-09 10:45 CST - Added dynamic header row selection feature
"""

import sys
import os
import csv
import re
import tempfile
import datetime
try:
    import openpyxl
    XLSX_SUPPORT_AVAILABLE = True
except ImportError:
    XLSX_SUPPORT_AVAILABLE = False
    openpyxl = None
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QGridLayout, QLabel, QScrollArea, 
                           QFileDialog, QMessageBox, QMenu, QSizePolicy,
                           QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                           QLineEdit, QPushButton, QTabBar)
from PyQt6.QtCore import Qt, QSettings, QSize, QEvent, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QFontMetrics, QPalette, QAction, QColor, QIcon

from icon_loader import icons
from cell_format import (format_cell, parse_number, parse_date,
                         is_date_format, is_number_format)

try:
    from pyqt_app_info import AppIdentity, gather_info
    from pyqt_app_info.qt import AboutDialog as _AboutDialog
    PYQT_APP_INFO_AVAILABLE = True
except ImportError:
    PYQT_APP_INFO_AVAILABLE = False

_INT_RE = re.compile(r'^-?(0|[1-9]\d*)$')
_FLOAT_RE = re.compile(r'^-?(0|[1-9]\d*)?\.\d+([eE][-+]?\d+)?$|^-?(0|[1-9]\d*)[eE][-+]?\d+$')


def coerce_cell_value(text, original, number_format=None):
    """Convert edited text back to a typed cell value, guided by the original
    cell value and its number format, so numbers/dates/bools are not saved as
    text. Formatted input such as "$1,250.00", "12%" or "9/4/2026" is understood."""
    if text == '':
        return None
    t = text.strip()
    if isinstance(original, bool):
        if t.lower() in ('true', 'false'):
            return t.lower() == 'true'
        return text
    if isinstance(original, (int, float)) or (original is None and is_number_format(number_format)):
        value = parse_number(t)
        return text if value is None else value
    if isinstance(original, (datetime.datetime, datetime.date, datetime.time)) or \
            (original is None and is_date_format(number_format)):
        value = parse_date(t, number_format)
        if value is None:
            return text
        if isinstance(original, datetime.time):
            return value.time()
        if isinstance(original, datetime.date) and not isinstance(original, datetime.datetime):
            return value.date()
        return value
    if original is None:
        # Blank General cell: plain numbers become numbers, leading zeros stay text
        if _INT_RE.match(t):
            return int(t)
        if _FLOAT_RE.match(t):
            return float(t)
    return text


def _formulaTip(formula):
    return f"Formula: {formula}\n(read-only - edit formulas in Excel)"


def _styleFormulaItem(item, formula):
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    item.setToolTip(_formulaTip(formula))
    font = item.font()
    font.setItalic(True)
    item.setFont(font)


class TableView(QTableWidget):
    """Widget to display CSV data in a spreadsheet-like table format"""

    cellEdited = pyqtSignal(int, int, str)
    # Optional callable returning {(data_row, col): formula} for read-only cells
    locked_provider = None

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configure table properties
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked |
            QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setWordWrap(True)
        
        # Enable scrolling
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        
        # Configure headers
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        self.verticalHeader().setDefaultSectionSize(25)
        self.verticalHeader().setVisible(True)
        
        # Default font settings
        self.base_font_size = 10
        self.current_zoom_level = 100  # 100%
        self.updateFontSize()
        
        # Enable sorting
        self.setSortingEnabled(True)
        
        # Search tracking
        self.search_results = []  # List of (row, col) tuples
        self.current_search_index = -1
        self.search_text = ""

        self._loading = False
        self.itemChanged.connect(self._onItemChanged)
        
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
        self._loading = True
        try:
            if not headers or not data:
                self.clear()
                self.setRowCount(0)
                self.setColumnCount(len(headers) if headers else 0)
                if headers:
                    self.setHorizontalHeaderLabels(headers)
                return

            # Set table dimensions
            self.setRowCount(len(data))
            self.setColumnCount(len(headers))

            # Set headers
            self.setHorizontalHeaderLabels(headers)

            locked = self.locked_provider() if self.locked_provider else {}

            # Populate table with data
            for row_idx, row_data in enumerate(data):
                # Ensure row has enough columns
                if len(row_data) < len(headers):
                    row_data = row_data + [''] * (len(headers) - len(row_data))

                for col_idx, cell_value in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                    formula = locked.get((row_idx, col_idx))
                    if formula is not None:
                        _styleFormulaItem(item, formula)
                    self.setItem(row_idx, col_idx, item)

            # Resize columns to content
            self.resizeColumnsToContents()

            # Update font size
            self.updateFontSize()

            # Clear search highlights
            self.clearSearch()
        finally:
            self._loading = False
    
    def searchTable(self, search_text, case_sensitive=False):
        """Search for text in the table and highlight results"""
        # Clear previous search
        self.clearSearch()
        
        if not search_text:
            return 0
        
        self.search_text = search_text
        self.search_results = []
        
        # Search through all cells
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    cell_text = item.text()
                    # Check if search text is in cell
                    if case_sensitive:
                        if search_text in cell_text:
                            self.search_results.append((row, col))
                    else:
                        if search_text.lower() in cell_text.lower():
                            self.search_results.append((row, col))
        
        # Highlight all results
        for row, col in self.search_results:
            item = self.item(row, col)
            if item:
                item.setBackground(QColor(255, 255, 0, 100))  # Light yellow
        
        # Move to first result if any
        if self.search_results:
            self.current_search_index = 0
            self.highlightCurrentResult()
        
        return len(self.search_results)
    
    def highlightCurrentResult(self):
        """Highlight the current search result with a different color"""
        if not self.search_results or self.current_search_index < 0:
            return
        
        # Unhighlight previous result (back to light yellow)
        for i, (row, col) in enumerate(self.search_results):
            item = self.item(row, col)
            if item:
                if i == self.current_search_index:
                    item.setBackground(QColor(255, 165, 0, 150))  # Orange for current
                else:
                    item.setBackground(QColor(255, 255, 0, 100))  # Light yellow for others
        
        # Scroll to current result
        if self.search_results:
            row, col = self.search_results[self.current_search_index]
            self.scrollToItem(self.item(row, col))
    
    def nextSearchResult(self):
        """Move to next search result"""
        if not self.search_results:
            return False
        
        self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        self.highlightCurrentResult()
        return True
    
    def previousSearchResult(self):
        """Move to previous search result"""
        if not self.search_results:
            return False
        
        self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
        self.highlightCurrentResult()
        return True
    
    def clearSearch(self):
        """Clear search highlights"""
        for row, col in self.search_results:
            item = self.item(row, col)
            if item:
                item.setBackground(QColor(255, 255, 255, 0))  # Transparent

        self.search_results = []
        self.current_search_index = -1
        self.search_text = ""

    def _onItemChanged(self, item):
        if not self._loading:
            self.cellEdited.emit(item.row(), item.column(), item.text())

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

        self.edit_mode = False
        self.field_editors = []

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
        
    def displayRecord(self, headers, record, locked=None):
        """Display a record with headers as labels (or editors in edit mode)"""
        scrollbar = self.verticalScrollBar()
        saved_scroll_position = scrollbar.value()

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.field_editors = []

        if not headers or not record:
            return

        for row, (header, value) in enumerate(zip(headers, record)):
            header_label = QLabel(header)
            header_label.setStyleSheet(self.label_style)
            header_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

            if self.edit_mode:
                value_widget = QLineEdit(str(value))
                self.field_editors.append(value_widget)
            else:
                value_widget = QLabel(str(value))
                value_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                value_widget.setWordWrap(True)
                value_widget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

            formula = locked.get(row) if locked else None
            if formula is not None:
                if self.edit_mode:
                    value_widget.setReadOnly(True)
                    value_widget.setEnabled(False)
                value_widget.setToolTip(_formulaTip(formula))
                font = value_widget.font()
                font.setItalic(True)
                value_widget.setFont(font)

            self.grid_layout.addWidget(header_label, row, 0)
            self.grid_layout.addWidget(value_widget, row, 1)

        self.grid_layout.setColumnStretch(0, 0)
        self.grid_layout.setColumnStretch(1, 1)

        self.updateFontSize()

        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: scrollbar.setValue(saved_scroll_position))

    def getEditedValues(self):
        """Return current values from edit-mode field editors"""
        return [editor.text() for editor in self.field_editors]

class CSVReaderApp(QMainWindow):
    """Main application window for CSV Reader"""
    
    MAX_RECENT_FILES = 10
    VERSION = "v0.1.9a  2026-11-27  07:52 CST"
    
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
        self.search_visible = False
        self.is_modified = False
        self.record_edit_mode = False

        # XLSX in-place save tracking
        self.xlsx_source = None      # {'path', 'sheets': [sheet state], 'active': index}
        self.row_origins = []        # sheet row (1-based) for [headers] + csv_data
        self.dirty_cells = set()     # {(sheet_row, col0)} edited since last XLSX save
        
        # Set up the UI
        self.initUI()
        
        # Load recent files list
        self.updateRecentFilesMenu()
        
        # Install event filter for key events at application level
        QApplication.instance().installEventFilter(self)
    
    def initUI(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("CSV/XLSX Reader")
        self.setMinimumSize(800, 600)
        
        # Set window icon
        self.setWindowIcon(icons.app_icon())
        
        # Create central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Create view toggle controls
        view_controls_layout = QHBoxLayout()
        
        # View mode buttons
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
        
        # Search button (only visible in table view)
        self.search_toggle_btn = QPushButton("Search")
        self.search_toggle_btn.setCheckable(True)
        self.search_toggle_btn.setChecked(False)
        self.search_toggle_btn.clicked.connect(self.toggleSearch)
        self.search_toggle_btn.hide()  # Hidden initially
        view_controls_layout.addWidget(self.search_toggle_btn)
        
        main_layout.addLayout(view_controls_layout)
        
        # Create search bar (initially hidden)
        self.search_widget = QWidget()
        search_layout = QHBoxLayout(self.search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        search_layout.addWidget(QLabel("Search:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search text...")
        self.search_input.returnPressed.connect(self.performSearch)
        search_layout.addWidget(self.search_input)
        
        self.search_btn = QPushButton("Find")
        self.search_btn.clicked.connect(self.performSearch)
        search_layout.addWidget(self.search_btn)
        
        self.prev_result_btn = QPushButton("Previous")
        self.prev_result_btn.clicked.connect(self.previousSearchResult)
        search_layout.addWidget(self.prev_result_btn)
        
        self.next_result_btn = QPushButton("Next")
        self.next_result_btn.clicked.connect(self.nextSearchResult)
        search_layout.addWidget(self.next_result_btn)
        
        self.search_result_label = QLabel("")
        search_layout.addWidget(self.search_result_label)
        
        self.clear_search_btn = QPushButton("Clear")
        self.clear_search_btn.clicked.connect(self.clearTableSearch)
        search_layout.addWidget(self.clear_search_btn)
        
        self.search_widget.hide()
        main_layout.addWidget(self.search_widget)
        
        # Create views container
        self.views_container = QWidget()
        self.views_layout = QVBoxLayout(self.views_container)
        
        # Create both views
        self.record_view = RecordView()
        self.table_view = TableView()
        
        # Connect table row click to record view
        self.table_view.cellClicked.connect(self.onTableCellClicked)
        self.table_view.cellEdited.connect(self._onTableCellEdited)
        self.table_view.locked_provider = self._lockedCells
        
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

        self.edit_record_btn = QPushButton("Edit")
        self.edit_record_btn.clicked.connect(self._toggleRecordEditMode)
        nav_layout.addWidget(self.edit_record_btn)

        main_layout.addWidget(self.nav_widget)

        # Sheet tabs (only shown for multi-sheet workbooks)
        self.sheet_tabs = QTabBar()
        self.sheet_tabs.setShape(QTabBar.Shape.RoundedSouth)
        self.sheet_tabs.setExpanding(False)
        self.sheet_tabs.setUsesScrollButtons(True)
        self.sheet_tabs.setDocumentMode(True)
        self.sheet_tabs.currentChanged.connect(self.switchSheet)
        self.sheet_tabs.hide()
        main_layout.addWidget(self.sheet_tabs)
        
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

        # Save action
        save_action = QAction('&Save', self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.saveFile)
        file_menu.addAction(save_action)

        # Save As action
        save_as_action = QAction('Save &As...', self)
        save_as_action.setShortcut(QKeySequence('Ctrl+Shift+S'))
        save_as_action.triggered.connect(self.saveFileAs)
        file_menu.addAction(save_as_action)

        # Separator
        file_menu.addSeparator()

        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('&Edit')

        # Search action
        search_action = QAction('&Search...', self)
        search_action.setShortcut(QKeySequence('Ctrl+F'))
        search_action.triggered.connect(self.activateSearch)
        edit_menu.addAction(search_action)

        # View menu
        view_menu = menubar.addMenu('&View')
        
        # Record view action
        record_view_action = QAction('&Record View', self)
        record_view_action.setCheckable(True)
        record_view_action.setChecked(True)
        record_view_action.triggered.connect(self.switchToRecordView)
        view_menu.addAction(record_view_action)
        self.record_view_action = record_view_action
        
        # Table view action
        table_view_action = QAction('&Table View', self)
        table_view_action.setCheckable(True)
        table_view_action.setChecked(False)
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

        view_menu.addSeparator()

        self.next_sheet_action = QAction('&Next Sheet', self)
        self.next_sheet_action.setShortcut(QKeySequence('Ctrl+PgDown'))
        self.next_sheet_action.triggered.connect(lambda: self.switchSheetBy(1))
        self.next_sheet_action.setEnabled(False)
        view_menu.addAction(self.next_sheet_action)

        self.prev_sheet_action = QAction('&Previous Sheet', self)
        self.prev_sheet_action.setShortcut(QKeySequence('Ctrl+PgUp'))
        self.prev_sheet_action.triggered.connect(lambda: self.switchSheetBy(-1))
        self.prev_sheet_action.setEnabled(False)
        view_menu.addAction(self.prev_sheet_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        # Quick Reference action
        quick_ref_action = QAction('&Quick Reference', self)
        quick_ref_action.setShortcut(QKeySequence('F1'))
        quick_ref_action.triggered.connect(self.showQuickReference)
        help_menu.addAction(quick_ref_action)
        
        # Changelog action
        changelog_action = QAction('&Changelog', self)
        changelog_action.triggered.connect(self.showChangelog)
        help_menu.addAction(changelog_action)
        
        # Separator
        help_menu.addSeparator()
        
        # About action
        about_action = QAction('&About CSV Reader', self)
        about_action.triggered.connect(self.showAbout)
        help_menu.addAction(about_action)
        
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
        self.edit_record_btn.show()

        # Hide search controls
        self.search_toggle_btn.hide()
        self.search_widget.hide()
        self.search_visible = False
        
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

        if self.record_edit_mode:
            self._commitRecordEdits(refresh=False)

        self.current_view_mode = "table"
        self.record_view.hide()
        self.table_view.show()
        self.nav_widget.hide()
        self.edit_record_btn.hide()

        # Show search button
        self.search_toggle_btn.show()
        
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
        sheet = ''
        if self.xlsx_source and len(self.xlsx_source['sheets']) > 1:
            src = self.xlsx_source
            sheet = (f"Sheet {src['active'] + 1}/{len(src['sheets'])}: "
                     f"{src['sheets'][src['active']]['name']} | ")

        if not self.csv_data or not self.headers:
            if self.xlsx_source:
                self.statusBar().showMessage(f"{sheet}Sheet has no data rows | {self.VERSION}")
            else:
                self.statusBar().showMessage(f'Ready | {self.VERSION}')
            return
            
        if self.current_view_mode == "record":
            self.statusBar().showMessage(f"{sheet}Record View - Record {self.current_record_index + 1} of {len(self.csv_data)} | {self.VERSION}")
        else:
            self.statusBar().showMessage(f"{sheet}Table View - {len(self.csv_data)} rows, {len(self.headers)} columns | {self.VERSION}")
    
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
        """Load the last viewed data file on startup"""
        last_file = self.settings.value("lastViewedFile", "")
        if last_file and os.path.exists(last_file):
            self.loadDataFile(last_file)
    
    def activateSearch(self):
        """Activate search - switch to table view if needed and show search bar"""
        if self.current_view_mode == "record":
            self.switchToTableView()
        if not self.search_visible:
            self.toggleSearch()
        self.search_input.setFocus()
        self.search_input.selectAll()

    def toggleSearch(self):
        """Toggle search bar visibility"""
        self.search_visible = not self.search_visible
        if self.search_visible:
            self.search_widget.show()
            self.search_input.setFocus()
        else:
            self.search_widget.hide()
            self.clearTableSearch()
    
    def performSearch(self):
        """Perform search in table view"""
        search_text = self.search_input.text()
        if not search_text:
            return
        
        count = self.table_view.searchTable(search_text, case_sensitive=False)
        if count > 0:
            self.search_result_label.setText(f"Found {count} match(es) - Showing 1/{count}")
        else:
            self.search_result_label.setText("No matches found")
    
    def nextSearchResult(self):
        """Move to next search result"""
        if self.table_view.nextSearchResult():
            total = len(self.table_view.search_results)
            current = self.table_view.current_search_index + 1
            self.search_result_label.setText(f"Found {total} match(es) - Showing {current}/{total}")
    
    def previousSearchResult(self):
        """Move to previous search result"""
        if self.table_view.previousSearchResult():
            total = len(self.table_view.search_results)
            current = self.table_view.current_search_index + 1
            self.search_result_label.setText(f"Found {total} match(es) - Showing {current}/{total}")
    
    def clearTableSearch(self):
        """Clear search in table view"""
        self.search_input.clear()
        self.search_result_label.setText("")
        self.table_view.clearSearch()
    
    def showQuickReference(self):
        """Display quick reference dialog"""
        quick_ref_text = """
<h2>CSV/XLSX Reader - Quick Reference</h2>

<h3>Supported File Formats</h3>
<ul>
<li><b>CSV Files</b>: Standard comma-separated values files (.csv)</li>
<li><b>Excel Files</b>: Excel workbook files (.xlsx) - all sheets; switch with the tabs at the bottom or Ctrl+PgUp / Ctrl+PgDn. Cells are shown with their Excel number format (currency, dates, percentages). Formula cells are shown in italics and are read-only. Save As .csv offers the current sheet or one file per sheet.</li>
</ul>

<h3>View Modes</h3>
<ul>
<li><b>Record View</b>: Displays one data record at a time with fields shown vertically (header-value pairs)</li>
<li><b>Table View</b>: Displays all data in a spreadsheet-like table format</li>
</ul>

<h3>Navigation (Record View)</h3>
<ul>
<li><b>Left Arrow</b>: Previous record</li>
<li><b>Right Arrow</b>: Next record</li>
<li><b>H</b>: Select current record as header row</li>
<li><b>Click Previous/Next buttons</b>: Navigate between records</li>
</ul>

<h3>Table View</h3>
<ul>
<li><b>Click any cell</b>: Switch to Record View for that row</li>
<li><b>Click column headers</b>: Sort by that column</li>
<li><b>Double-click a cell</b>: Edit cell value inline; press Enter to confirm, Escape to cancel</li>
</ul>

<h3>Editing Data</h3>
<ul>
<li><b>Table View</b>: Double-click any cell to edit it in place</li>
<li><b>Record View</b>: Click the <b>Edit</b> button to enter edit mode; all fields become text inputs. Click <b>Done Editing</b> to save changes to memory. Navigation (arrow keys or buttons) auto-saves the current record before moving.</li>
<li><b>Ctrl+S</b>: Save changes back to the original file</li>
<li><b>Ctrl+Shift+S</b>: Save As — write to a new file</li>
<li>Unsaved changes are indicated by <b>*</b> in the title bar. You will be prompted to save when opening a new file or closing the application.</li>
</ul>

<h3>Keyboard Shortcuts</h3>
<ul>
<li><b>Ctrl+O</b>: Open CSV/XLSX file</li>
<li><b>Ctrl+S</b>: Save file</li>
<li><b>Ctrl+Shift+S</b>: Save As</li>
<li><b>Ctrl+F</b>: Search (switches to Table View if needed)</li>
<li><b>Ctrl+T</b>: Toggle between Record and Table views</li>
<li><b>Ctrl+MouseWheel</b>: Zoom in/out (40%-300%)</li>
<li><b>F1</b>: Show Quick Reference</li>
<li><b>Ctrl+Q</b>: Quit application</li>
</ul>

<h3>Features</h3>
<ul>
<li><b>Recent Files</b>: Access recently opened CSV files from File menu</li>
<li><b>Auto-load</b>: Last viewed file opens automatically on startup</li>
<li><b>Independent Zoom</b>: Each view mode maintains its own zoom level</li>
<li><b>Text Selection</b>: Select and copy text in Record View</li>
<li><b>Dynamic Header Selection</b>: Press H to set current record as new header row</li>
<li><b>Scroll Position Lock</b>: Scroll position is preserved when navigating between records for easy field comparison</li>
</ul>
        """

        from PyQt6.QtWidgets import QDialog, QTextBrowser, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Quick Reference")
        dialog.setMinimumSize(600, 500)

        layout = QVBoxLayout(dialog)

        text_browser = QTextBrowser()
        text_browser.setHtml(quick_ref_text)
        text_browser.setOpenExternalLinks(True)
        layout.addWidget(text_browser)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.exec()

    CHANGELOG_URL = "https://github.com/juren53/csv-reader/blob/main/CHANGELOG.md"

    def showChangelog(self):
        """Show CHANGELOG.md locally, falling back to the GitHub URL"""
        # Source tree: next to this script. Frozen EXE: next to the executable.
        candidates = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "CHANGELOG.md")]
        if getattr(sys, 'frozen', False):
            candidates.append(os.path.join(os.path.dirname(sys.executable), "CHANGELOG.md"))
        changelog_path = next((p for p in candidates if os.path.isfile(p)), None)

        if changelog_path:
            try:
                from PyQt6.QtWidgets import QDialog, QTextBrowser, QDialogButtonBox
                with open(changelog_path, 'r', encoding='utf-8') as f:
                    changelog_text = f.read()

                dialog = QDialog(self)
                dialog.setWindowTitle("Changelog")
                dialog.resize(740, 560)
                layout = QVBoxLayout(dialog)

                text_browser = QTextBrowser()
                text_browser.setOpenExternalLinks(True)
                text_browser.setMarkdown(changelog_text)
                layout.addWidget(text_browser)

                button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
                button_box.accepted.connect(dialog.accept)
                layout.addWidget(button_box)

                dialog.exec()
                return
            except Exception as e:
                print(f"Error showing local changelog: {e}")

        # Local file unavailable (compiled EXE, or source tree missing) —
        # open the GitHub copy in the default browser.
        import webbrowser
        try:
            webbrowser.open(self.CHANGELOG_URL)
        except Exception:
            QMessageBox.warning(self, "Changelog",
                                f"Could not open changelog.\n\nURL: {self.CHANGELOG_URL}")
    
    def showAbout(self):
        """Display about dialog"""
        if PYQT_APP_INFO_AVAILABLE:
            identity = AppIdentity(
                name="CSV/XLSX Reader",
                version=self.VERSION,
                description="A PyQt6-based application for viewing CSV and XLSX files with both record and table view modes.",
                features=[
                    "Support for CSV and XLSX files",
                    "Multi-sheet XLSX files (sheet tabs, Ctrl+PgUp/PgDn)",
                    "Dual view modes (Record and Table)",
                    "Dynamic header row selection",
                    "Keyboard navigation and shortcuts",
                    "Zoom functionality (40%–300%)",
                    "Recent files tracking",
                    "Auto-load last viewed file",
                ],
            )
            info = gather_info(identity, caller_file=__file__)
            _AboutDialog(info, parent=self).exec()
        else:
            about_text = f"""
<h2>CSV/XLSX Reader</h2>
<p><b>Version:</b> {self.VERSION}</p>
<p>A PyQt6-based application for viewing CSV and XLSX files with both record and table view modes.</p>
<p><b>Features:</b></p>
<ul>
<li>Support for CSV and XLSX files</li>
<li>Multi-sheet XLSX files (sheet tabs, Ctrl+PgUp/PgDn)</li>
<li>Dual view modes (Record and Table)</li>
<li>Dynamic header row selection</li>
<li>Keyboard navigation and shortcuts</li>
<li>Zoom functionality (40%-300%)</li>
<li>Recent files tracking</li>
<li>Auto-load last viewed file</li>
</ul>
<p><b>Copyright © 2026</b></p>
            """
            msg = QMessageBox(self)
            msg.setWindowTitle("About CSV/XLSX Reader")
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setText(about_text)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
    
    def openRecentFile(self, file_path):
        """Open a file from the recent files menu"""
        if os.path.exists(file_path):
            self.loadDataFile(file_path)
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
        """Open a file dialog to select a CSV or XLSX file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Data File", "",
            "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)"
        )

        if file_path:
            self.loadDataFile(file_path)

    def _loadCSVData(self, file_path):
        """Parse CSV file and populate headers and csv_data"""
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
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

        self.xlsx_source = None
        self.row_origins = []
        self.dirty_cells = set()

    def _loadXLSXData(self, file_path):
        """Open an XLSX workbook: read the first sheet now, the rest on first view"""
        if not XLSX_SUPPORT_AVAILABLE:
            raise Exception(
                "XLSX support requires the 'openpyxl' library.\n\n"
                "Install it using: pip install openpyxl"
            )

        try:
            formula_wb = openpyxl.load_workbook(file_path, read_only=True)
        except Exception as e:
            raise Exception(f"Failed to open XLSX file: {str(e)}")

        try:
            if len(formula_wb.sheetnames) == 0:
                raise Exception("XLSX file contains no sheets")
            sheets = [self._newSheetState(name) for name in formula_wb.sheetnames]
            self._readSheet(sheets[0], file_path, formula_wb)
        finally:
            formula_wb.close()

        self.xlsx_source = {'path': file_path, 'sheets': sheets, 'active': 0}
        self._restoreSheet(0)

    @staticmethod
    def _newSheetState(name):
        return {'name': name, 'loaded': False, 'headers': [], 'data': [],
                'record_index': 0, 'raw': [], 'row_origins': [], 'dirty_cells': set(),
                'formulas': {}, 'formats': {}}

    @staticmethod
    def _fillSheetState(state, formula_sheet, cached_sheet_fn):
        """Read a worksheet into a sheet-state dict.

        `formula_sheet` is the sheet read with formulas as text. Only when it
        contains formulas is `cached_sheet_fn()` called for the same sheet with
        cached (calculated) values, so formula-free sheets are read once."""
        # Pass 1: values and formula candidates. Start at A1 so index == sheet row - 1
        rows = []
        formats = {}     # {(sheet_row, col): number format} for non-General cells
        candidates = {}  # {sheet_row: {col: formula text}}
        for sheet_row, cells in enumerate(
                formula_sheet.iter_rows(min_row=1, min_col=1), 1):
            row = []
            for col, cell in enumerate(cells):
                row.append(getattr(cell, 'value', cell))
                fmt = getattr(cell, 'number_format', None)
                if fmt and fmt != 'General':
                    formats[(sheet_row, col)] = fmt
            for col, fval in enumerate(row):
                ftext = getattr(fval, 'text', fval)  # ArrayFormula has .text
                if isinstance(ftext, str) and ftext.startswith('='):
                    candidates.setdefault(sheet_row, {})[col] = ftext
            rows.append(row)

        # Pass 2 (only if needed): swap formula text for cached values
        formulas = {}
        no_cache = set()
        if candidates:
            cached_rows = cached_sheet_fn().iter_rows(min_row=1, min_col=1, values_only=True)
            for sheet_row, crow in enumerate(cached_rows, 1):
                for col, ftext in candidates.get(sheet_row, {}).items():
                    cached = crow[col] if col < len(crow) else None
                    if isinstance(cached, str) and cached == ftext:
                        continue  # a literal string that starts with "=", not a formula
                    formulas.setdefault(sheet_row, {})[col] = ftext
                    rows[sheet_row - 1][col] = cached
                    if cached is None:
                        no_cache.add((sheet_row, col))

        raw = []
        data = []
        for sheet_row, row in enumerate(rows, 1):
            text = [format_cell(cell, formats.get((sheet_row, col), 'General'))
                    for col, cell in enumerate(row)]
            for col, ftext in formulas.get(sheet_row, {}).items():
                if (sheet_row, col) in no_cache:
                    text[col] = ftext  # no cached value (e.g. saved by openpyxl)
            raw.append(tuple(row))
            data.append(text)
        # Drop trailing all-blank rows (formatting-only rows inflate max_row)
        while data and not any(data[-1]):
            data.pop()
            raw.pop()
        state.update(loaded=True, raw=raw, formulas=formulas, formats=formats,
                     headers=data[0] if data else [],
                     data=data[1:],
                     row_origins=list(range(1, len(data) + 1)),
                     record_index=0, dirty_cells=set())

    def _ensureSheetLoaded(self, index):
        state = self.xlsx_source['sheets'][index]
        if state['loaded']:
            return
        formula_wb = openpyxl.load_workbook(self.xlsx_source['path'], read_only=True)
        try:
            self._readSheet(state, self.xlsx_source['path'], formula_wb)
        finally:
            formula_wb.close()

    def _readSheet(self, state, file_path, formula_wb):
        """Fill `state` from its sheet, opening the cached-values copy only if needed"""
        cached_wb = None

        def cached_sheet():
            nonlocal cached_wb
            cached_wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            return cached_wb[state['name']]

        try:
            self._fillSheetState(state, formula_wb[state['name']], cached_sheet)
        finally:
            if cached_wb is not None:
                cached_wb.close()

    def _lockedCells(self):
        """Formula cells of the active sheet as {(data_row, col): formula}"""
        if not self.xlsx_source:
            return {}
        formulas = self.xlsx_source['sheets'][self.xlsx_source['active']]['formulas']
        if not formulas:
            return {}
        locked = {}
        for data_row, sheet_row in enumerate(self.row_origins[1:]):
            for col, formula in formulas.get(sheet_row, {}).items():
                locked[(data_row, col)] = formula
        return locked

    def _stashActiveSheet(self):
        """Copy the working globals back into the active sheet's state"""
        if not self.xlsx_source:
            return
        state = self.xlsx_source['sheets'][self.xlsx_source['active']]
        state.update(headers=self.headers, data=self.csv_data,
                     record_index=self.current_record_index,
                     row_origins=self.row_origins, dirty_cells=self.dirty_cells)

    def _restoreSheet(self, index):
        """Make sheet `index` the working data"""
        state = self.xlsx_source['sheets'][index]
        self.xlsx_source['active'] = index
        self.headers = state['headers']
        self.csv_data = state['data']
        self.current_record_index = min(state['record_index'], max(len(state['data']) - 1, 0))
        self.row_origins = state['row_origins']
        self.dirty_cells = state['dirty_cells']

    def _refreshSheetTabs(self):
        """Populate / hide the sheet tab bar for the loaded file"""
        multi = bool(self.xlsx_source) and len(self.xlsx_source['sheets']) > 1
        self.sheet_tabs.blockSignals(True)
        while self.sheet_tabs.count():
            self.sheet_tabs.removeTab(0)
        if multi:
            for state in self.xlsx_source['sheets']:
                self.sheet_tabs.addTab(state['name'])
            self.sheet_tabs.setCurrentIndex(self.xlsx_source['active'])
        self.sheet_tabs.blockSignals(False)
        self.sheet_tabs.setVisible(multi)
        self.next_sheet_action.setEnabled(multi)
        self.prev_sheet_action.setEnabled(multi)

    def _finishTableEdit(self):
        """Commit an open inline table editor (its focus-out commits the value)"""
        if self.table_view.state() == QAbstractItemView.State.EditingState:
            focus = QApplication.focusWidget()
            if focus is not None and self.table_view.isAncestorOf(focus):
                focus.clearFocus()

    def switchSheetBy(self, step):
        if self.xlsx_source and len(self.xlsx_source['sheets']) > 1:
            count = len(self.xlsx_source['sheets'])
            self.switchSheet((self.xlsx_source['active'] + step) % count)

    def switchSheet(self, index):
        """Switch the views to another worksheet of the open workbook"""
        src = self.xlsx_source
        if not src or not (0 <= index < len(src['sheets'])) or index == src['active']:
            return

        self._finishTableEdit()
        if self.record_edit_mode:
            self._commitRecordEdits(refresh=False)

        try:
            self._ensureSheetLoaded(index)
        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"Failed to read sheet '{src['sheets'][index]['name']}': {str(e)}")
            self._refreshSheetTabs()  # snap the tab back to the active sheet
            return

        self._stashActiveSheet()
        self._restoreSheet(index)

        self.sheet_tabs.blockSignals(True)
        self.sheet_tabs.setCurrentIndex(index)
        self.sheet_tabs.blockSignals(False)

        if self.search_visible:
            self.clearTableSearch()
        self._updateTitle()
        self.displayCurrentRecord()

    def _updateTitle(self):
        title = "CSV/XLSX Reader"
        if self.current_file_path:
            title += f" - {self.current_file_path}"
            if self.xlsx_source and len(self.xlsx_source['sheets']) > 1:
                title += f" [{self.xlsx_source['sheets'][self.xlsx_source['active']]['name']}]"
        if self.is_modified:
            title += " *"
        self.setWindowTitle(title)

    def loadDataFile(self, file_path):
        """Load and parse a CSV or XLSX file"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Save before opening a new file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.saveFile()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        try:
            # Detect file type
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == '.xlsx':
                self._loadXLSXData(file_path)
            elif file_ext == '.csv':
                self._loadCSVData(file_path)
            else:
                raise Exception(f"Unsupported file type: {file_ext}")

            # Reset current record index
            self.current_record_index = 0

            # Update UI
            self.current_file_path = file_path

            # Display data based on current view mode
            if self.current_view_mode == "record":
                self.displayCurrentRecord()
            else:
                self.table_view.displayData(self.headers, self.csv_data)

            # Add to recent files
            self.addToRecentFiles(file_path)

            # Save as last viewed file
            self.settings.setValue("lastViewedFile", file_path)

            # Reset modified / edit state
            self.is_modified = False
            self.record_edit_mode = False
            self.edit_record_btn.setText("Edit")
            self.record_view.edit_mode = False
            self._updateTitle()
            self._refreshSheetTabs()

            # Update status
            self.updateStatusBar()

        except Exception as e:
            QMessageBox.critical(self, "Error",
                               f"Failed to load file: {str(e)}",
                               QMessageBox.StandardButton.Ok)
            self.statusBar().showMessage("Failed to load file")

    def loadCSVFile(self, file_path):
        """Load and parse a CSV file (deprecated - use loadDataFile)"""
        self.loadDataFile(file_path)
    
    def displayCurrentRecord(self):
        """Display the current record or table based on view mode"""
        if not self.csv_data or not self.headers:
            if self.xlsx_source:
                self.nav_label.setText("Sheet has no data rows")
                self.record_view.displayRecord([], [])
                self.table_view.displayData(self.headers, [])
                self.updateStatusBar()
            else:
                self.nav_label.setText("No file loaded")
            return
            
        if self.current_view_mode == "record":
            # Display the current record
            record = self.csv_data[self.current_record_index]
            
            # Extend record if shorter than headers
            if len(record) < len(self.headers):
                record = record + [''] * (len(self.headers) - len(record))
                
            # Update the record view
            self.record_view.displayRecord(
                self.headers, record,
                locked={c: f for (r, c), f in self._lockedCells().items()
                        if r == self.current_record_index})
            
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

        if self.record_edit_mode:
            self._commitRecordEdits(refresh=False)

        if self.current_record_index > 0:
            self.current_record_index -= 1
            self.displayCurrentRecord()

    def nextRecord(self):
        """Go to the next record"""
        if not self.csv_data:
            return

        if self.record_edit_mode:
            self._commitRecordEdits(refresh=False)

        if self.current_record_index < len(self.csv_data) - 1:
            self.current_record_index += 1
            self.displayCurrentRecord()

    def selectCurrentRecordAsHeader(self):
        """Allow user to select current record as the new header row"""
        if not self.csv_data or not self.headers:
            return

        # Don't allow if only one row (would leave no data)
        if len(self.csv_data) <= 1:
            QMessageBox.warning(
                self,
                "Cannot Change Header",
                "Cannot set header when only one data row exists.",
                QMessageBox.StandardButton.Ok
            )
            return

        current_record = self.csv_data[self.current_record_index]

        # Show confirmation dialog
        if self.showHeaderSelectionDialog(current_record, self.current_record_index):
            self.reassignHeaderRow(self.current_record_index)

    def showHeaderSelectionDialog(self, record_data, record_index):
        """Show dialog to confirm header selection with horizontal display"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, \
                                     QTableWidgetItem, QDialogButtonBox, QLabel

        dialog = QDialog(self)
        dialog.setWindowTitle("Select Header Row")
        dialog.setMinimumWidth(600)

        layout = QVBoxLayout()

        # Add explanation label
        info_label = QLabel(
            f"Select record {record_index + 1} as the new header row?\n\n"
            "The current header will become a data row.\n"
            "All rows before this will remain as data."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Create table to show current headers and selected row
        preview_table = QTableWidget(2, len(self.headers))
        preview_table.setHorizontalHeaderLabels([f"Col {i+1}" for i in range(len(self.headers))])
        preview_table.setVerticalHeaderLabels(["Current Header", "New Header"])

        # Populate table
        for col_idx, header in enumerate(self.headers):
            preview_table.setItem(0, col_idx, QTableWidgetItem(str(header)))

        for col_idx, value in enumerate(record_data):
            if col_idx < len(self.headers):
                preview_table.setItem(1, col_idx, QTableWidgetItem(str(value)))

        preview_table.resizeColumnsToContents()
        preview_table.setMaximumHeight(150)
        layout.addWidget(preview_table)

        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        # Show dialog and return result
        return dialog.exec() == QDialog.DialogCode.Accepted

    def reassignHeaderRow(self, new_header_index):
        """Reassign the header row to a different row in the data"""
        if new_header_index < 0 or new_header_index >= len(self.csv_data):
            return

        # Get the new header row
        new_header_row = self.csv_data[new_header_index]

        # Pad new header if needed to match maximum row length
        max_cols = max(len(row) for row in self.csv_data)
        if len(new_header_row) < max_cols:
            new_header_row = list(new_header_row) + \
                            [f"Column{i+1}" for i in range(len(new_header_row), max_cols)]
        else:
            new_header_row = list(new_header_row)

        # Build new data structure
        new_data = []

        # 1. Add old header as first data row
        new_data.append(self.headers)

        # 2. Add all rows before the selected row
        new_data.extend(self.csv_data[0:new_header_index])

        # 3. Add all rows after the selected row (skip the selected row itself)
        new_data.extend(self.csv_data[new_header_index + 1:])

        # Normalize all rows to have same length as headers
        for i in range(len(new_data)):
            if len(new_data[i]) < len(new_header_row):
                new_data[i] = list(new_data[i]) + [''] * (len(new_header_row) - len(new_data[i]))

        # Keep sheet-row origins aligned with the reordered rows
        if self.row_origins:
            header_origin, data_origins = self.row_origins[0], self.row_origins[1:]
            self.row_origins = ([data_origins[new_header_index], header_origin]
                                + data_origins[:new_header_index]
                                + data_origins[new_header_index + 1:])

        # Update application state
        self.headers = new_header_row
        self.csv_data = new_data

        # Adjust current record index if needed
        if self.current_record_index >= len(self.csv_data):
            self.current_record_index = len(self.csv_data) - 1
        if self.current_record_index < 0:
            self.current_record_index = 0

        # Update both views
        if self.current_view_mode == "record":
            self.displayCurrentRecord()
        else:
            self.table_view.displayData(self.headers, self.csv_data)
            self.switchToRecordView()  # Switch back to record view after change

        # Update UI
        self.updateStatusBar()
        self.statusBar().showMessage("Header row updated", 3000)

    def _markModified(self):
        if not self.is_modified:
            self.is_modified = True
            self._updateTitle()

    def _markSaved(self):
        self.is_modified = False
        self._updateTitle()

    def closeEvent(self, event):
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.saveFile()
                event.accept()
            elif reply == QMessageBox.StandardButton.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def _onTableCellEdited(self, row, col, value):
        if 0 <= row < len(self.csv_data):
            row_data = list(self.csv_data[row])
            while len(row_data) <= col:
                row_data.append('')
            if row_data[col] != value:
                row_data[col] = value
                self.csv_data[row] = row_data
                self._markCellDirty(row, col)
                self._markModified()

    def _markCellDirty(self, data_row, col):
        """Record an edited data cell by its original sheet position"""
        if self.xlsx_source and data_row + 1 < len(self.row_origins):
            self.dirty_cells.add((self.row_origins[data_row + 1], col))

    def _commitRecordEdits(self, refresh=True):
        if not self.record_edit_mode:
            return
        edited_values = self.record_view.getEditedValues()
        if edited_values:
            if len(edited_values) < len(self.headers):
                edited_values.extend([''] * (len(self.headers) - len(edited_values)))
            old_values = self.csv_data[self.current_record_index]
            changed = [c for c, v in enumerate(edited_values)
                       if v != (old_values[c] if c < len(old_values) else '')]
            if changed:
                self.csv_data[self.current_record_index] = edited_values
                for c in changed:
                    self._markCellDirty(self.current_record_index, c)
                self._markModified()
        self.record_edit_mode = False
        self.edit_record_btn.setText("Edit")
        self.record_view.edit_mode = False
        if refresh:
            self.displayCurrentRecord()

    def _toggleRecordEditMode(self):
        if not self.csv_data or self.current_view_mode != "record":
            return
        if not self.record_edit_mode:
            self.record_edit_mode = True
            self.edit_record_btn.setText("Done Editing")
            self.record_view.edit_mode = True
            self.displayCurrentRecord()
        else:
            self._commitRecordEdits()

    def saveFile(self):
        self._finishTableEdit()
        if self.record_edit_mode:
            self._commitRecordEdits()
        if not self.csv_data and not self.is_modified:
            return
        if not self.current_file_path:
            self.saveFileAs()
            return
        try:
            ext = os.path.splitext(self.current_file_path)[1].lower()
            if ext == '.xlsx':
                self._saveXLSX(self.current_file_path)
            else:
                self._saveCSV(self.current_file_path)
            self._markSaved()
            self.statusBar().showMessage("File saved", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save file: {str(e)}")

    def saveFileAs(self):
        if not self.csv_data and not self.xlsx_source:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File As",
            self.current_file_path or "",
            "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)"
        )
        if file_path:
            is_csv = os.path.splitext(file_path)[1].lower() != '.xlsx'
            if is_csv and self.xlsx_source and len(self.xlsx_source['sheets']) > 1:
                self._exportWorkbookCSV(file_path)
                return
            self.current_file_path = file_path
            self._updateTitle()
            self.saveFile()

    def _saveCSV(self, file_path):
        self._writeCSV(file_path, self.headers, self.csv_data)

    @staticmethod
    def _writeCSV(file_path, headers, data):
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(data)

    def _askCSVExportMode(self, sheet_count, sheet_name):
        """Ask how to export a multi-sheet workbook to CSV.
        Returns 'current', 'each' or None (cancel)."""
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("Export to CSV")
        text = (f"This workbook has {sheet_count} sheets, but a CSV file holds only one.\n\n"
                f"The workbook stays open; this is an export.")
        if self.is_modified:
            text += "\nYour workbook edits are still unsaved - use Save to keep them in the .xlsx file."
        box.setText(text)
        current_btn = box.addButton(f"Current Sheet ({sheet_name})", QMessageBox.ButtonRole.AcceptRole)
        each_btn = box.addButton("One File per Sheet", QMessageBox.ButtonRole.AcceptRole)
        box.addButton(QMessageBox.StandardButton.Cancel)
        box.setDefaultButton(current_btn)
        box.exec()
        clicked = box.clickedButton()
        if clicked is current_btn:
            return 'current'
        if clicked is each_btn:
            return 'each'
        return None

    def _confirmOverwrite(self, paths):
        names = "\n".join(os.path.basename(p) for p in paths[:8])
        if len(paths) > 8:
            names += f"\n... and {len(paths) - 8} more"
        reply = QMessageBox.question(
            self, "Replace Files?",
            f"These files already exist and will be replaced:\n\n{names}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        return reply == QMessageBox.StandardButton.Yes

    @staticmethod
    def _perSheetCSVPaths(file_path, sheet_names):
        """report.csv + ['Orders', 'Q1/Q2'] -> report_Orders.csv, report_Q1_Q2.csv"""
        base, ext = os.path.splitext(file_path)
        ext = ext or '.csv'
        paths, used = [], set()
        for name in sheet_names:
            safe = re.sub(r'[\\/:*?"<>|\s]+', '_', name).strip('._') or 'Sheet'
            candidate, n = f"{base}_{safe}{ext}", 2
            while candidate.lower() in used:
                candidate, n = f"{base}_{safe}_{n}{ext}", n + 1
            used.add(candidate.lower())
            paths.append(candidate)
        return paths

    def _exportWorkbookCSV(self, file_path):
        """Save As .csv for a multi-sheet workbook: export without leaving the workbook"""
        self._finishTableEdit()
        if self.record_edit_mode:
            self._commitRecordEdits()
        src = self.xlsx_source
        active_name = src['sheets'][src['active']]['name']
        mode = self._askCSVExportMode(len(src['sheets']), active_name)
        if mode is None:
            return
        try:
            if mode == 'current':
                self._saveCSV(file_path)
                self.statusBar().showMessage(
                    f"Exported sheet '{active_name}' to {os.path.basename(file_path)}", 5000)
                return

            self._stashActiveSheet()
            for i in range(len(src['sheets'])):
                self._ensureSheetLoaded(i)
            sheets = [s for s in src['sheets'] if s['headers'] or s['data']]
            skipped = len(src['sheets']) - len(sheets)
            paths = self._perSheetCSVPaths(file_path, [s['name'] for s in sheets])
            existing = [p for p in paths if os.path.exists(p)]
            if existing and not self._confirmOverwrite(existing):
                return
            for state, path in zip(sheets, paths):
                self._writeCSV(path, state['headers'], state['data'])
            msg = f"Exported {len(paths)} sheets to {os.path.dirname(os.path.abspath(file_path))}"
            if skipped:
                msg += f" ({skipped} empty sheet{'s' if skipped > 1 else ''} skipped)"
            self.statusBar().showMessage(msg, 8000)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export CSV: {str(e)}")

    def _saveXLSX(self, file_path):
        if not XLSX_SUPPORT_AVAILABLE:
            raise Exception("XLSX support requires the 'openpyxl' library.")
        if self.xlsx_source and os.path.exists(self.xlsx_source['path']):
            self._patchXLSX(file_path)
        else:
            self._writeNewXLSX(file_path)

    def _writeNewXLSX(self, file_path):
        """Write current data to a brand-new workbook (source was CSV)"""
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.append(self.headers)
        for row in self.csv_data:
            sheet.append([coerce_cell_value(v, None) for v in row])
        self._atomicSave(workbook, file_path)

    def _patchXLSX(self, file_path):
        """Re-open the source workbook and write only edited cells (on every
        sheet), so other sheets, formulas, formatting and value types are kept."""
        src = self.xlsx_source
        self._stashActiveSheet()
        workbook = openpyxl.load_workbook(src['path'])  # full mode: keeps formulas/styles

        written = []  # (state, {(sheet_row, col): value})
        for state in src['sheets']:
            if not state['dirty_cells']:
                continue
            sheet = workbook[state['name']]
            raw = state['raw']
            current = dict(zip(state['row_origins'], [state['headers']] + state['data']))
            values_written = {}
            for sheet_row, col in state['dirty_cells']:
                values = current.get(sheet_row)
                if values is None:
                    continue
                text = values[col] if col < len(values) else ''
                orig_row = raw[sheet_row - 1] if sheet_row - 1 < len(raw) else ()
                original = orig_row[col] if col < len(orig_row) else None
                fmt = state['formats'].get((sheet_row, col))
                value = coerce_cell_value(text, original, fmt)
                if not isinstance(value, str) and col < len(values):
                    values[col] = format_cell(value, fmt or 'General')  # show as Excel would
                sheet.cell(row=sheet_row, column=col + 1).value = value
                values_written[(sheet_row, col)] = value
            written.append((state, values_written))

        self._atomicSave(workbook, file_path)

        # The saved file is now the baseline for future saves
        for state, values_written in written:
            raw = state['raw']
            for (sheet_row, col), value in values_written.items():
                while len(raw) < sheet_row:
                    raw.append(())
                row = list(raw[sheet_row - 1])
                while len(row) <= col:
                    row.append(None)
                row[col] = value
                raw[sheet_row - 1] = tuple(row)
            state['dirty_cells'].clear()  # same set object as self.dirty_cells when active
        src['path'] = file_path
        if written:
            self.displayCurrentRecord()  # show saved cells in their Excel format

    def _atomicSave(self, workbook, file_path):
        """Save via a temp file in the same folder so a failed save
        never leaves a truncated workbook behind."""
        folder = os.path.dirname(os.path.abspath(file_path))
        fd, tmp_path = tempfile.mkstemp(suffix='.xlsx', dir=folder)
        os.close(fd)
        try:
            workbook.save(tmp_path)
            os.replace(tmp_path, file_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

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
            # Skip when in edit mode so keystrokes reach the QLineEdit fields
            if self.current_view_mode == "record" and not self.record_edit_mode:
                if event.key() == Qt.Key.Key_Left:
                    self.previousRecord()
                    return True
                elif event.key() == Qt.Key.Key_Right:
                    self.nextRecord()
                    return True
                elif event.key() == Qt.Key.Key_H:
                    self.selectCurrentRecordAsHeader()
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
    
    # Set application icon
    app.setWindowIcon(icons.app_icon())
    
    # Create and show the main window
    window = CSVReaderApp()
    window.show()
    
    # Fix Windows taskbar icon (no-op on other platforms)
    icons.set_taskbar_icon(window)
    
    # Check for command line arguments (file to open)
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            file_ext = file_path.lower()
            if file_ext.endswith('.csv') or file_ext.endswith('.xlsx'):
                window.loadDataFile(file_path)
            else:
                print(f"Error: Unsupported file type. Please provide a .csv or .xlsx file.")
    else:
        # Only load last viewed file if no command line argument
        window.loadLastViewedFile()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

