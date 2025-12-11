# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

CSV Reader is a PyQt6-based desktop application for viewing and navigating CSV files. The application provides two view modes:
- **Record View**: Displays one CSV record at a time with fields shown vertically (header-value pairs)
- **Table View**: Displays all CSV data in a traditional spreadsheet-like table

The entire application is contained in a single file (`csv-reader.py`) with no external configuration or dependency files tracked in the repository.

## Development Commands

### Running the Application
```powershell
python csv-reader.py
```

### Building Executable (PyInstaller)
```powershell
# Build using the spec file
pyinstaller CSV-Reader.spec

# The executable will be in the dist/ directory
```

### Required Dependencies
The application requires:
- Python 3.x
- PyQt6
- PyInstaller (for building executables)

Install dependencies:
```powershell
pip install PyQt6 pyinstaller
```

## Architecture

### Single-File Design
The entire application is in `csv-reader.py` (~680 lines). This monolithic structure means:
- All changes will be in one file
- No module imports or package structure
- Direct class instantiation without factory patterns

### Key Classes

**CSVReaderApp (QMainWindow)** - Lines 194-664
- Main application window and orchestrator
- Manages file I/O, recent files, and application settings via QSettings
- Coordinates between RecordView and TableView
- Handles global keyboard events (arrow keys for navigation, Ctrl+wheel for zoom)
- Manages view mode switching (F1/F2 keys or Ctrl+T to toggle)

**RecordView (QScrollArea)** - Lines 106-192
- Displays a single CSV record vertically using QGridLayout
- Column 0: header labels (bold, right-aligned)
- Column 1: values (left-aligned, word-wrapped, selectable)
- Supports independent zoom levels (40%-300%)

**TableView (QTableWidget)** - Lines 25-104
- Displays all CSV data in spreadsheet format
- Read-only, sortable columns
- Double-clicking a row switches to RecordView for that record
- Supports independent zoom levels (40%-300%)

### Data Flow
1. CSV file loaded via `loadCSVFile()` - reads entire file into memory
2. First row extracted as headers, remaining rows stored as data
3. Data displayed via either `RecordView.displayRecord()` or `TableView.displayData()`
4. Navigation in RecordView updates `current_record_index` and refreshes display

### Navigation & Controls
- **Arrow Keys** (Left/Right): Navigate records in RecordView only
- **Ctrl+MouseWheel**: Zoom in/out (each view maintains its own zoom level)
- **F1/F2**: Switch between Record and Table view
- **Ctrl+T**: Toggle between views
- **Clicking table cell**: Switches to RecordView for that row

### Settings Persistence
Uses QSettings with organization "CSVReader" and application "csv-reader":
- Recent files list (max 10 files)
- Stored in Windows registry under HKEY_CURRENT_USER\Software\CSVReader\csv-reader

## Important Implementation Notes

### When Adding Features
- All UI elements are created in `initUI()` (lines 222-354)
- Global event filtering happens in `eventFilter()` (lines 616-642) - this is where keyboard shortcuts are intercepted
- Both views support zoom independently - ensure zoom functionality is updated for both if modifying zoom behavior

### CSV Handling
- Uses Python's built-in `csv` module (not pandas)
- Files are read with UTF-8 encoding
- Empty cells are handled by padding rows with empty strings
- No validation of CSV structure beyond checking for empty files

### PyQt6 Specifics
- Uses PyQt6 (not PyQt5) - enum syntax differs (e.g., `Qt.AlignmentFlag.AlignLeft`)
- Event filter installed at application level to catch all keyboard events
- QSettings automatically handles Windows registry persistence

### Version Information
The version string is hardcoded in `CSVReaderApp.VERSION` (line 198) and displayed in the status bar.
