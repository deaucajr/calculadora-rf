@echo off
chcp 65001 >nul
title RF_Calc — Instalar Add-in no Excel

echo ================================================
echo   RF_Calc — Instalacao do Add-in Excel
echo ================================================
echo.
echo ATENCAO: Certifique-se de que o Excel esta FECHADO.
echo.
echo Pressione qualquer tecla para instalar...
pause >nul

cd /d "%~dp0.."

echo.
echo [1/3] Verificando dependencias Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado! Instale Python 3.11+ primeiro.
    pause
    exit /b 1
)
echo Python OK.

echo.
echo [2/3] Instalando dependencias...
pip install requests pandas openpyxl scipy python-dateutil pywin32 --quiet
echo Dependencias OK.

echo.
echo [3/3] Gerando e instalando add-in...
python addin\build_xlam.py

echo.
echo ================================================
echo   INSTALACAO CONCLUIDA
echo ================================================
echo.
echo Abra o Excel e teste em qualquer celula:
echo   =RF_LISTAR()
echo.
echo Se as funcoes nao aparecerem:
echo   Arquivo ^> Opcoes ^> Suplementos ^> Ir...
echo   Marque "RF_Calc" na lista
echo.
pause
