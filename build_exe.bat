@echo off
setlocal

cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0compile_to_exe.ps1"
exit /b %errorlevel%
