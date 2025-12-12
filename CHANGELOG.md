# Changelog

All notable changes to CSV Reader will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Command line argument support: Application can now be launched with a CSV file path as argument
  - Opens specified CSV file on startup when file path provided
  - Falls back to loading last viewed file when no argument provided

### Changed
- Deferred auto-load of last viewed file to after window is shown for better startup behavior

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

[0.0.2]: https://github.com/juren53/csv-reader/releases/tag/v0.0.2
[0.0.1]: https://github.com/juren53/csv-reader/releases/tag/v0.0.1
