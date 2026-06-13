@echo off
rem ===================================================================
rem  Start-GitSync.cmd - widoczne okno z logiem daemona na zywo.
rem  Repo = folder, w ktorym lezy ten plik (dziala na ZW i Filip).
rem  Podwojne klikniecie albo:  Start-GitSync.cmd ZW  /  Start-GitSync.cmd Filip
rem  Okno NIE zamyka sie po zatrzymaniu (-NoExit). Stop = zamknij okno / Ctrl+C.
rem ===================================================================
setlocal
set "TAG=%~1"
if "%TAG%"=="" set /p "TAG=Podaj tag komputera (ZW / Filip): "
set "REPO=%~dp0"
if "%REPO:~-1%"=="\" set "REPO=%REPO:~0,-1%"
title SchemaGen GitSync - %TAG%
powershell -NoProfile -ExecutionPolicy Bypass -NoExit -File "%~dp0GitSyncDaemon.ps1" -MachineTag %TAG% -RepoPath "%REPO%" -Toast
endlocal
