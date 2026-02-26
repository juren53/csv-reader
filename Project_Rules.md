# Project Rules

## Timezone Convention

**CRITICAL**: ALL timestamps, dates, and times in this project MUST use Central Time USA (CST/CDT), NEVER UTC or any other timezone.

This applies to:

- Changelog entries in source code headers
- Version labels and dates in the UI
- Git commit messages (if applicable)
- Documentation timestamps
- Any other date/time references in the project

Example formats:

- Changelog: `Tue 03 Dec 2025 09:20:00 PM CST`
- Version label: `v0.0.9b 2025-12-03`
- Always include timezone indicator (CST or CDT) in full timestamps

## Version Numbering

- Format: `v0.0.X` for releases
- Format: `v0.0.Xa`, `v0.0.Xb`, `v0.0.Xc` for point releases/patches
- Version info consists of: Version Number + Date + Time (CST/CDT). Example: `v0.1.5  2026-02-18  09:27 CST`

### Files that MUST be updated on every release

| File | What to update |
|------|---------------|
| `csv-reader.py` | Header changelog block (add new entry) + `VERSION = "..."` constant |
| `README.md` | `**Version:**` line near top |
| `CHANGELOG.md` | New version section + tag link at bottom |
| `WINDOWS-11-COMPATIBILITY.md` | `**Version:**` and `**Last Updated:**` footer |
| `WINDOWS-INSTALLATION-GUIDE.md` | `**Version:**` and `**Last Updated:**` footer |

After updating files: commit, tag (`git tag vX.X.X`), push tag, create GitHub release.

## Compiling Instructions

- compile csv-reader to make a single executable EXE file CSV-Reader.spec
