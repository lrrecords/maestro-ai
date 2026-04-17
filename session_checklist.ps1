# Session Checklist for Maestro AI

$projectDir = "C:\Users\brett\Documents\maestro-ai"
$releasesFile = Join-Path $projectDir "RELEASES.md"
$dashboardCmd = "python dashboard/app.py"

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "SESSION CHECKLIST RESULTS"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Git status and log
Write-Host "`nGit status:"
git -C $projectDir status

Write-Host "`nLast 3 commits:"
git -C $projectDir log --oneline -3

# 2. Start dashboard, check endpoint
Write-Host "`nStarting dashboard and checking endpoint..."
$dashboard = Start-Process -FilePath "python" -ArgumentList "dashboard/app.py" -WorkingDirectory $projectDir -PassThru
Start-Sleep -Seconds 3
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8080" -UseBasicParsing -TimeoutSec 3
    Write-Host "`nDashboard web head (first 5 lines):"
    $response.Content -split "`n" | Select-Object -First 5
} catch {
    Write-Host "❌ Error checking dashboard endpoint: $($_.Exception.Message)"
}
Stop-Process -Id $dashboard.Id -Force

# 3. Tail RELEASES.md
Write-Host "`nLast 10 lines of RELEASES.md:"
if (Test-Path $releasesFile) {
    Get-Content $releasesFile | Select-Object -Last 10
} else {
    Write-Host "❌ RELEASES.md not found."
}


# Open Maestro-AI dashboard in Brave browser
$bravePath = "$Env:ProgramFiles\BraveSoftware\Brave-Browser\Application\brave.exe"
if (-Not (Test-Path $bravePath)) {
    $bravePath = "$Env:ProgramFiles(x86)\BraveSoftware\Brave-Browser\Application\brave.exe"
}
if (Test-Path $bravePath) {
    Start-Process -FilePath $bravePath -ArgumentList 'http://127.0.0.1:8080'
    Write-Host "Opened Maestro-AI dashboard in Brave browser."
} else {
    Write-Host "Brave browser not found. Please open http://127.0.0.1:8080 manually."
}

Write-Host "`nReady to begin. Which mission from the backlog are you starting?"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"