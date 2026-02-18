# CSV Reader Windows Installation Guide

This guide helps you install CSV Reader on Windows 11 for desktop integration.

## Quick Installation

### Option 1: Using the Executable (Recommended)
1. Navigate to the `dist` folder
2. Copy `CSV Reader.exe` to your desired location (e.g., `C:\Program Files\CSV Reader\`)
3. Double-click `CSV Reader.exe` to launch the application

### Option 2: Using PowerShell (run.ps1)
1. Open PowerShell in the project directory
2. Run `.\run.ps1` — auto-creates a venv, installs dependencies, and launches the app
3. If blocked by execution policy, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once first

### Option 3: Using the Batch File
1. Ensure you have Python installed with PyQt6
2. Double-click `csv-reader.bat` to launch the application

## Desktop Integration

### Create Desktop Shortcut
1. Right-click on `CSV Reader.exe` 
2. Select "Send to" > "Desktop (create shortcut)"
3. Right-click the new shortcut and select "Properties"
4. Click "Change Icon..." and browse to `icons\ICON_csv-reader.ico`
5. Click "Apply" then "OK"

### Set Up File Associations
1. Double-click `install-file-association.reg`
2. Confirm the registry changes when prompted
3. Now CSV files will open with CSV Reader by default

**Manual File Association:**
If the registry file doesn't work, follow these steps:
1. Right-click any CSV file
2. Select "Open with" > "Choose another app"
3. Check "Always use this app to open .csv files"
4. Browse to and select `CSV Reader.exe`

## Start Menu Integration

### Add to Start Menu
1. Press `Win + R` and type `shell:programs`
2. Create a new folder named "CSV Reader"
3. Copy the `CSV Reader.exe` shortcut to this folder
4. Rename it to just "CSV Reader"

## Testing the Installation

### Basic Functionality Test
1. Launch CSV Reader using your preferred method
2. Click "File" > "Open" and select `short.csv`
3. Test both view modes:
   - **Record View**: Use arrow keys to navigate
   - **Table View**: Click column headers to sort
4. Test search functionality in Table View
5. Test zoom with `Ctrl + Mouse Wheel`

### File Association Test
1. Double-click any CSV file in Windows Explorer
2. Verify it opens with CSV Reader
3. Test opening multiple CSV files

## Troubleshooting

### Common Issues

**"Python not found" Error:**
- Use the executable version instead of the batch file
- Or install Python and add it to your PATH

**"PyQt6 not found" Error:**
- Install PyQt6: `pip install PyQt6`
- Use the executable version which includes all dependencies

**File associations not working:**
- Run `install-file-association.reg` as Administrator
- Manually set file associations through Windows Settings

**Icon not displaying:**
- Ensure the ICO file is in the correct location
- Re-create the shortcut and select the icon manually

### Performance Tips

**For large CSV files:**
- Use Table View for better performance with thousands of rows
- Enable search to quickly find specific data
- Use zoom to adjust text size for better readability

**Memory usage:**
- Close CSV Reader when not in use
- Avoid opening very large files (>100MB) on systems with limited RAM

## Advanced Configuration

### Portable Installation
1. Copy the entire `csv-reader` folder to a USB drive
2. Use `csv-reader.bat` for portable operation
3. Settings will be stored in the Windows registry on each PC

### Network Installation
1. Place `CSV Reader.exe` on a network share
2. Create shortcuts pointing to the network location
3. Ensure all users have read access to the executable

## Uninstallation

### Remove File Associations
1. Open `Settings` > `Apps` > `Default apps`
2. Find CSV file type and change default app
2. Or run `regedit` and delete the `CSVReader.csv` keys

### Remove Application
1. Delete the application folder
2. Remove desktop and Start Menu shortcuts
3. Clear any registry entries if desired

## Support

For issues and feature requests:
- Check the changelog for known issues
- Report problems on the GitHub repository
- Review the help documentation in the application (Help menu)

---

**Version:** v0.1.6
**Last Updated:** 2026-02-18
**Platform:** Windows 11