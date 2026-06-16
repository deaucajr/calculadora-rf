@echo off
:: Compara o universo da B3 (DEB, CRI, CRA) com os CSVs locais.
:: Mostra quais ativos existem na B3 mas nao estao cadastrados localmente.
::
:: Uso:
::   verificar_ativos_b3.bat              -> so relata o que falta
::   verificar_ativos_b3.bat --baixar     -> cadastra os que faltam (chama API)
::   verificar_ativos_b3.bat --refresh    -> reconsulta o universo B3 (sem cache)
::
:: ATENCAO: --baixar consume chamadas na API da calculadora B3 (tem custo).

cd /d "%~dp0..\..\"
python scripts\verificar_cadastro.py %*
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha na verificacao de cadastro.
    pause
    exit /b 1
)
