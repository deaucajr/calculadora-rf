@echo off
chcp 65001 >nul
title RF_Calc — Rotina Diaria Rapida

echo ================================================
echo   RF_Calc — Rotina Diaria (Incremental)
echo ================================================
echo.
echo Atualiza apenas ativos novos ou nao sincronizados hoje.
echo Ideal para rodar toda manha (7h30).
echo.

cd /d "%~dp0.."

echo [%date% %time%] Iniciando rotina diaria...
echo.

python scripts\rotina_diaria_v2.py

echo.
echo ================================================
echo   ROTINA DIARIA CONCLUIDA
echo ================================================
echo.
echo Se os dados nao aparecerem no Excel:
echo   1. Pressione Alt+F8 no Excel
echo   2. Selecione RF_ATUALIZAR
echo   3. Execute
echo.
pause
