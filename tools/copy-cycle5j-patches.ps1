<#
.SYNOPSIS
  Copy Cycle 5i/5j patch bundles (subfolders) into mcwiki tools/ and docs/

.DESCRIPTION
  Source folder structure (user staged in MCProject):
    E:\MCProject\KMCProject\outputs\cycle_patches\
      cycle_5i_patches\
        *.py
        README.md (optional)
      cycle_5j_patches\
        *.py
        README.md (optional)
        ...

  Copies:
    Each subfolder's *.py    -> E:\MCWiki\tools\
    Each subfolder's README  -> E:\MCWiki\docs\<subfolder>_README.md

  Backup of current find_cross_link_broken.py + manifest.json + mcp_server.py
  goes to E:\MCWiki\backup\pre-v0.4.0\

.PARAMETER DryRun
  Validation only, no file copy.

.PARAMETER SourceBase
  Override source folder
  (default: E:\MCProject\KMCProject\outputs\cycle_patches).

.PARAMETER OverwritePy
  Overwrite existing .py files in tools/ (default: true).
  Set to $false to skip files that already exist.

.EXAMPLE
  .\copy-cycle5j-patches.ps1 -DryRun
  .\copy-cycle5j-patches.ps1
  .\copy-cycle5j-patches.ps1 -SourceBase "D:\elsewhere\cycle_patches"
#>
[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$SourceBase = "E:\MCProject\KMCProject\outputs\cycle_patches",
    [bool]$OverwritePy = $true
)

$ErrorActionPreference = "Stop"

# Vault paths
$Vault  = "E:\MCWiki"
$Tools  = Join-Path $Vault "tools"
$Docs   = Join-Path $Vault "docs"
$Backup = Join-Path $Vault "backup\pre-v0.4.0"

$ModeTag = if ($DryRun) { "[DRY RUN]" } else { "[APPLY]" }
Write-Host "===== $ModeTag mcwiki v0.4.0 patch copy =====" -ForegroundColor Magenta
Write-Host ""

# ---------------------------------------------------------------------------
# [1/5] Source validation - scan subfolders

Write-Host "[1/5] Source folder + subfolder scan" -ForegroundColor Cyan
Write-Host "  source base = $SourceBase"

if (-not (Test-Path $SourceBase)) {
    throw "Source folder not found: $SourceBase"
}

$subfolders = @(Get-ChildItem $SourceBase -Directory)
if ($subfolders.Count -eq 0) {
    # Fallback: maybe .py are at root
    Write-Host "  ! no subfolders - falling back to root scan" -ForegroundColor Yellow
    $subfolders = @([PSCustomObject]@{ Name = "<root>"; FullName = $SourceBase })
}

Write-Host "  found $($subfolders.Count) subfolder(s):" -ForegroundColor Green

# Build manifest of files to copy
$copyPlan = @()
foreach ($sub in $subfolders) {
    Write-Host "    [$($sub.Name)]"
    $pyFiles = @(Get-ChildItem (Join-Path $sub.FullName "*.py") -ErrorAction SilentlyContinue)
    $readme  = Join-Path $sub.FullName "README.md"
    $hasReadme = Test-Path $readme

    if ($pyFiles.Count -eq 0 -and -not $hasReadme) {
        Write-Host "        (no .py or README - skip)" -ForegroundColor Yellow
        continue
    }

    foreach ($f in $pyFiles) {
        $msg = "        " + $f.Name + " (" + $f.Length + " bytes)"
        Write-Host $msg
        $copyPlan += [PSCustomObject]@{
            Type     = "py"
            Source   = $f.FullName
            Target   = Join-Path $Tools $f.Name
            Size     = $f.Length
        }
    }
    if ($hasReadme) {
        $r = Get-Item $readme
        $renamed = $sub.Name + "_README.md"
        $msg = "        README.md -> " + $renamed + " (" + $r.Length + " bytes)"
        Write-Host $msg
        $copyPlan += [PSCustomObject]@{
            Type     = "readme"
            Source   = $r.FullName
            Target   = Join-Path $Docs $renamed
            Size     = $r.Length
        }
    }
}

if ($copyPlan.Count -eq 0) {
    throw "No files to copy - check $SourceBase structure"
}

$pyCount     = ($copyPlan | Where-Object { $_.Type -eq "py" }).Count
$readmeCount = ($copyPlan | Where-Object { $_.Type -eq "readme" }).Count
Write-Host ""
Write-Host "  total: $pyCount .py + $readmeCount README" -ForegroundColor Green

# ---------------------------------------------------------------------------
# [2/5] Target vault validation

Write-Host ""
Write-Host "[2/5] Target vault validation" -ForegroundColor Cyan

if (-not (Test-Path $Tools)) { throw "tools/ not found: $Tools" }
if (-not (Test-Path $Docs))  { throw "docs/ not found: $Docs" }
Write-Host "  OK $Tools"
Write-Host "  OK $Docs"

$existing_v030 = Join-Path $Tools "find_cross_link_broken.py"
if (Test-Path $existing_v030) {
    $size = (Get-Item $existing_v030).Length
    $msg = "  OK existing v0.3.0 find_cross_link_broken.py (" + $size + " bytes) - will overwrite per OverwritePy=$OverwritePy"
    Write-Host $msg
}

# ---------------------------------------------------------------------------
# [3/5] Backup

Write-Host ""
Write-Host "[3/5] Backup" -ForegroundColor Cyan

if (-not $DryRun) {
    New-Item -ItemType Directory -Path $Backup -Force | Out-Null

    $targets = @(
        (Join-Path $Tools "find_cross_link_broken.py"),
        (Join-Path $Vault "manifest.json"),
        (Join-Path $Tools "mcp_server.py")
    )
    foreach ($t in $targets) {
        if (Test-Path $t) {
            Copy-Item $t $Backup -Force
            $name = Split-Path $t -Leaf
            Write-Host "  OK $Backup\$name"
        }
    }
} else {
    Write-Host "  (DRY RUN - skip backup)"
}

# ---------------------------------------------------------------------------
# [4/5] Copy plan execute - .py

Write-Host ""
Write-Host "[4/5] Copy .py -> tools/" -ForegroundColor Cyan

$skipped = 0
foreach ($item in ($copyPlan | Where-Object { $_.Type -eq "py" })) {
    $exists = Test-Path $item.Target
    if ($exists -and -not $OverwritePy) {
        $msg = "  SKIP " + (Split-Path $item.Target -Leaf) + " (already exists, OverwritePy=false)"
        Write-Host $msg -ForegroundColor Yellow
        $skipped += 1
        continue
    }

    if (-not $DryRun) {
        Copy-Item $item.Source $item.Target -Force
        $size = (Get-Item $item.Target).Length
        $msg = "  OK " + $item.Target + " (" + $size + " bytes)"
        Write-Host $msg
    } else {
        $verb = if ($exists) { "OVERWRITE" } else { "NEW" }
        $msg = "  (DRY RUN) " + $verb + " " + (Split-Path $item.Target -Leaf) + " (" + $item.Size + " bytes)"
        Write-Host $msg
    }
}
if ($skipped -gt 0) {
    Write-Host "  ($skipped skipped)" -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# [5/5] Copy plan execute - README

Write-Host ""
Write-Host "[5/5] Copy README -> docs/" -ForegroundColor Cyan

foreach ($item in ($copyPlan | Where-Object { $_.Type -eq "readme" })) {
    if (-not $DryRun) {
        Copy-Item $item.Source $item.Target -Force
        $size = (Get-Item $item.Target).Length
        $msg = "  OK " + $item.Target + " (" + $size + " bytes)"
        Write-Host $msg
    } else {
        $msg = "  (DRY RUN) " + (Split-Path $item.Target -Leaf) + " (" + $item.Size + " bytes)"
        Write-Host $msg
    }
}

# ---------------------------------------------------------------------------
# Result summary

Write-Host ""
Write-Host "===== $ModeTag DONE =====" -ForegroundColor Magenta

if (-not $DryRun) {
    Write-Host ""
    Write-Host "tools/ status (.py applied):" -ForegroundColor Cyan
    $copyPlan | Where-Object { $_.Type -eq "py" } | ForEach-Object {
        Get-Item $_.Target -ErrorAction SilentlyContinue
    } | Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize

    Write-Host "docs/ status (README applied):" -ForegroundColor Cyan
    $copyPlan | Where-Object { $_.Type -eq "readme" } | ForEach-Object {
        Get-Item $_.Target -ErrorAction SilentlyContinue
    } | Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize

    Write-Host ""
    Write-Host "Next steps (delegate to main):" -ForegroundColor Yellow
    Write-Host "  1. Analyze new .py via Read"
    Write-Host "  2. Register new tools in mcp_server.py"
    Write-Host "  3. Apply v0.3.1 patch (strip_code_blocks) if find_cross_link_broken.py overwritten"
    Write-Host "  4. Bump manifest.json v0.3.0 -> v0.4.0"
    Write-Host "  5. mcpb pack . dist\mcwiki-0.4.0.mcpb"
    Write-Host "  6. Cowork install + Desktop restart"
} else {
    Write-Host ""
    Write-Host "DryRun mode - remove -DryRun to actually copy" -ForegroundColor Yellow
}
