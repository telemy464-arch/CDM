@echo off
chcp 65001 >nul
title CDM - Cloud Download Manager — Build EXE
color 0A
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║      CDM - Cloud Download Manager v2.0 Builder       ║
echo  ║      Official Production Release                     ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install Python 3.8+ first.
    pause & exit /b 1
)

:: Install dependencies
echo [1/4] Installing dependencies...
pip install pyinstaller yt-dlp pillow pyperclip requests --quiet

:: Build with PyInstaller
echo [2/4] Building CDM.exe with PyInstaller...
pyinstaller CDM.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed!
    pause & exit /b 1
)

echo [3/4] Build complete!
echo.

:: Check if Inno Setup is available
set INNO_PATH=
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set INNO_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"  set INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"        set INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe

if "%INNO_PATH%"=="" (
    echo.
    echo  ════════════════════════════════════════════════════════
    echo  ✅ EXE Built Successfully!
    echo     Location: dist\CDM.exe
    echo.
    echo  📦 To create installer: Install Inno Setup 6
    echo  ════════════════════════════════════════════════════════
) else (
    echo [4/4] Building Setup Installer with Inno Setup...
    mkdir "installer\output" 2>nul
    "%INNO_PATH%" "installer\CDM_Setup.iss"
    if not errorlevel 1 (
        copy /y "installer\output\CDM_Setup_v2.0.exe" "CDM_Setup_v2.0.exe" >nul
        echo.
        echo  ════════════════════════════════════════════════════════════
        echo  ✅ CDM SETUP BUILT SUCCESSFULLY!
        echo     Location: CDM_Setup_v2.0.exe
        echo  ════════════════════════════════════════════════════════════
    )
)

echo.
echo  ✅ Portable EXE: dist\CDM.exe
echo  📦 Installer: CDM_Setup_v2.0.exe
echo.
pause
