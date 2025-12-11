# Changelog

All notable changes to CSV Reader will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

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
  - F1: Switch to Record View
  - F2: Switch to Table View
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

[0.0.1]: https://github.com/yourusername/csv-reader/releases/tag/v0.0.1
