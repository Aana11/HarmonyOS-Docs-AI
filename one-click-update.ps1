[CmdletBinding()]
param(
    [ValidateSet('FAQ', 'All')]
    [string]$Mode = 'FAQ',
    [switch]$ForceRefresh,
    [int]$Limit = 0,
    [switch]$SkipRebuild
)

$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding

$PackageRoot = $PSScriptRoot
$ScraperRoot = Join-Path $PackageRoot 'scraper'
$SyncModule = Join-Path $ScraperRoot 'scripts\sync.py'
$RebuildScript = Join-Path $PackageRoot 'tools\rebuild_indexes.py'

if (-not (Test-Path -LiteralPath $SyncModule)) {
    throw 'Scraper not found. Extract HarmonyOS-Docs-AI.zip completely, then run this script again.'
}

$Uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $Uv) {
    throw 'uv was not found. Install uv from https://docs.astral.sh/uv/ and run this script again.'
}

$Started = Get-Date
$SyncArgs = @('run', 'python', '-m', 'scripts.sync')
if ($Mode -eq 'FAQ') {
    $SyncArgs += @('--root', 'harmonyos-faqs')
}
if ($ForceRefresh) {
    $SyncArgs += '--force'
}
if ($Limit -gt 0) {
    $SyncArgs += @('--limit', $Limit.ToString())
}

Write-Host ''
Write-Host "HarmonyOS docs one-click update: $Mode" -ForegroundColor Cyan
Write-Host 'Source: Huawei Developer documentPortal API'
Write-Host "Package: $PackageRoot"
Write-Host ''

Push-Location $ScraperRoot
try {
    Write-Host '[1/3] Preparing the isolated environment...' -ForegroundColor Yellow
    & $Uv.Source sync
    if ($LASTEXITCODE -ne 0) {
        throw "uv sync failed with exit code $LASTEXITCODE"
    }

    Write-Host '[2/3] Discovering and incrementally fetching documents...' -ForegroundColor Yellow
    & $Uv.Source @SyncArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Document sync failed with exit code $LASTEXITCODE. See scraper\data\logs."
    }
}
finally {
    Pop-Location
}

if (-not $SkipRebuild) {
    Write-Host '[3/3] Rebuilding AI JSONL files and manifest...' -ForegroundColor Yellow
    & $Uv.Source run python $RebuildScript $PackageRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Index rebuild failed with exit code $LASTEXITCODE"
    }
}
else {
    Write-Host '[3/3] Index rebuild skipped (test mode).' -ForegroundColor DarkYellow
}

$Elapsed = (Get-Date) - $Started
Write-Host ''
Write-Host ("Update completed in {0:mm\:ss}." -f $Elapsed) -ForegroundColor Green
Write-Host 'AI-ready outputs: harmonyos\references, catalog.jsonl, and faq-corpus.jsonl.'
