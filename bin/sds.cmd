@echo off
setlocal enabledelayedexpansion

:: System Design Studio CLI for Windows Command Prompt (sds.cmd)
:: Universal Windows Command Line Interface for System Design Studio.

set "SCRIPT_DIR=%~dp0"
set "GLOBAL_DIR=%USERPROFILE%\.system-design-studio"

if exist "%SCRIPT_DIR%..\skills\system-design-studio\scripts" (
  set "BASE_SCRIPTS=%SCRIPT_DIR%..\skills\system-design-studio\scripts"
) else (
  set "BASE_SCRIPTS=%GLOBAL_DIR%\skills\system-design-studio\scripts"
)

:: Locate Python 3
where python3 >nul 2>&1
if %errorlevel% equ 0 (
  set "PY_CMD=python3"
) else (
  where python >nul 2>&1
  if %errorlevel% equ 0 (
    set "PY_CMD=python"
  ) else (
    echo [ERROR] Python 3 was not found in your PATH. Please install Python 3 from https://python.org
    exit /b 1
  )
)

if "%~1"=="" goto usage
if /i "%~1"=="init" goto do_init
if /i "%~1"=="dashboard" goto do_dashboard
if /i "%~1"=="serve" goto do_dashboard
if /i "%~1"=="tracker" goto do_dashboard
if /i "%~1"=="dummy" goto do_dummy
if /i "%~1"=="demo" goto do_dummy
if /i "%~1"=="revisions" goto do_revisions
if /i "%~1"=="revision" goto do_revisions
if /i "%~1"=="rev" goto do_revisions
if /i "%~1"=="projects" goto do_projects
if /i "%~1"=="list" goto do_projects
if /i "%~1"=="switch" goto do_switch
if /i "%~1"=="open" goto do_switch
if /i "%~1"=="notes" goto do_notes
if /i "%~1"=="delete" goto do_delete
if /i "%~1"=="remove" goto do_delete
if /i "%~1"=="rm" goto do_delete
if /i "%~1"=="rollback" goto do_rollback
if /i "%~1"=="restore" goto do_rollback
if /i "%~1"=="undo" goto do_rollback
if /i "%~1"=="checkpoints" goto do_checkpoints
if /i "%~1"=="curriculum" goto do_curriculum
if /i "%~1"=="config" goto do_config
if /i "%~1"=="status" goto do_status
if /i "%~1"=="update" goto do_update
if /i "%~1"=="upgrade" goto do_update
if /i "%~1"=="version" goto do_version
if /i "%~1"=="-v" goto do_version
if /i "%~1"=="--version" goto do_version
if /i "%~1"=="help" goto usage
if /i "%~1"=="-h" goto usage
if /i "%~1"=="--help" goto usage

:usage
echo ============================================================================
echo   SYSTEM DESIGN STUDIO CLI (sds) - v4.2.0
echo ============================================================================
echo Usage: sds ^<command^> [options]
echo.
echo Core Commands:
echo   sds init [options]         Initialize or scaffold a project learning instance
echo   sds dashboard [options]    Launch interactive curriculum studio ^& workbench on localhost
echo   sds dummy [options]        Launch dashboard for local dummy test project
echo   sds revisions [options]    Review high-yield invariants ^& trade-off defenses
echo   sds list / projects        List registered projects, tracks, and progress
echo   sds switch ^<id^>            Switch active project context
echo   sds notes [id]             List generated study notes for active project
echo   sds delete ^<id^>            Safely delete a project instance
echo.
echo State ^& Safety:
echo   sds rollback [--steps N]   Roll back state to a previous atomic checkpoint
echo   sds checkpoints            List recent state snapshots and Git commits
echo   sds curriculum [options]   Configure, prune, or reorder curriculum tracks
echo   sds config [key] [val]     Inspect or dynamically update settings
echo   sds status                 Display current living cursor and topic metrics
echo   sds update                 Update studio skills to the latest release
echo   sds version                Print version information
echo ============================================================================
exit /b 0

:do_init
shift
where bash >nul 2>&1
if %errorlevel% equ 0 (
  bash "%BASE_SCRIPTS%\init-learning-instance.sh" %*
) else (
  %PY_CMD% "%BASE_SCRIPTS%\manage-projects.py" init %*
)
exit /b %errorlevel%

:do_dashboard
shift
%PY_CMD% "%BASE_SCRIPTS%\serve-dashboard.py" %*
exit /b %errorlevel%

:do_dummy
shift
set "DUMMY_DIR="
if exist "%SCRIPT_DIR%..\dummy-project\.system-design" (
  set "DUMMY_DIR=%SCRIPT_DIR%..\dummy-project\.system-design"
) else if exist "%CD%\dummy-project\.system-design" (
  set "DUMMY_DIR=%CD%\dummy-project\.system-design"
)
if "%DUMMY_DIR%"=="" (
  echo [ERROR] dummy-project\.system-design not found.
  exit /b 1
)
echo Launching System Design Studio Dashboard for Dummy Project...
%PY_CMD% "%BASE_SCRIPTS%\serve-dashboard.py" --instance-dir "%DUMMY_DIR%" %*
exit /b %errorlevel%

:do_revisions
shift
%PY_CMD% "%BASE_SCRIPTS%\update-revisions.py" %*
exit /b %errorlevel%

:do_projects
shift
%PY_CMD% "%BASE_SCRIPTS%\manage-projects.py" list %*
exit /b %errorlevel%

:do_switch
shift
%PY_CMD% "%BASE_SCRIPTS%\manage-projects.py" switch %*
exit /b %errorlevel%

:do_notes
shift
%PY_CMD% "%BASE_SCRIPTS%\manage-projects.py" notes %*
exit /b %errorlevel%

:do_delete
shift
%PY_CMD% "%BASE_SCRIPTS%\manage-projects.py" delete %*
exit /b %errorlevel%

:do_rollback
shift
%PY_CMD% "%BASE_SCRIPTS%\git-checkpoint.py" rollback %*
exit /b %errorlevel%

:do_checkpoints
shift
%PY_CMD% "%BASE_SCRIPTS%\git-checkpoint.py" list %*
exit /b %errorlevel%

:do_curriculum
shift
%PY_CMD% "%BASE_SCRIPTS%\configure-curriculum.py" %*
exit /b %errorlevel%

:do_config
shift
%PY_CMD% "%BASE_SCRIPTS%\merge-settings.py" %*
exit /b %errorlevel%

:do_status
shift
%PY_CMD% "%BASE_SCRIPTS%\sync-status.py" %*
exit /b %errorlevel%

:do_update
shift
if exist "%GLOBAL_DIR%\update.ps1" (
  powershell -ExecutionPolicy Bypass -File "%GLOBAL_DIR%\update.ps1" %*
) else if exist "%GLOBAL_DIR%\update.sh" (
  where bash >nul 2>&1 && bash "%GLOBAL_DIR%\update.sh" %*
) else (
  powershell -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/alph-a07/system-design-studio/main/update.ps1 | iex"
)
exit /b %errorlevel%

:do_version
echo System Design Studio CLI v4.2.0
exit /b 0
