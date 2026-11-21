@echo off
start "" pythonw cdm_download_manager.pyw
if errorlevel 1 (
  start "" python cdm_download_manager.py
)
exit
