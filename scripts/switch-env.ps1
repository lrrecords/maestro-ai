param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('local-ollama', 'railway')]
    [string]$Profile
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$targetEnv = Join-Path $repoRoot '.env'
$sourceEnv = switch ($Profile) {
    'local-ollama' { Join-Path $repoRoot '.env.local-ollama' }
    'railway' { Join-Path $repoRoot '.env.railway' }
}

if (-not (Test-Path $sourceEnv)) {
    Write-Error "Profile file not found: $sourceEnv"
    exit 1
}

if (Test-Path $targetEnv) {
    $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backupEnv = Join-Path $repoRoot ".env.backup.$timestamp"
    Copy-Item -Path $targetEnv -Destination $backupEnv -Force
    Write-Host "Backed up existing .env to $backupEnv"
}

Copy-Item -Path $sourceEnv -Destination $targetEnv -Force
Write-Host "Activated profile '$Profile' by copying $(Split-Path $sourceEnv -Leaf) -> .env"
Write-Host "Next step: restart your Flask process so new environment variables are loaded."
