# PowerShell script to prioritize WindowsApps Python over msys64 Python
# Run this as Administrator if you want to modify system PATH, or as regular user for user PATH

# Get current user PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

# Define the paths
$windowsAppsPython = "C:\Users\jimur\AppData\Local\Microsoft\WindowsApps"
$msys64Python = "C:\msys64\mingw64\bin"

# Split into array
$pathArray = $currentPath -split ';'

# Remove both Python paths if they exist
$pathArray = $pathArray | Where-Object { $_ -ne $windowsAppsPython -and $_ -ne $msys64Python }

# Add WindowsApps first, then msys64
$newPathArray = @($windowsAppsPython) + $pathArray + @($msys64Python)

# Join back together
$newPath = $newPathArray -join ';'

# Set the new PATH
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")

Write-Host "PATH updated successfully!" -ForegroundColor Green
Write-Host "Please restart PowerShell for changes to take effect." -ForegroundColor Yellow
Write-Host ""
Write-Host "New PATH order (first 5 entries):" -ForegroundColor Cyan
($newPath -split ';')[0..4] | ForEach-Object { Write-Host "  $_" }
