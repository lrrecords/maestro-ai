# start_maestro_session.ps1
# This script runs the Maestro AI session checklist, opens the dashboard in Brave, and launches FORGE (Open Interpreter with maestro profile).

# 1. Run the session checklist
Write-Host "Running session checklist..."
.\session_checklist.ps1

# 2. Open dashboard in Brave browser
$bravePaths = @(
    "$Env:ProgramFiles\BraveSoftware\Brave-Browser\Application\brave.exe",
    "$Env:ProgramFiles(x86)\BraveSoftware\Brave-Browser\Application\brave.exe"
)
$braveFound = $false
foreach ($path in $bravePaths) {
    if (Test-Path $path) {
        Start-Process -FilePath $path -ArgumentList 'http://127.0.0.1:8080'
        Write-Host "Opened Maestro-AI dashboard in Brave browser."
        $braveFound = $true
        break
    }
}
if (-not $braveFound) {
    Write-Host "Brave browser not found. Please open http://127.0.0.1:8080 manually."
}

# 3. Wait for user confirmation before launching FORGE
Read-Host "Press Enter to launch FORGE (Open Interpreter)..."

# 4. Launch FORGE (Open Interpreter with maestro profile, local Ollama)
Start-Process "D:\oi-env\Scripts\interpreter.exe" -ArgumentList "--profile maestro --local"
