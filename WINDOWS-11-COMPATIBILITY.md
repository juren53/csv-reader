# Windows 11 Compatibility Guide

This document outlines the considerations and requirements for running CSV Reader on Windows 11 systems.

## Current Status

The core Python application is cross-platform and should work on Windows 11 with minimal modifications. However, the desktop integration methods differ between Linux and Windows.

## Linux vs Windows Desktop Integration

### Linux (Current Implementation)
- **Desktop File**: `csv-reader.desktop` for system menu integration
- **File Association**: MIME type handling through desktop file
- **Icon Path**: Direct file path to PNG icon
- **Execution**: `python3 script.py %F`

### Windows 11 (Required Implementation)
- **File Association**: Registry entries for `.csv` extension
- **Shortcut**: Windows shortcut (.lnk) file
- **Icon Path**: Embedded in executable or separate ICO file
- **Execution**: `python script.py %1` or standalone executable

## Windows 11 Implementation Requirements

### 1. File Association Setup
```reg
[HKEY_CLASSES_ROOT\.csv]
@="CSVReader.csv"

[HKEY_CLASSES_ROOT\CSVReader.csv]
@="CSV File"

[HKEY_CLASSES_ROOT\CSVReader.csv\shell\open\command]
@="\"C:\\Path\\To\\csv-reader.exe\" \"%1\""
```

### 2. Windows Shortcut (.lnk)
- Create shortcut to Python script or executable
- Set appropriate icon file
- Place in user's Start Menu or Desktop

### 3. Python Script Considerations
The current `csv-reader.py` should work on Windows 11 with these considerations:

#### Path Handling
- ✅ Already using `os.path.join()` - cross-platform compatible
- ✅ Uses proper path separators automatically

#### Python Executable
- Windows users need `python` in system PATH
- Consider bundling Python with application

#### GUI Framework
- ✅ PyQt6 is fully compatible with Windows 11
- ✅ Cross-platform Qt framework

#### Settings Storage
- Current implementation uses QSettings
- Windows: Uses registry automatically
- Linux: Uses configuration files

## Recommended Windows Distribution Methods

### Option 1: PyInstaller Executable
```bash
# Create standalone executable
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icons/ICON_csv-reader.ico csv-reader.py
```

**Benefits:**
- No Python installation required
- Single file distribution
- Professional appearance

### Option 2: Installer Package
- Use NSIS, Inno Setup, or similar
- Handles file associations automatically
- Creates Start Menu entries
- Manages uninstallation

### Option 3: Portable Distribution
- ZIP file with Python script and dependencies
- Batch file for launching
- Manual file association instructions

## Windows-Specific Code Changes (If Needed)

### 1. Icon File Format
- Convert PNG to ICO format for Windows
- Update icon loading code if using executable

### 2. Error Handling
- Add Windows-specific error messages
- Handle Windows path edge cases

### 3. Installation Detection
- Detect if running from installed location
- Handle portable vs installed modes

## Testing Checklist for Windows 11

- [ ] Application launches from shortcut
- [ ] CSV files open via double-click
- [ ] Right-click "Open with" works
- [ ] Icon displays correctly
- [ ] Settings persist between sessions
- [ ] Recent files menu works
- [ ] Help dialogs display properly
- [ ] All keyboard shortcuts function

## Development Workflow

1. **Test on Linux** (current environment)
2. **Test on Windows 11** (when available)
3. **Create Windows distribution package**
4. **Test installation and file associations**
5. **Document Windows-specific installation steps**

## Notes

- The core application logic requires minimal changes for Windows compatibility
- Most differences are in desktop integration and distribution methods
- Consider creating separate documentation for Windows users
- Test on different Windows versions if possible

---

**Last Updated:** 2025-12-12  
**Version:** v0.0.3  
**Platform:** Cross-platform (Linux primary, Windows 11 target)