# System Design Studio — Universal Windows PowerShell Updater (v4.0.0)
# Updates agent skills and CLI to latest release while strictly preserving:
# 1. User learning progress (manifest.json, CURSOR.md, CURRICULUM.md, DECISIONS.md)
# 2. Existing interactive lesson artifacts (lessons/*.html, lessons/*.md)
# 3. User custom settings & chosen visual preferences
# 4. Windows Environment PATH for 'sds' command
#
# Usage:
#   irm https://raw.githubusercontent.com/alph-a07/system-design-studio/main/update.ps1 | iex
#   .\update.ps1 [-InstanceDir <path>]

[CmdletBinding()]
param(
    [Parameter()]
    [string]$InstanceDir = '.system-design'
)

$ErrorActionPreference = 'Stop'

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "    System Design Studio — Universal Update Engine        " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$HomeDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
$GlobalStudioDir = Join-Path $HomeDir ".system-design-studio"
$GlobalBin = Join-Path $GlobalStudioDir "bin"

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
    Write-Host "📥 Fetching latest release archive from GitHub..." -ForegroundColor Yellow
    $TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("sds-update-" + [System.Guid]::NewGuid().ToString("N"))
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
    # 1. Resolve Agent Target Locations
    $AgentSkillTargets = [System.Collections.Generic.List[string]]::new()
    $AgentAgentTargets = [System.Collections.Generic.List[string]]::new()

    $AgentSkillTargets.Add((Join-Path $GlobalStudioDir "skills"))
    $AgentAgentTargets.Add((Join-Path $GlobalStudioDir "agents"))

    $AgentSkillTargets.Add((Join-Path $HomeDir ".gemini\antigravity\skills"))
    $AgentSkillTargets.Add((Join-Path $HomeDir ".gemini\config\skills"))
    $AgentSkillTargets.Add((Join-Path $HomeDir ".agents\skills"))
    $AgentAgentTargets.Add((Join-Path $HomeDir ".gemini\antigravity\agents"))
    $AgentAgentTargets.Add((Join-Path $HomeDir ".gemini\config\agents"))
    $AgentAgentTargets.Add((Join-Path $HomeDir ".agents\agents"))

    $AgentSkillTargets.Add((Join-Path $HomeDir ".claude\skills"))
    $AgentAgentTargets.Add((Join-Path $HomeDir ".claude\agents"))
    if ($env:APPDATA) {
        $AgentSkillTargets.Add((Join-Path $env:APPDATA "Claude\skills"))
    }

    $AgentSkillTargets.Add((Join-Path $HomeDir ".cursor\skills"))
    $AgentAgentTargets.Add((Join-Path $HomeDir ".cursor\agents"))
    if ($env:APPDATA) {
        $AgentSkillTargets.Add((Join-Path $env:APPDATA "Cursor\User\skills"))
        $AgentAgentTargets.Add((Join-Path $env:APPDATA "Cursor\User\agents"))
    }

    $AgentSkillTargets.Add((Join-Path $HomeDir ".codex\skills"))
    $AgentAgentTargets.Add((Join-Path $HomeDir ".codex\agents"))

    # 2. Update Skills
    Write-Host "📦 Updating agent skills..." -ForegroundColor Cyan
    $UpdatedCount = 0

    $SourceMainSkill = Join-Path $SourceSkillsDir "system-design-studio"
    $CompanionSkills = Get-ChildItem -Path $SourceSkillsDir -Directory -Filter "sds-*"

    foreach ($targetParent in $AgentSkillTargets) {
        if (Test-Path $targetParent) {
            try {
                $dest = Join-Path $targetParent "system-design-studio"
                if (Test-Path $dest) { Remove-Item -Path $dest -Recurse -Force | Out-Null }
                Copy-Item -Path $SourceMainSkill -Destination $dest -Recurse -Force

                foreach ($comp in $CompanionSkills) {
                    $compDest = Join-Path $targetParent $comp.Name
                    if (Test-Path $compDest) { Remove-Item -Path $compDest -Recurse -Force | Out-Null }
                    Copy-Item -Path $comp.FullName -Destination $compDest -Recurse -Force
                }

                Write-Host "   ✅ Updated at $dest (+ $($CompanionSkills.Count) in-chat commands)" -ForegroundColor Green
                $UpdatedCount++
            } catch {
                Write-Verbose "Skipped target $targetParent`: $_"
            }
        }
    }

    # 3. Update Subagents
    if (Test-Path $SourceAgentsDir) {
        Write-Host "🤖 Updating specialized subagents..." -ForegroundColor Cyan
        $Subagents = Get-ChildItem -Path $SourceAgentsDir
        foreach ($targetAgentParent in $AgentAgentTargets) {
            if (Test-Path $targetAgentParent) {
                try {
                    foreach ($sa in $Subagents) {
                        $saDest = Join-Path $targetAgentParent $sa.Name
                        if (Test-Path $saDest) { Remove-Item -Path $saDest -Recurse -Force | Out-Null }
                        Copy-Item -Path $sa.FullName -Destination $saDest -Recurse -Force
                    }
                    Write-Host "   ✅ Updated subagents at $targetAgentParent" -ForegroundColor Green
                } catch {
                    Write-Verbose "Skipped agent target $targetAgentParent`: $_"
                }
            }
        }
    }

    # 4. Update CLI Binaries in ~/.system-design-studio/bin
    Write-Host "⚡ Updating CLI binaries in $GlobalBin..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $GlobalBin -Force | Out-Null
    if (Test-Path $SourceBinDir) {
        Copy-Item -Path (Join-Path $SourceBinDir "*") -Destination $GlobalBin -Recurse -Force
    }

    # 5. Verify / Configure User Environment PATH
    Write-Host "🔍 Configuring Windows Environment PATH for 'sds'..." -ForegroundColor Cyan
    $UserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $BinPath = $GlobalBin
    $Paths = ($UserPath -split ';') | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

    if ($Paths -notcontains $BinPath) {
        $NewUserPath = if ([string]::IsNullOrEmpty($UserPath)) { $BinPath } else { "$UserPath;$BinPath" }
        [Environment]::SetEnvironmentVariable('Path', $NewUserPath, 'User')
        $env:Path = "$BinPath;$env:Path"
        Write-Host "   ✅ Added '$BinPath' to Windows User Environment PATH registry" -ForegroundColor Green
    }

    # 6. Settings Merge & Local Instance Protection
    if (Test-Path $InstanceDir) {
        Write-Host ""
        Write-Host "🔧 Local project instance found at '$InstanceDir':" -ForegroundColor Cyan
        $SettingsFile = Join-Path $InstanceDir "settings.json"
        $TemplateSettings = Join-Path $SourceMainSkill "resources\settings-template.json"
        $MergeScript = Join-Path $SourceMainSkill "scripts\merge-settings.py"

        if ((Test-Path $SettingsFile) -and (Test-Path $TemplateSettings) -and (Test-Path $MergeScript)) {
            Write-Host "   🔄 Merging settings.json to preserve user preferences..." -ForegroundColor Cyan
            try {
                python $MergeScript --current $SettingsFile --template $TemplateSettings --output $SettingsFile
            } catch {
                Write-Verbose "Merge script skipped: $_"
            }
        }
    }

    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "🎉 System Design Studio updated across $UpdatedCount agent location(s)!" -ForegroundColor Green
    Write-Host "   All learning progress and custom user settings were preserved." -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green

} finally {
    if ($null -ne $TempDir -and (Test-Path $TempDir)) {
        Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
