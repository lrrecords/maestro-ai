# PowerShell script to set Railway environment variables
# Usage: .\set_railway_env_vars.ps1 -ProjectId <project_id> -MaestroToken <maestro_token> [-SecretKey <secret_key>] [-PremiumFeaturesEnabled <true|false>]

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    [Parameter(Mandatory=$true)]
    [string]$MaestroToken,
    [string]$SecretKey,
    [string]$PremiumFeaturesEnabled
)

function Set-RailwayVar {
    param(
        [string]$Name,
        [string]$Value
    )
    Write-Host "Setting $Name..."
    railway variables set "$Name=$Value" --project $ProjectId --environment production
}

Set-RailwayVar -Name "MAESTRO_TOKEN" -Value $MaestroToken
if ($SecretKey) {
    Set-RailwayVar -Name "SECRET_KEY" -Value $SecretKey
}
Set-RailwayVar -Name "PREMIUM_FEATURES_ENABLED" -Value $PremiumFeaturesEnabled

Write-Host "All variables set. Trigger a redeploy from the Railway dashboard if needed."
