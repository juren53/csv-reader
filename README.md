# CSV Reader

**Version:** v0.1.9 (2026-11-26)

A PyQt6-based application for viewing CSV and XLSX files with dual view modes — record-by-record or spreadsheet table.

## Features

- **Dual view modes**
  - **Record View**: Displays one record at a time with field names as labels (vertical layout)
  - **Table View**: Spreadsheet-style view with sortable columns
- **CSV and XLSX support**: Opens `.csv` and `.xlsx` files; multi-sheet workbooks get Excel-style sheet tabs; formula cells are read-only; Save As CSV can export one sheet or every sheet
- **Dynamic header selection**: Press `H` in Record View to reassign any row as the header
- **Search**: `Ctrl+F` searches across all cells in Table View with match highlighting
- **Zoom**: `Ctrl+MouseWheel` adjusts text size (40%–300%) independently per view
- **Recent files**: Tracks last 10 opened files; auto-loads last viewed file on startup
- **Scroll position lock**: Preserves scroll position when navigating between records
- **Cross-platform icons**: Platform-aware icon loading (Windows `.ico`, macOS `.icns`, Linux `.png`)
- **Command-line support**: Open a file directly from the terminal

## Requirements

- Python 3.8+
- PyQt6
- openpyxl (for `.xlsx` support)

## Installation

### Quick Start

**Linux / macOS / Git Bash:**
```bash
git clone https://github.com/juren53/csv-reader.git
cd csv-reader
./run.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/juren53/csv-reader.git
cd csv-reader
.\run.ps1
```

Both launchers auto-create a virtual environment, install dependencies, and launch the app. If PowerShell blocks `run.ps1`, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once first.

### Manual Setup
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python csv-reader.py
```

### Windows Executable
A standalone Windows 11 executable (no Python required) is available at:

https://github.com/juren53/csv-reader/releases

**Direct download (always the newest build):** [csv-reader.exe](https://github.com/juren53/csv-reader/releases/latest/download/csv-reader.exe)

**Latest release:** [v0.1.9](https://github.com/juren53/csv-reader/releases/tag/v0.1.9) — Multi-sheet XLSX with sheet tabs, Save keeps workbooks intact, read-only formula cells, CSV export per sheet

See `WINDOWS-INSTALLATION-GUIDE.md` for installation and file-association details.

## Usage

```bash
# Open the app
./run.sh              # Linux/macOS
.\run.ps1             # Windows PowerShell

# Open a file directly
python csv-reader.py mydata.csv
python csv-reader.py mydata.xlsx
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open file |
| `Ctrl+F` | Search (Table View) |
| `Ctrl+T` | Toggle Record / Table view |
| `Ctrl+PgDn` / `Ctrl+PgUp` | Next / previous sheet (multi-sheet XLSX) |
| `Ctrl+MouseWheel` | Zoom in / out |
| `Left / Right` | Previous / Next record (Record View) |
| `H` | Set current record as header row (Record View) |
| `F1` | Quick Reference |
| `Ctrl+Q` | Quit |

## Project Structure

```
csv-reader/
├── csv-reader.py               # Application entry point
├── icon_loader.py              # Cross-platform icon loader
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Test dependencies (pytest)
├── tests/                      # pytest suite (headless)
├── run.sh                      # Linux/macOS/Git Bash launcher
├── run.ps1                     # Windows PowerShell launcher
├── csv-reader.bat              # Windows batch launcher
├── icons/                      # Application icon assets
├── CHANGELOG.md                # Version history
└── WINDOWS-INSTALLATION-GUIDE.md  # Windows setup and deployment guide
```

## Running Tests

The test suite runs the app headless (no window appears) and never touches your saved settings or recent-files list.

```bash
pip install -r requirements-dev.txt
python -m pytest
```

On Windows use `venv\Scripts\python -m pytest`; on Linux/macOS `venv/bin/python -m pytest`.

## Version History

See [CHANGELOG.md](CHANGELOG.md) for full version history.

## License

MIT License
