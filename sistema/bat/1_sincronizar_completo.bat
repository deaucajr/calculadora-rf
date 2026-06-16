@echo off
chcp 65001 >nul
title RF_Calc — Sincronizacao Completa (FI Analytics)

echo ================================================
echo   RF_Calc — Sincronizacao Completa
echo ================================================
echo.
echo Este script baixa TODOS os ativos do FI Analytics,
echo calcula VNA localmente e atualiza os CSVs.
echo.
echo Pressione Ctrl+C para cancelar, ou qualquer tecla para continuar...
pause >nul

cd /d "%~dp0.."

echo.
echo [%date% %time%] Iniciando sincronizacao completa...
echo.

python -m src.sync_engine --all

echo.
echo ================================================
echo   CONCLUIDO!
echo ================================================
echo.
echo Pasta de fluxos: sistema\data\fluxos\
echo Total de CSVs gerados:
dir /b data\fluxos\*.csv 2>nul | find /c /v ""
echo.
echo Proximo passo: execute 2_sincronizar_rapido.bat diariamente.
echo.
pause
