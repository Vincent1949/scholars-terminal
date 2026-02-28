# PowerShell Script to Create Scholar's Terminal Desktop Shortcut

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Creating Scholar's Terminal Shortcut" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Paths
$BatchFile = "D:\Claude\Projects\scholars-terminal\launch_scholars_terminal.bat"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Scholar's Terminal.lnk"

# Create shortcut
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $BatchFile
$Shortcut.WorkingDirectory = "D:\Claude\Projects\scholars-terminal"
$Shortcut.Description = "Launch Scholar's Terminal - RAG Knowledge Base"
$Shortcut.IconLocation = "shell32.dll,265"  # Book icon
$Shortcut.Save()

Write-Host "✅ Shortcut created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Location: $ShortcutPath" -ForegroundColor Yellow
Write-Host ""
Write-Host "You can now double-click 'Scholar's Terminal' on your desktop!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
