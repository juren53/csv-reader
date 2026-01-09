# PowerShell script to create CSV Reader shortcut
# Run this script as administrator to create desktop shortcut

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ShortcutPath = "$env:USERPROFILE\Desktop\CSV Reader.lnk"
$TargetPath = "$ScriptDir\csv-reader.bat"
$IconLocation = "$ScriptDir\icons\ICON_csv-reader.ico"

# Create Shell Object
$WScriptShell = New-Object -ComObject WScript.Shell

# Create Shortcut
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = $ScriptDir
$Shortcut.IconLocation = $IconLocation
$Shortcut.Description = "CSV Reader - View CSV files in record or table format"

# Save Shortcut
$Shortcut.Save()

Write-Host "Shortcut created successfully at: $ShortcutPath"
Write-Host "You can now double-click the desktop shortcut to launch CSV Reader"