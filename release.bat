@echo off
setlocal enabledelayedexpansion

echo ============================================
echo  CSV-Reader Release Script
echo ============================================
echo.

REM --- Step 1: Read version from csv-reader.py ---
REM VERSION format is: VERSION = "v0.1.1  2026-02-01  18:42 CST"
for /f "tokens=3 delims= " %%a in ('findstr /C:"VERSION = " csv-reader.py') do (
    set "RAW=%%a"
    goto :got_version
)
:got_version
REM Trim quotes and leading 'v'
set "RAW=%RAW:"=%"
set "VERSION=%RAW:v=%"
echo [1/7] Version detected: v%VERSION%
echo.

REM --- Step 2: Check for uncommitted changes ---
echo [2/7] Checking for uncommitted changes...
git diff --quiet 2>nul
if errorlevel 1 (
    echo WARNING: You have uncommitted changes!
    echo Commit or stash them before releasing.
    echo.
    git status --short
    echo.
    set /p CONTINUE="Continue anyway? (y/N): "
    if /i not "!CONTINUE!"=="y" (
        echo Aborted.
        exit /b 1
    )
)
echo       Working tree is clean.
echo.

REM --- Step 3: Push latest commits ---
echo [3/7] Pushing latest commits to GitHub...
git push origin main
echo.

REM --- Step 4: Build the executable ---
echo [4/7] Building executable with PyInstaller...
set "VENV_PYTHON=%~dp0venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
    echo ERROR: Virtual environment not found. Run .\run.ps1 first to create it.
    exit /b 1
)
REM Ensure PyInstaller is installed in the venv (no-op if already present)
"%VENV_PYTHON%" -m pip install pyinstaller --quiet
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller into the venv.
    exit /b 1
)
if exist build rmdir /s /q build
if exist dist\csv-reader.exe del /f dist\csv-reader.exe
"%VENV_PYTHON%" -m PyInstaller --clean --noconfirm CSV-Reader.spec
if not exist dist\csv-reader.exe (
    echo ERROR: Build failed! dist\csv-reader.exe not found.
    exit /b 1
)
echo       Build successful.
echo.

REM --- Step 5: Create git tag ---
echo [5/7] Creating git tag v%VERSION%...
git tag -a v%VERSION% -m "Release v%VERSION%"
if errorlevel 1 (
    echo WARNING: Tag v%VERSION% may already exist.
    set /p OVERWRITE="Delete and recreate tag? (y/N): "
    if /i "!OVERWRITE!"=="y" (
        git tag -d v%VERSION%
        git push origin :refs/tags/v%VERSION%
        git tag -a v%VERSION% -m "Release v%VERSION%"
    ) else (
        echo Continuing with existing tag...
    )
)
git push origin v%VERSION%
echo.

REM --- Step 6: Extract changelog and create GitHub Release ---
echo [6/7] Creating GitHub Release with binary...

REM Extract changelog section for this version into a temp file
REM (PowerShell regex: everything after "## [VERSION]" up to the next "## [" header)
powershell -NoProfile -Command "$c = Get-Content -Raw -Encoding UTF8 CHANGELOG.md; $m = [regex]::Match($c, '(?ms)^## \[' + [regex]::Escape('%VERSION%') + '\][^\n]*\n(.*?)(?=^## \[|\z)'); $n = $m.Groups[1].Value.Trim() + \"`n`n## Download`n[csv-reader.exe](https://github.com/juren53/csv-reader/releases/download/v%VERSION%/csv-reader.exe) - standalone Windows 11 executable, no Python required.`n\"; [IO.File]::WriteAllText('release_notes_temp.md', $n)"
for %%F in (release_notes_temp.md) do if %%~zF LSS 200 (
    echo WARNING: No CHANGELOG.md section found for [%VERSION%] - release notes will be minimal.
)

REM Create the release
gh release create v%VERSION% ^
    --title "CSV-Reader v%VERSION%" ^
    --notes-file release_notes_temp.md ^
    dist\csv-reader.exe

del release_notes_temp.md 2>nul
echo.

REM --- Step 7: Deploy to local bin ---
echo [7/7] Deploying to ~\bin\CSV-Reader.exe...
copy /y dist\csv-reader.exe "%USERPROFILE%\bin\CSV-Reader.exe"
echo.

echo ============================================
echo  Release v%VERSION% complete!
echo ============================================
echo.
echo  Tag:     v%VERSION%
echo  Release: https://github.com/juren53/csv-reader/releases/tag/v%VERSION%
echo  Binary:  %USERPROFILE%\bin\CSV-Reader.exe
echo.
pause
