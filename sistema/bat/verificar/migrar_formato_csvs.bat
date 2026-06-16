@echo off
:: Migra todos os CSVs de fluxo do formato legado (META/FLUXO/VNA)
:: para o formato novo (chave-valor + tabela DATA/FLUXO_TAI/TIPO).
::
:: Uso:
::   migrar_formato_csvs.bat             -> migra tudo (irreversivel sem backup)
::   migrar_formato_csvs.bat --dry-run   -> so mostra o que seria migrado

cd /d "%~dp0..\..\"
python scripts\migrar_csvs.py %*
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha na migracao.
    pause
    exit /b 1
)
