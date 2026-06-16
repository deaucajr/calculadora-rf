@echo off
:: Atualiza a curva DI/PRE da B3 (endpoint publico, sem custo de API).
:: Roda via: bat\rotina\atualizar_curva.bat
:: Agende no Agendador de Tarefas para rodar toda manha apos a abertura do mercado.

cd /d "%~dp0..\..\"
python src\sync_b3_curve.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao atualizar curva DI/PRE.
    pause
    exit /b 1
)
echo [OK] Curva DI/PRE atualizada.
