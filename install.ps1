# Install the newwwbe Claude Code plugin set on this machine (Windows PowerShell).
#
#   irm https://raw.githubusercontent.com/newwwbe/plugins/main/install.ps1 | iex
#
# With options, download first:
#   & ([scriptblock]::Create((irm https://raw.githubusercontent.com/newwwbe/plugins/main/install.ps1))) -Add "github notion"
param(
  [string]$Add = "",
  [string]$Plugins = "attention-span anti-slop thermos pstack cursor-team-kit dyl-stack advisor ralph-loop orchestrate create-plugin agent-compatibility cli-for-agent teaching docs-canvas pr-review-canvas",
  [string]$Style = "attention-span:Attention-kind",
  [switch]$NoStyle
)
$ErrorActionPreference = "Stop"

$MarketplaceRepo = if ($env:NEWWWBE_MARKETPLACE_REPO) { $env:NEWWWBE_MARKETPLACE_REPO } else { "newwwbe/plugins" }
$MarketplaceName = "newwwbe"

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Write-Error "Claude Code is not installed. Install it first:  irm https://claude.ai/install.ps1 | iex"
  exit 1
}

Write-Host "==> Marketplace: $MarketplaceRepo"
claude plugin marketplace add $MarketplaceRepo | Out-Null
claude plugin marketplace update $MarketplaceName | Out-Null

$failed = @()
foreach ($plugin in (($Plugins + " " + $Add) -split "\s+" | Where-Object { $_ })) {
  claude plugin install "$plugin@$MarketplaceName" *> $null
  if ($LASTEXITCODE -eq 0) { Write-Host "    ok  $plugin" } else { Write-Host "    !!  $plugin (install failed)"; $failed += $plugin }
}

if (-not $NoStyle -and $Style) {
  $configDir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $HOME ".claude" }
  $settings = Join-Path $configDir "settings.json"
  New-Item -ItemType Directory -Force -Path $configDir | Out-Null
  $data = if ((Test-Path $settings) -and (Get-Item $settings).Length -gt 0) { Get-Content $settings -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
  $data | Add-Member -NotePropertyName outputStyle -NotePropertyValue $Style -Force
  # Write UTF-8 without a BOM; Windows PowerShell 5.1's "utf8" adds one, which breaks JSON parsing.
  [System.IO.File]::WriteAllText($settings, ($data | ConvertTo-Json -Depth 32), (New-Object System.Text.UTF8Encoding $false))
  Write-Host "==> Output style: $Style"
}

Write-Host "==> Done. Start a new Claude Code session to use the plugins."
if ($failed.Count -gt 0) { Write-Error ("Failed: " + ($failed -join " ")); exit 1 }
