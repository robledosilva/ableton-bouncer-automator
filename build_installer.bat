@echo off
setlocal enabledelayedexpansion
title Ableton Bounce Automator — Build Installer

echo.
echo ============================================================
echo   Ableton Bounce Automator — Build Script
echo ============================================================
echo.

:: ── Step 1: Build the exe with cx_Freeze ─────────────────────────────────
echo [1/3] Building executable with cx_Freeze...
python setup.py build
if errorlevel 1 (
    echo.
    echo ERROR: cx_Freeze build failed. Make sure you have:
    echo   pip install cx_freeze pywin32 pyautogui Pillow
    pause & exit /b 1
)

:: ── Step 2: Find the build output directory ───────────────────────────────
echo.
echo [2/3] Locating build output...

set "BUILD_DIR="
for /d %%D in (build\exe.*) do (
    set "BUILD_DIR=%%D"
)

if not defined BUILD_DIR (
    echo ERROR: Could not find cx_Freeze output in build\exe.*
    pause & exit /b 1
)
echo     Found: %BUILD_DIR%

:: Copy build output to installer\dist\ (fixed path for .iss)
if exist installer\dist rmdir /s /q installer\dist
xcopy /e /i /q "%BUILD_DIR%" "installer\dist" > nul
if errorlevel 1 (
    echo ERROR: Could not copy build output to installer\dist\
    pause & exit /b 1
)
echo     Copied to installer\dist\

:: ── Step 3: Compile the Inno Setup installer ─────────────────────────────
echo.
echo [3/3] Compiling installer with Inno Setup...

:: Look for ISCC in common locations
set "ISCC="
for %%P in (
    "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    "%ProgramFiles%\Inno Setup 6\ISCC.exe"
    "%ProgramFiles(x86)%\Inno Setup 5\ISCC.exe"
    "%ProgramFiles%\Inno Setup 5\ISCC.exe"
) do (
    if exist %%P set "ISCC=%%P"
)

:: Also check PATH
if not defined ISCC (
    where iscc >nul 2>&1
    if not errorlevel 1 set "ISCC=iscc"
)

if not defined ISCC (
    echo.
    echo ERROR: Inno Setup not found.
    echo Please install it from https://jrsoftware.org/isdownload.php
    echo Then re-run this script.
    pause & exit /b 1
)

echo     Using: %ISCC%
%ISCC% "installer\installer.iss"
if errorlevel 1 (
    echo.
    echo ERROR: Inno Setup compilation failed.
    pause & exit /b 1
)

:: ── Done ─────────────────────────────────────────────────────────────────
echo.
echo ============================================================
echo   SUCCESS!
echo   Installer: installer\output\AbletonBounceAutomator_Setup_v2.0.exe
echo ============================================================
echo.
pause
