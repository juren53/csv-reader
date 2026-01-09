@echo off
REM CSV Reader Launcher for Windows
REM This batch file launches the CSV Reader application

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

REM Use the Windows Store Python to run the application
C:\Users\jimur\AppData\Local\Microsoft\WindowsApps\python.exe "%SCRIPT_DIR%csv-reader.py" %*

REM If the application exits with an error, pause to see the message
if errorlevel 1 (
    echo.
    echo CSV Reader encountered an error. Press any key to exit...
    pause >nul
)