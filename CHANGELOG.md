# Changelog

All notable changes to CSV Reader will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [0.1.5] - 2026-02-18 CST

### Changed
- **`run.ps1`**: Synced from Python-venv generic template
  - Added `# --- CONFIGURATION ---` block (`$AppName`, `$EntryPoint`, `$VenvDir`, `$Requirements`)
  - Status messages now include `[CSVreader]` prefix
- **`run.sh`**: Full rewrite to match `run.ps1` feature parity
  - Added `# --- CONFIGURATION ---` block
  - Added `test_venv_valid()` — reads `pyvenv.cfg` to check base Python still exists without invoking the venv
  - Added `find_python()` — tries `python3`, `python`, then common fixed paths (`/usr/bin/python3`, `/usr/local/bin/python3`, `~/.pyenv/shims/python3`)
  - Added broken venv detection: wipes and recreates venv if base Python is missing
  - Status messages now include `[CSVreader]` prefix
- **`csv-reader.py`**: Updated `VERSION` constant to `v0.1.5 2026-02-18 09:27 CST`; added v0.1.3/0.1.4/0.1.5 entries to header changelog
- **`README.md`**: Version line updated to v0.1.5
- **`WINDOWS-11-COMPATIBILITY.md`**: Version and Last Updated footer updated
- **`WINDOWS-INSTALLATION-GUIDE.md`**: Version and Last Updated footer updated
- **`Project_Rules.md`**: Added explicit table of all files requiring version updates on each release

## [0.1.4] - 2026-02-17 CST

### Fixed
- **`run.ps1`**: Detect and recreate broken venv before activation
  - Added `Test-VenvValid` helper that reads `pyvenv.cfg` to check whether the venv's base Python path still exists — without running any broken executable
  - If the venv points to a missing Python (e.g. created under a different user account), it is automatically wiped and recreated
  - Prevents the `No Python at '...'` error that occurred when activating a stale venv

## [0.1.3] - 2026-02-17 CST

### Fixed
- **`run.ps1`**: Robust Python detection when a stale or broken venv is activated
  - Added `Find-Python` helper that probes candidates in order: `py` launcher, common install paths, PATH python
  - Each candidate is verified by running `--version` before use, skipping shims that point to missing interpreters
  - Prevents failure caused by a venv created under a different user account or a moved Python installation

## [0.1.2] - 2026-02-16 16:39 CST

### Added
- **Edit Menu**: New Edit pull-down menu between File and View menus
  - Search... (Ctrl+F): Activates search functionality from any view mode
  - Automatically switches to Table View if in Record View
  - Focuses search input and selects existing text for quick replacement
- **`run.ps1`**: Windows PowerShell launcher — auto-creates venv, installs dependencies, and launches csv-reader
- Complements the existing `run.sh` for Linux/macOS/Git Bash users
- **`README.md`**: New project README with features, quick start for all platforms, keyboard shortcuts, and project structure

### Documentation
- `WINDOWS-INSTALLATION-GUIDE.md` updated to document `run.ps1` as an installation option

## [0.1.1] - 2026-02-01 18:42 CST

### Added
- **Icon Manager Module Integration**: Cross-platform icon management for consistent icon display
  - Integrated icon_loader.py module from Icon_Manager_Module
  - Generated platform-specific icons: app.ico (Windows), app.icns (macOS), multi-resolution PNGs (Linux)
  - Automatic OS-specific icon format selection
  - Windows taskbar icon fix via AppUserModelID + WM_SETICON
  - Graceful fallback chain: native format → sized PNGs → null icon with warnings
  - 4 lines of code changes across 1 file (csv-reader.py)
- Generated cross-platform icon assets from ICON_csv-reader-2.png source
  - app.ico (135 KB) - Multi-resolution Windows icon with 7 embedded sizes
  - app.icns (1.2 KB) - macOS dock icon
  - app.png (35.3 KB) - Linux default icon (256x256)
  - Individual resolution PNGs: 16x16, 24x24, 32x32, 48x48, 64x64, 128x128, 256x256

### Changed
- Updated csv-reader.desktop Icon path from ICON_csv-reader.png to app.png
- Icon loading now uses Icon Manager Module instead of direct QIcon(path)

## [0.1.0] - 2026-01-17 14:30 CST

### Added
- **Scroll Position Lock**: Scroll position is now preserved when navigating between records in Record View
  - Enables easy comparison of the same fields across different records
  - Position automatically maintained when using arrow keys or navigation buttons
- **Windows Executable**: Compiled standalone EXE file for Windows deployment
  - Built with PyInstaller using --onefile and --windowed options
  - Embedded application icon (ICON_csv-reader.ico)
  - Includes all dependencies (PyQt6, openpyxl, etc.)
  - No Python installation required on target system
  - File size: ~58MB
  - Download available at: https://drive.google.com/file/d/10FXUc7KbMLFsl2dUwSSt81OxmMuI1ibC/view?usp=sharing

### Changed
- **Quick Reference Dialog**: Now uses scrollable dialog instead of message box
  - Content is fully accessible regardless of window size
  - Uses QTextBrowser for improved HTML rendering
- Updated Quick Reference to document Scroll Position Lock and Dynamic Header Selection features

## [0.0.5] - 2026-01-09

### Added
- **Dynamic Header Selection**: Users can now select any row as the header in Record View
  - Press 'H' key in Record View to select current record as header
  - Preview dialog shows current header vs. new header in horizontal table format
  - Confirmation required before applying change
  - Original header becomes first data row
  - All rows before selected row remain as data rows
  - Selected row becomes new header and is removed from data
  - Headers automatically reset to first row when file is reopened
  - Single-row protection: prevents operation when only one data row exists
  - Handles column count mismatches with automatic padding

### Changed
- Updated Quick Reference to include 'H' key shortcut and Dynamic Header Selection feature
- Version bumped to v0.0.5 2026-01-09 10:45 CST

## [0.0.4] - 2026-01-08

### Added
- **XLSX File Support**: Application now supports Excel .xlsx files
  - Uses openpyxl library for parsing Excel files
  - Loads first sheet only from multi-sheet workbooks
  - Maintains same data structure and UI behavior as CSV files
  - Graceful error handling when openpyxl not installed
- Updated file dialogs to accept both .csv and .xlsx files
- Command-line argument support extended to .xlsx files
- XLSX files tracked in recent files alongside CSV files
- **Application Icon**: Set window icon using icons/ICON_csv-reader.png
- **Changelog Menu Item**: New "Changelog" option in Help menu that displays CHANGELOG.md content
- **Icons Directory**: Added three PNG icon files (ICON_csv-reader.png, ICON_csv-reader-1.png, ICON_csv-reader-2.png)
- **Desktop File**: csv-reader.desktop for system menu integration
- **Windows 11 Compatibility Guide**: WINDOWS-11-COMPATIBILITY.md with comprehensive Windows deployment documentation
- **requirements.txt**: Added dependency file listing PyQt6 and openpyxl

### Changed
- Window title updated from "CSV Reader" to "CSV/XLSX Reader"
- File dialogs now show "Open Data File" instead of "Open CSV File"
- Error messages now say "Failed to load file" instead of "Failed to load CSV file"
- Quick Reference and About dialogs updated to reflect multi-format support

### Fixed
- **Desktop File Integration**: Fixed csv-reader.desktop to properly handle CSV files from file manager
  - Changed %U to %F for better local file handling
  - Corrected argument order (script path before %F)
  - Now properly opens CSV files when selected from file manager right-click menu

### Dependencies
- openpyxl: Required for .xlsx file support (install: pip install openpyxl)

## [0.0.3] - 2025-12-12

### Added
- Command line argument support: Application can now be launched with a CSV file path as argument
  - Opens specified CSV file on startup when file path provided
  - Falls back to loading last viewed file when no argument provided

### Changed
- Deferred auto-load of last viewed file to after window is shown for better startup behavior
- Version updated to v0.0.3 with timestamp 2025-12-12 01:45

## [0.0.2] - 2025-12-11

### Added
- **Table Search Feature**: Comprehensive search functionality in Table View
  - Search bar with text input and navigation controls
  - Case-insensitive search across all table cells
  - Visual highlighting of search results (yellow for matches, orange for current)
  - "Find", "Next", "Previous", and "Clear" buttons
  - Result counter showing current match position
  - Auto-scroll to current match
  - Enter key support in search field
- **Help Menu**: New menu with Quick Reference and About dialogs
  - Quick Reference (F1): Comprehensive guide covering view modes, navigation, keyboard shortcuts, and features
  - About CSV Reader: Version information, feature list, and copyright notice
- Search toggle button in Table View toolbar

### Changed
- Left-aligned column headers in Table View for improved readability
- Removed F1/F2 keyboard shortcuts from view switching to avoid conflicts
- F1 now opens Quick Reference help dialog
- Search controls only visible in Table View
- Version updated to v0.0.2 with timestamp 2025-12-11 18:25

### Fixed
- Keyboard shortcut conflicts resolved

## [0.0.1] - 2025-12-11

### Added
- Initial release of CSV Reader application
- PyQt6-based desktop application for viewing CSV files
- Two view modes:
  - **Record View**: Display one CSV record at a time with vertical field layout
  - **Table View**: Display all CSV data in spreadsheet format
- Navigation features:
  - Arrow keys (Left/Right) to navigate between records in Record View
  - Click table cells to jump to that record in Record View
- Keyboard shortcuts:
  - Ctrl+T: Toggle between views
  - Ctrl+MouseWheel: Zoom in/out (40%-300%)
- Recent files menu (tracks last 10 files)
- Auto-load last viewed CSV file on startup
- Settings persistence via Windows registry (QSettings)
- Fully qualified file paths displayed in:
  - Window title bar
  - Recent files menu
- Version information displayed in status bar
- PyInstaller build configuration (CSV-Reader.spec)
- WARP.md documentation for Warp AI integration

### Features
- Read-only CSV viewing with UTF-8 encoding
- Sortable columns in Table View
- Selectable text in Record View
- Word wrapping for long content
- Auto-resize columns to content
- Independent zoom levels for each view mode

[0.1.5]: https://github.com/juren53/csv-reader/releases/tag/v0.1.5
[0.1.4]: https://github.com/juren53/csv-reader/releases/tag/v0.1.4
[0.1.3]: https://github.com/juren53/csv-reader/releases/tag/v0.1.3
[0.1.2]: https://github.com/juren53/csv-reader/releases/tag/v0.1.2
[0.1.1]: https://github.com/juren53/csv-reader/releases/tag/v0.1.1
[0.1.0]: https://github.com/juren53/csv-reader/releases/tag/v0.1.0
[0.0.5]: https://github.com/juren53/csv-reader/releases/tag/v0.0.5
[0.0.4]: https://github.com/juren53/csv-reader/releases/tag/v0.0.4
[0.0.3]: https://github.com/juren53/csv-reader/releases/tag/v0.0.3
[0.0.2]: https://github.com/juren53/csv-reader/releases/tag/v0.0.2
[0.0.1]: https://github.com/juren53/csv-reader/releases/tag/v0.0.1
