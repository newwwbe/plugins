# Install the newwwbe Claude Code plugin set on this machine (Windows PowerShell).
#
#   irm https://raw.githubusercontent.com/newwwbe/plugins/main/install.ps1 | iex
#
# With options, download first:
#   & ([scriptblock]::Create((irm https://raw.githubusercontent.com/newwwbe/plugins/main/install.ps1))) -Add "github notion" -With "ruflo headroom"
param(
  [string]$Add = "",
  [string]$Plugins = "attention-span anti-slop thermos pstack cursor-team-kit dyl-stack advisor ralph-loop orchestrate create-plugin agent-compatibility cli-for-agent teaching docs-canvas pr-review-canvas ponytail arena-skill markitdown",
  [string]$With = "",
  [switch]$NoTools,
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

$failed = @()
function Install-Plugin([string]$Id) {
  claude plugin install $Id *> $null
  if ($LASTEXITCODE -eq 0) { Write-Host "    ok  $Id" } else { Write-Host "    !!  $Id (install failed)"; $script:failed += $Id }
}

# uv runs the MarkItDown MCP server (uvx) and installs the Python CLIs below.
function Ensure-Uv {
  if (Get-Command uv -ErrorAction SilentlyContinue) { return $true }
  Write-Host "==> Installing uv"
  try { powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex" *> $null } catch {}
  $env:Path = "$HOME\.local\bin;$env:Path"
  return [bool](Get-Command uv -ErrorAction SilentlyContinue)
}
function Uv-Bin { $d = (uv tool dir --bin 2>$null); if ($d) { $d } else { "$HOME\.local\bin" } }

Write-Host "==> Marketplace: $MarketplaceRepo"
claude plugin marketplace add $MarketplaceRepo | Out-Null
claude plugin marketplace update $MarketplaceName | Out-Null

foreach ($plugin in (($Plugins + " " + $Add) -split "\s+" | Where-Object { $_ })) {
  Install-Plugin "$plugin@$MarketplaceName"
}

if (-not $NoTools) {
  if (Ensure-Uv) {
    Write-Host "==> Graphify (codebase knowledge graph, /graphify)"
    uv tool install --upgrade graphifyy *> $null
    if ($LASTEXITCODE -eq 0) { & (Join-Path (Uv-Bin) "graphify.exe") install --platform windows *> $null }
    if ($LASTEXITCODE -eq 0) { Write-Host "    ok  graphify" } else { Write-Host "    !!  graphify (run: uv tool install graphifyy; graphify install)"; $failed += "graphify" }
  } else {
    Write-Host "    !!  uv (install it from https://docs.astral.sh/uv/; markitdown and graphify need it)"; $failed += "uv"
  }
}

foreach ($extra in ($With -split "\s+" | Where-Object { $_ })) {
  switch ($extra) {
    "ruflo" {
      Write-Host "==> Ruflo (marketplace ruvnet/ruflo)"
      claude plugin marketplace add ruvnet/ruflo *> $null
      claude plugin marketplace update ruflo *> $null
      Install-Plugin "ruflo-core@ruflo"
      Install-Plugin "ruflo-swarm@ruflo"
    }
    "headroom" {
      Write-Host "==> Headroom (marketplace headroomlabs-ai/headroom)"
      if (Ensure-Uv) { uv tool install --upgrade --python 3.13 "headroom-ai[all]" *> $null }
      if ($LASTEXITCODE -eq 0) { & (Join-Path (Uv-Bin) "headroom.exe") init -g claude *> $null }
      if ($LASTEXITCODE -eq 0) { Write-Host "    ok  headroom CLI (undo: headroom unwrap claude)" } else { Write-Host "    !!  headroom CLI (see https://github.com/headroomlabs-ai/headroom)"; $failed += "headroom-cli" }
      claude plugin marketplace add headroomlabs-ai/headroom *> $null
      claude plugin marketplace update headroom-marketplace *> $null
      Install-Plugin "headroom@headroom-marketplace"
    }
    default { Write-Host "    !!  unknown extra: $extra (choose from: ruflo headroom)"; $failed += $extra }
  }
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
