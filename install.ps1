# System Design Studio — Universal Windows PowerShell Installer (v4.1.1)
# Configures global studio preferences ($HOME\.system-design-studio\config.json)
# and installs skill packages across AI coding agents on Windows.
#
# Usage:
#   irm https://raw.githubusercontent.com/alph-a07/system-design-studio/main/install.ps1 | iex
#   .\install.ps1 [-Theme <theme>] [-Output <html|markdown>] [-Notes <bool>] [-Defaults]

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateSet('slate-clean', 'editorial-paper', 'midnight-neon', 'nordic-frost', 'warm-amber')]
    [string]$Theme = 'slate-clean',

    [Parameter()]
    [ValidateSet('html')]
    [string]$Output = 'html',

    [Parameter()]
    [bool]$Notes = $true,

    [Parameter()]
    [ValidateSet('per-topic', 'per-cluster', 'per-tier', 'single-file')]
    [string]$NotesStructure = 'per-topic',

    [Parameter()]
    [switch]$All,

    [Parameter()]
    [switch]$Antigravity,

    [Parameter()]
    [switch]$Claude,

    [Parameter()]
    [switch]$Cursor,

    [Parameter()]
    [switch]$Codex,

    [Parameter()]
    [Alias('y')]
    [switch]$Defaults,

    [Parameter()]
    [Alias('h')]
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Host @"
==========================================================
  System Design Studio — Windows PowerShell Installer
==========================================================
Usage: .\install.ps1 [OPTIONS]

Parameters:
  -Theme <name>          slate-clean, editorial-paper, midnight-neon, nordic-frost, warm-amber
  -Output <type>         html | markdown
  -Notes <bool>          `$true | `$false
  -NotesStructure <str>  per-topic | per-cluster | per-tier | single-file
  -All                   Install across all detected and potential agent locations
  -Defaults, -y          Install using default preferences without prompting
"@
    exit 0
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  System Design Studio — Universal Agent Skill Installer  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$HomeDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
$GlobalStudioDir = Join-Path $HomeDir ".system-design-studio"
$GlobalBin = Join-Path $GlobalStudioDir "bin"
$GlobalConfig = Join-Path $GlobalStudioDir "config.json"
$GlobalProjects = Join-Path $GlobalStudioDir "projects.json"

# Check prior global config if present
if (Test-Path $GlobalConfig) {
    try {
        $prior = Get-Content -Raw $GlobalConfig | ConvertFrom-Json
        if ($prior.artifactStyle) { $Theme = $prior.artifactStyle }
        if ($prior.outputType) { $Output = $prior.outputType }
        if ($prior.notesStructure) { $NotesStructure = $prior.notesStructure }
        if ($null -ne $prior.autoGenerateNotes) { $Notes = [bool]$prior.autoGenerateNotes }
    } catch {
        # Ignore json parse error
    }
}

# Source resolution
$SourceSkillsDir = $null
$SourceAgentsDir = $null
$SourceBinDir = $null
$TempDir = $null

$ScriptRootPath = $PSScriptRoot
if (-not [string]::IsNullOrEmpty($ScriptRootPath) -and (Test-Path (Join-Path $ScriptRootPath "plugin.json"))) {
    $SourceSkillsDir = Join-Path $ScriptRootPath "skills"
    $SourceAgentsDir = Join-Path $ScriptRootPath "agents"
    $SourceBinDir = Join-Path $ScriptRootPath "bin"
} else {
    Write-Host "Fetching latest release archive from GitHub..." -ForegroundColor Yellow
    $TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("sds-install-" + [System.Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
    
    $ZipUrl = "https://github.com/alph-a07/system-design-studio/archive/refs/heads/main.zip"
    $ZipFile = Join-Path $TempDir "sds.zip"
    
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipFile -UseBasicParsing
    
    Expand-Archive -Path $ZipFile -DestinationPath $TempDir -Force
    $ExtractedRoot = Join-Path $TempDir "system-design-studio-main"
    $SourceSkillsDir = Join-Path $ExtractedRoot "skills"
    $SourceAgentsDir = Join-Path $ExtractedRoot "agents"
    $SourceBinDir = Join-Path $ExtractedRoot "bin"
}

try {
    # 1. Save Global Preferences
    New-Item -ItemType Directory -Path $GlobalStudioDir -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $GlobalStudioDir "projects") -Force | Out-Null
    New-Item -ItemType Directory -Path $GlobalBin -Force | Out-Null

    $configObj = @{
        "`$schemaVersion" = "3.2"
        "artifactStyle" = $Theme
        "outputType" = $Output
        "autoGenerateNotes" = $Notes
        "notesStructure" = $NotesStructure
        "defaultTrack" = "full-mastery"
    }
    $configObj | ConvertTo-Json -Depth 4 | Set-Content -Path $GlobalConfig -Encoding UTF8

    if (-not (Test-Path $GlobalProjects)) {
        @{
            "`$schemaVersion" = "3.2"
            "activeProjectId" = $null
            "projects" = @()
        } | ConvertTo-Json -Depth 4 | Set-Content -Path $GlobalProjects -Encoding UTF8
    }

    Write-Host "💾 Global preferences saved to $GlobalConfig" -ForegroundColor Green

    # 2. Resolve Agent Locations
    $AgentSkillTargets = [System.Collections.Generic.List[string]]::new()
    $AgentAgentTargets = [System.Collections.Generic.List[string]]::new()

    # Always install to global studio skills
    $AgentSkillTargets.Add((Join-Path $GlobalStudioDir "skills"))
    $AgentAgentTargets.Add((Join-Path $GlobalStudioDir "agents"))

    # Antigravity / Gemini
    $AgentSkillTargets.Add((Join-Path $HomeDir ".gemini\antigravity\skills"))
    $AgentSkillTargets.Add((Join-Path $HomeDir ".gemini\config\skills"))
    $AgentSkillTargets.Add((Join-Path $HomeDir ".agents\skills"))
    $AgentAgentTargets.Add((Join-Path $HomeDir ".gemini\antigravity\agents"))
    $AgentAgentTargets.Add((Join-Path $HomeDir ".gemini\config\agents"))
    $AgentAgentTargets.Add((Join-Path $HomeDir ".agents\agents"))

    # Claude Code
    $AgentSkillTargets.Add((Join-Path $HomeDir ".claude\skills"))
    $AgentAgentTargets.Add((Join-Path $HomeDir ".claude\agents"))
    if ($env:APPDATA) {
        $AgentSkillTargets.Add((Join-Path $env:APPDATA "Claude\skills"))
    }

    # Cursor
    $AgentSkillTargets.Add((Join-Path $HomeDir ".cursor\skills"))
    $AgentAgentTargets.Add((Join-Path $HomeDir ".cursor\agents"))
    if ($env:APPDATA) {
        $AgentSkillTargets.Add((Join-Path $env:APPDATA "Cursor\User\skills"))
        $AgentAgentTargets.Add((Join-Path $env:APPDATA "Cursor\User\agents"))
    }

    # Codex
    $AgentSkillTargets.Add((Join-Path $HomeDir ".codex\skills"))
    $AgentAgentTargets.Add((Join-Path $HomeDir ".codex\agents"))

    # 3. Copy Skills and In-Chat Commands
    Write-Host "📦 Installing skills and companion commands..." -ForegroundColor Cyan
    $InstalledCount = 0

    $SourceMainSkill = Join-Path $SourceSkillsDir "system-design-studio"
    $CompanionSkills = Get-ChildItem -Path $SourceSkillsDir -Directory -Filter "sds-*"

    foreach ($targetParent in $AgentSkillTargets) {
        try {
            New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
            $dest = Join-Path $targetParent "system-design-studio"
            if (Test-Path $dest) { Remove-Item -Path $dest -Recurse -Force | Out-Null }
            Copy-Item -Path $SourceMainSkill -Destination $dest -Recurse -Force

            foreach ($comp in $CompanionSkills) {
                $compDest = Join-Path $targetParent $comp.Name
                if (Test-Path $compDest) { Remove-Item -Path $compDest -Recurse -Force | Out-Null }
                Copy-Item -Path $comp.FullName -Destination $compDest -Recurse -Force
            }

            Write-Host "   ✅ Installed at $dest (+ $($CompanionSkills.Count) commands)" -ForegroundColor Green
            $InstalledCount++
        } catch {
            Write-Verbose "Skipped target $targetParent`: $_"
        }
    }

    # 4. Copy Subagents
    if (Test-Path $SourceAgentsDir) {
        Write-Host "🤖 Installing specialized subagents..." -ForegroundColor Cyan
        $Subagents = Get-ChildItem -Path $SourceAgentsDir
        foreach ($targetAgentParent in $AgentAgentTargets) {
            try {
                New-Item -ItemType Directory -Path $targetAgentParent -Force | Out-Null
                foreach ($sa in $Subagents) {
                    $saDest = Join-Path $targetAgentParent $sa.Name
                    if (Test-Path $saDest) { Remove-Item -Path $saDest -Recurse -Force | Out-Null }
                    Copy-Item -Path $sa.FullName -Destination $saDest -Recurse -Force
                }
                Write-Host "   ✅ Installed subagents at $targetAgentParent" -ForegroundColor Green
            } catch {
                Write-Verbose "Skipped agent target $targetAgentParent`: $_"
            }
        }
    }

    # 5. Install CLI Binaries & Wrappers
    Write-Host "⚡ Installing CLI wrappers into $GlobalBin..." -ForegroundColor Cyan
    if (Test-Path $SourceBinDir) {
        Copy-Item -Path (Join-Path $SourceBinDir "*") -Destination $GlobalBin -Recurse -Force
    }

    # Also copy updater scripts to GlobalStudioDir
    $RootFolder = Split-Path $SourceSkillsDir -Parent
    $UpdatePs1 = Join-Path $RootFolder "update.ps1"
    $UpdateSh = Join-Path $RootFolder "update.sh"
    if (Test-Path $UpdatePs1) { Copy-Item -Path $UpdatePs1 -Destination (Join-Path $GlobalStudioDir "update.ps1") -Force }
    if (Test-Path $UpdateSh) { Copy-Item -Path $UpdateSh -Destination (Join-Path $GlobalStudioDir "update.sh") -Force }

    # 6. Auto-Add to User PATH Environment Variable
    Write-Host "🔍 Configuring Windows Environment PATH for 'sds'..." -ForegroundColor Cyan
    $UserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $BinPath = $GlobalBin
    $Paths = ($UserPath -split ';') | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

    if ($Paths -notcontains $BinPath) {
        $NewUserPath = if ([string]::IsNullOrEmpty($UserPath)) { $BinPath } else { "$UserPath;$BinPath" }
        [Environment]::SetEnvironmentVariable('Path', $NewUserPath, 'User')
        $env:Path = "$BinPath;$env:Path"
        Write-Host "   ✅ Added '$BinPath' to Windows User Environment PATH registry" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️  '$BinPath' is already present in User PATH." -ForegroundColor Gray
    }

    # 7. Success Banner
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "🎉 System Design Studio skill installed across $InstalledCount agent location(s)!" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚙️  Global Defaults Configured:" -ForegroundColor Cyan
    Write-Host "   • Visual Theme:     $Theme"
    Write-Host "   • Output Format:    $Output"
    Write-Host "   • Auto-Notes:       $Notes ($NotesStructure)"
    Write-Host "   • Machine Root:     $GlobalStudioDir"
    Write-Host "   • CLI Command:      sds"
    Write-Host ""
    Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
    Write-Host "   Open a PowerShell or Terminal window and run:"
    Write-Host "     sds init" -ForegroundColor Yellow
    Write-Host "     sds dashboard" -ForegroundColor Yellow
    Write-Host "==========================================================" -ForegroundColor Green

} finally {
    if ($null -ne $TempDir -and (Test-Path $TempDir)) {
        Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
