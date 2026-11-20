@echo off
title VnA Download Manager - EXE Builder
echo ============================================
echo  VnA Download Manager - EXE banano hocche
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

echo [1/3] PyInstaller install hocche...
python -m pip install --upgrade pyinstaller
if errorlevel 1 (
  echo PyInstaller install holo na - internet check koro.
  pause
  exit /b 1
)

echo.
echo [2/3] EXE build hocche (2-3 minute lagte pare)...
python -m PyInstaller --onefile --windowed --name "VnA Download Manager" --clean vna_download_manager.py
if errorlevel 1 (
  echo Build fail koreche.
  pause
  exit /b 1
)

echo.
echo [3/3] Done!
echo EXE file-ta ekhane ache:
echo   %CD%\dist\VnA Download Manager.exe
echo.
echo Oita jekono folder-e niye double-click korlei cholbe - Python lagbe na.
pause
