@echo off
REM Instala o add-in RF_Calc no Excel. Duplo-clique aqui (Excel fechado).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar.ps1"
echo.
pause
