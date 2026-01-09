# PowerShell script to create CSV Reader shortcut in current directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ShortcutPath = "$ScriptDir\CSV Reader.lnk"
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
Write-Host "You can move this shortcut to your Desktop or Start Menu"