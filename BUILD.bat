@echo off
chcp 65001 >nul
title VnA Download Manager — Build EXE
color 0A
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║      VnA Download Manager v2.0 — EXE Builder        ║
echo  ║      IDM-er Dada, Goriber Bondhu                     ║
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

:: Create placeholder icon if missing
echo [2/4] Preparing assets...
if not exist "assets\icon.ico" (
    python -c "
try:
    from PIL import Image, ImageDraw, ImageFont
    import struct, io, os
    os.makedirs('assets', exist_ok=True)
    # Create a simple 64x64 icon
    img = Image.new('RGBA', (64, 64), (26, 26, 46, 255))
    draw = ImageDraw.Draw(img)
    # Background circle
    draw.ellipse([4, 4, 60, 60], fill=(233, 69, 96, 255))
    # Down arrow
    draw.polygon([(32,16),(48,36),(40,36),(40,52),(24,52),(24,36),(16,36)], fill=(255,255,255,255))
    # Save as ICO
    img.save('assets/icon.ico', format='ICO', sizes=[(64,64),(48,48),(32,32),(16,16)])
    print('Icon created.')
except Exception as e:
    print(f'Could not create icon: {e}')
"
)

:: Build with PyInstaller
echo [3/4] Building EXE with PyInstaller...
echo       (This may take 1-3 minutes...)
pyinstaller VnA_Download_Manager.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed!
    echo         Check the output above for errors.
    pause & exit /b 1
)

echo [4/4] Build complete!
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
    echo     Location: dist\VnA_Download_Manager.exe
    echo.
    echo  📦 To create installer (.exe setup):
    echo     1. Download Inno Setup 6: https://jrsoftware.org/isinfo.php
    echo     2. Open installer\VnA_Setup.iss with Inno Setup
    echo     3. Press Ctrl+F9 to compile
    echo     4. Installer will be in: installer\output\
    echo  ════════════════════════════════════════════════════════
) else (
    echo  Found Inno Setup! Building installer...
    mkdir "installer\output" 2>nul
    "%INNO_PATH%" "installer\VnA_Setup.iss"
    if errorlevel 1 (
        echo [WARNING] Inno Setup build had errors. Check manually.
    ) else (
        echo.
        echo  ════════════════════════════════════════════════════════════
        echo  ✅ INSTALLER BUILT SUCCESSFULLY!
        echo     Location: installer\output\VnA_Download_Manager_v2.0_Setup.exe
        echo  ════════════════════════════════════════════════════════════
    )
)

echo.
echo  ✅ EXE: dist\VnA_Download_Manager.exe
echo  📦 Installer: installer\output\ (if Inno Setup was found)
echo  🌐 Chrome Extension: browser_extension\chrome\
echo  🦊 Firefox Extension: browser_extension\firefox\
echo.
pause
