@echo off
start "" pythonw vna_download_manager.py
if errorlevel 1 (
  start "" python vna_download_manager.py
)
exit
