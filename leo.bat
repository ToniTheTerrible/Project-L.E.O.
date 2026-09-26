@echo off
cd /d "C:\Users\Toniz\Desktop\Project-LEO"
python "C:\Users\Toniz\Desktop\Project-LEO\leo.py"
if %ERRORLEVEL% equ 99 exit 0
pause