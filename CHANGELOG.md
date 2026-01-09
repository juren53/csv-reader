# Changelog

All notable changes to CSV Reader will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

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

[0.0.4]: https://github.com/juren53/csv-reader/releases/tag/v0.0.4
[0.0.3]: https://github.com/juren53/csv-reader/releases/tag/v0.0.3
[0.0.2]: https://github.com/juren53/csv-reader/releases/tag/v0.0.2
[0.0.1]: https://github.com/juren53/csv-reader/releases/tag/v0.0.1
