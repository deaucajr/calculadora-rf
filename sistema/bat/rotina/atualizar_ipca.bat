@echo off
:: Atualiza o IPCA historico (BACEN) e a projecao ANBIMA.
:: Nao usa a API da calculadora B3 (zero custo).
:: Opcional: passe --refresh-ativos para re-importar VNA exata dos ativos IPCA+
::   (usa a API B3 apenas se houve mes novo de IPCA).
::
:: Uso: atualizar_ipca.bat [--refresh-ativos]

cd /d "%~dp0..\..\"
python scripts\atualizar_ipca.py %*
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao atualizar IPCA.
    pause
    exit /b 1
)
echo [OK] IPCA e projecao ANBIMA atualizados.
