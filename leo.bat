@echo off
cd /d "%~dp0"
python "%~dp0leo.py"
if %ERRORLEVEL% equ 99 exit 0
pause