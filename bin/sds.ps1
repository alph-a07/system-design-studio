<#
.SYNOPSIS
System Design Studio CLI for Windows PowerShell (sds.ps1)
Universal PowerShell interface for System Design Studio.
#>
param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$RemainingArgs
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$GlobalDir = if ($env:SDS_GLOBAL_DIR) { $env:SDS_GLOBAL_DIR } else { Join-Path $HOME ".system-design-studio" }

if (Test-Path (Join-Path $ScriptDir "..\skills\system-design-studio\scripts")) {
    $BaseScripts = (Resolve-Path (Join-Path $ScriptDir "..\skills\system-design-studio\scripts")).Path
} else {
    $BaseScripts = Join-Path $GlobalDir "skills\system-design-studio\scripts"
}

# Resolve Python 3 executable
$PyCmd = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } elseif (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { $null }

if (-not $PyCmd) {
    Write-Error "Python 3 is required to run System Design Studio. Please install Python 3 from https://python.org"
    exit 1
}

switch ($Command.ToLower()) {
    "init" {
        $initScript = Join-Path $BaseScripts "init-learning-instance.sh"
        if (Get-Command bash -ErrorAction SilentlyContinue) {
            & bash $initScript @RemainingArgs
        } else {
            & $PyCmd (Join-Path $BaseScripts "manage-projects.py") init @RemainingArgs
        }
    }
    { $_ -in "dashboard", "serve", "tracker" } {
        & $PyCmd (Join-Path $BaseScripts "serve-dashboard.py") @RemainingArgs
    }
    { $_ -in "dummy", "demo" } {
        $dummyDir = Join-Path $PWD "dummy-project\.system-design"
        if (-not (Test-Path $dummyDir)) {
            $dummyDir = Join-Path $ScriptDir "..\dummy-project\.system-design"
        }
        if (-not (Test-Path $dummyDir)) {
            Write-Error "dummy-project\.system-design not found."
            exit 1
        }
        Write-Host "Launching System Design Studio Dashboard for Dummy Project..."
        & $PyCmd (Join-Path $BaseScripts "serve-dashboard.py") --instance-dir $dummyDir @RemainingArgs
    }
    { $_ -in "revisions", "revision", "rev" } {
        & $PyCmd (Join-Path $BaseScripts "update-revisions.py") @RemainingArgs
    }
    { $_ -in "projects", "list" } {
        & $PyCmd (Join-Path $BaseScripts "manage-projects.py") list @RemainingArgs
    }
    { $_ -in "switch", "open" } {
        & $PyCmd (Join-Path $BaseScripts "manage-projects.py") switch @RemainingArgs
    }
    "notes" {
        & $PyCmd (Join-Path $BaseScripts "manage-projects.py") notes @RemainingArgs
    }
    { $_ -in "delete", "remove", "rm" } {
        & $PyCmd (Join-Path $BaseScripts "manage-projects.py") delete @RemainingArgs
    }
    { $_ -in "rollback", "restore", "undo" } {
        & $PyCmd (Join-Path $BaseScripts "git-checkpoint.py") rollback @RemainingArgs
    }
    "checkpoints" {
        & $PyCmd (Join-Path $BaseScripts "git-checkpoint.py") list @RemainingArgs
    }
    "curriculum" {
        & $PyCmd (Join-Path $BaseScripts "configure-curriculum.py") @RemainingArgs
    }
    "config" {
        & $PyCmd (Join-Path $BaseScripts "merge-settings.py") @RemainingArgs
    }
    "status" {
        & $PyCmd (Join-Path $BaseScripts "sync-status.py") @RemainingArgs
    }
    { $_ -in "update", "upgrade" } {
        $updatePs1 = Join-Path $GlobalDir "update.ps1"
        if (Test-Path $updatePs1) {
            & $updatePs1 @RemainingArgs
        } else {
            Invoke-Expression (Invoke-RestMethod "https://raw.githubusercontent.com/alph-a07/system-design-studio/main/update.ps1")
        }
    }
    { $_ -in "version", "-v", "--version" } {
        Write-Host "System Design Studio CLI v4.2.1"
    }
    default {
        Write-Host "============================================================================"
        Write-Host "  SYSTEM DESIGN STUDIO CLI (sds) - v4.2.1"
        Write-Host "============================================================================"
        Write-Host "Usage: sds <command> [options]"
        Write-Host ""
        Write-Host "Core Commands:"
        Write-Host "  sds init [options]         Initialize or scaffold a project learning instance"
        Write-Host "  sds dashboard [options]    Launch interactive curriculum studio & workbench on localhost"
        Write-Host "  sds dummy [options]        Launch dashboard for local dummy test project"
        Write-Host "  sds revisions [options]    Review high-yield invariants & trade-off defenses"
        Write-Host "  sds list / projects        List registered projects, tracks, and progress"
        Write-Host "  sds switch <id>            Switch active project context"
        Write-Host "  sds notes [id]             List generated study notes for active project"
        Write-Host "  sds delete <id>            Safely delete a project instance"
        Write-Host ""
        Write-Host "State & Safety:"
        Write-Host "  sds rollback [--steps N]   Roll back state to a previous atomic checkpoint"
        Write-Host "  sds checkpoints            List recent state snapshots and Git commits"
        Write-Host "  sds curriculum [options]   Configure, prune, or reorder curriculum tracks"
        Write-Host "  sds config [key] [val]     Inspect or dynamically update settings"
        Write-Host "  sds status                 Display current living cursor and topic metrics"
        Write-Host "  sds update                 Update studio skills to the latest release"
        Write-Host "  sds version                Print version information"
        Write-Host "============================================================================"
    }
}
