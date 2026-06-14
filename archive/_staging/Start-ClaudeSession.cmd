@echo off
rem ===================================================================
rem  Start-ClaudeSession.cmd - przygotowanie sesji Claude Cowork (ZW).
rem  Sync repo + wczytanie promptu sesji do schowka.
rem  Uzycie:  Start-ClaudeSession.cmd
rem           Start-ClaudeSession.cmd ZW
rem           Start-ClaudeSession.cmd ZW sync/prompts/1.7g-ma-global-dt.md
rem ===================================================================
setlocal
set "TAG=%~1"
if "%TAG%"=="" set "TAG=ZW"
set "PROMPT=%~2"
if "%PROMPT%"=="" set "PROMPT=sync/prompts/1.7g-ma-global-dt.md"
set "REPO=%~dp0"
if "%REPO:~-1%"=="\" set "REPO=%REPO:~0,-1%"
title SchemaGen Claude Session - %TAG%
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-ClaudeSession.ps1" -MachineTag %TAG% -RepoPath "%REPO%" -PromptFile "%PROMPT%"
endlocal
pause
