@echo off
chcp 65001 >nul
title RF_Calc — Validar Calculos

echo ================================================
echo   RF_Calc — Validacao de Precos
echo ================================================
echo.
echo Compara PU local vs. FI Analytics para uma amostra de ativos.
echo.

cd /d "%~dp0.."

python scripts\validar.py

echo.
pause
