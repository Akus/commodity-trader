<#
.SYNOPSIS
  Register this repo's Azure DevOps pipelines (CI + PR validation).

.DESCRIPTION
  Idempotent one-time setup. Creates two pipeline definitions pointing at the
  YAML in this repo:
    - commodity-trader-ci         -> azure-pipelines/ci.yml
    - commodity-trader-pr         -> azure-pipelines/pr-validation.yml

  It does NOT recreate the shared bits (variable group `commodity-cicd`, the
  ARM service connection, the commodity-dev/preprod/prod Environments) — those
  are shared with the infra repo and are assumed to already exist. See the
  "Still manual" notes printed at the end for the few UI-only steps.

.PREREQUISITES
  - az CLI logged in (az login), or an ADO PAT exported as AZURE_DEVOPS_EXT_PAT.
  - A GitHub service connection already created in the ADO project so ADO can
    read Akus/commodity-trader (pass its name via -GitHubServiceConnection).

.EXAMPLE
  $env:AZURE_DEVOPS_EXT_PAT = "<pat>"
  ./azure-pipelines/setup-ado.ps1 `
    -OrgUrl https://dev.azure.com/myorg -Project commodity `
    -GitHubServiceConnection "Akus-GitHub"
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)] [string]$OrgUrl,                  # https://dev.azure.com/<org>
  [Parameter(Mandatory)] [string]$Project,
  [Parameter(Mandatory)] [string]$GitHubServiceConnection, # name of the existing GitHub service connection in ADO
  [string]$Repository = "Akus/commodity-trader",
  [string]$Branch     = "main"
)

$ErrorActionPreference = "Stop"

function New-Pipeline {
  param([string]$Name, [string]$YamlPath, [string]$ScId)
  # Use `list` (returns empty when absent) — `show` errors on a missing pipeline,
  # which would abort under $ErrorActionPreference = "Stop".
  $existing = az pipelines list --org $OrgUrl --project $Project --query "[?name=='$Name'].id | [0]" -o tsv
  if ($existing) {
    Write-Host "= pipeline '$Name' already exists (id $existing) - skipping" -ForegroundColor Yellow
    return
  }
  Write-Host "+ creating pipeline '$Name' -> $YamlPath" -ForegroundColor Green
  az pipelines create `
    --name $Name `
    --org $OrgUrl --project $Project `
    --repository $Repository --repository-type github --branch $Branch `
    --yaml-path $YamlPath `
    --service-connection $ScId `
    --skip-first-run true | Out-Null
}

# 1. Ensure the azure-devops CLI extension is present. Use `list` (empty when
# absent) — `show` errors on a missing extension, aborting under Stop.
$hasExt = az extension list --query "[?name=='azure-devops'] | length(@)" -o tsv
if ($hasExt -ne "1") {
  Write-Host "+ installing azure-devops extension" -ForegroundColor Green
  az extension add --name azure-devops --only-show-errors
}

# 2. Set org/project defaults for this session.
az devops configure --defaults organization=$OrgUrl project=$Project | Out-Null

# 3. Resolve the GitHub service connection name -> id.
$scId = az devops service-endpoint list --org $OrgUrl --project $Project `
  --query "[?name=='$GitHubServiceConnection'].id | [0]" -o tsv
if (-not $scId) {
  throw "GitHub service connection '$GitHubServiceConnection' not found in $OrgUrl/$Project. Create it first (Project Settings -> Service connections -> GitHub)."
}
Write-Host "= using GitHub service connection '$GitHubServiceConnection' (id $scId)"

# 4. Create the two pipelines.
New-Pipeline -Name "commodity-trader-ci" -YamlPath "azure-pipelines/ci.yml"           -ScId $scId
New-Pipeline -Name "commodity-trader-pr" -YamlPath "azure-pipelines/pr-validation.yml" -ScId $scId

Write-Host ""
Write-Host "Done. Still manual in the ADO UI:" -ForegroundColor Cyan
Write-Host "  1. Add 'commodity-trader-pr' as a branch policy / build validation on main."
Write-Host "  2. Add Approval checks on the commodity-preprod and commodity-prod Environments."
Write-Host "  3. Confirm the 'commodity-cicd' variable group (azureServiceConnection + FLUX_PAT)"
Write-Host "     and the commodity-dev/preprod/prod Environments exist (shared with the infra repo)."
