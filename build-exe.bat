@echo off
title CDM - Cloud Download Manager - EXE Builder
echo ============================================
echo  CDM - Cloud Download Manager - EXE Builder
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
  echo Python pawa jay ni!
  echo Age python.org theke Python install koro ("Add to PATH"-e tick dio),
  echo tarpor ei file-ta abar double-click koro.
  pause
  exit /b 1
)

echo [1/3] Dependencies check...
python -m pip install --upgrade pyinstaller yt-dlp pillow pyperclip requests --quiet

echo.
echo [2/3] Building CDM.exe with CDM.spec...
python -m PyInstaller CDM.spec --clean --noconfirm
if errorlevel 1 (
  echo Build fail koreche.
  pause
  exit /b 1
)

echo.
echo [3/3] Done!
echo EXE file-ta ekhane ache:
echo   %CD%\dist\CDM.exe
echo.
echo CDM Setup toiri korte BUILD.bat run koro.
pause
