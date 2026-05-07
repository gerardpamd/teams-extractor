$ErrorActionPreference = "Stop"

# Run once in PowerShell (no admin needed) to register the Teams Extractor native messaging host.
# Usage: powershell -ExecutionPolicy Bypass -File register.ps1

$hostDir  = "C:\teams-extractor-host"
$jsonPath = "$hostDir\com.teams_extractor.writer.json"
$regKey   = "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\com.teams_extractor.writer"

# Resolve WSL username from the UNC path of this script (avoids hanging wsl.exe call)
# Path is like \\wsl.localhost\Ubuntu\home\<user>\...
if ($PSScriptRoot -match '\\wsl\.localhost\\[^\\]+\\home\\([^\\]+)') {
    $wslUser = $Matches[1]
} else {
    # Fallback: prompt rather than hang
    $wslUser = Read-Host "Enter your WSL username"
}
if (-not $wslUser) { throw "Could not determine WSL username." }

# Create host directory
if (-not (Test-Path $hostDir)) { New-Item -ItemType Directory -Path $hostDir | Out-Null }

# Generate run_host.bat with the correct WSL path for this machine
@"
@echo off
wsl.exe python3 /home/$wslUser/teams-extractor/native-host/teams_writer.py
"@ | Set-Content "$hostDir\run_host.bat" -Encoding ASCII

# Copy host manifest
Copy-Item -Path "$PSScriptRoot\com.teams_extractor.writer.json" -Destination $jsonPath -Force

# Register registry key
New-Item -Path $regKey -Force | Out-Null
Set-ItemProperty -Path $regKey -Name "(Default)" -Value $jsonPath

Write-Host "Registered native messaging host."
Write-Host "  WSL user  : $wslUser"
Write-Host "  Host dir  : $hostDir"
Write-Host "  Registry  : $regKey"
Write-Host ""
Write-Host "NEXT STEPS:"
Write-Host "  1. Load the extension in Edge: edge://extensions/ -> Load unpacked -> select the extension/ folder"
Write-Host "  2. Copy your extension ID from edge://extensions/"
Write-Host "  3. Edit $jsonPath and replace REPLACE_WITH_EXTENSION_ID with your extension ID"
Write-Host "  4. Re-run this script to re-register with the updated JSON"
