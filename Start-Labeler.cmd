@echo off
rem ===================================================================
rem  Start-Labeler.cmd - widoczne okno z serwerem labelera na zywo.
rem  Repo = folder, w ktorym lezy ten plik (dziala na ZW i Filip).
rem  Podwojne klikniecie -> http://localhost:8765 (przegladarka po ~2 s)
rem  Okno NIE zamyka sie po zatrzymaniu (-NoExit). Stop = zamknij okno / Ctrl+C.
rem  Log: sync\.labeler.log
rem ===================================================================
setlocal
set "REPO=%~dp0"
if "%REPO:~-1%"=="\" set "REPO=%REPO:~0,-1%"
title SchemaGen Labeler
powershell -NoProfile -ExecutionPolicy Bypass -NoExit -File "%~dp0LabelerServe.ps1" -RepoPath "%REPO%"
endlocal
