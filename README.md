# CSV Reader

**Version:** v0.1.2 (2026-02-16)

A PyQt6-based application for viewing CSV and XLSX files with dual view modes — record-by-record or spreadsheet table.

## Features

- **Dual view modes**
  - **Record View**: Displays one record at a time with field names as labels (vertical layout)
  - **Table View**: Spreadsheet-style view with sortable columns
- **CSV and XLSX support**: Opens `.csv` and `.xlsx` files (first sheet)
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
A standalone `.exe` (no Python required) is available — see `WINDOWS-INSTALLATION-GUIDE.md` for details.

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
├── run.sh                      # Linux/macOS/Git Bash launcher
├── run.ps1                     # Windows PowerShell launcher
├── csv-reader.bat              # Windows batch launcher
├── icons/                      # Application icon assets
├── CHANGELOG.md                # Version history
└── WINDOWS-INSTALLATION-GUIDE.md  # Windows setup and deployment guide
```

## Version History

See [CHANGELOG.md](CHANGELOG.md) for full version history.

## License

MIT License
