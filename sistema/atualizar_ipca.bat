@echo off
REM Atualiza o IPCA (historico BACEN + projecao ANBIMA) agora. Duplo-clique p/ rodar.
cd /d "%~dp0"
python scripts\atualizar_ipca.py
echo.
pause
