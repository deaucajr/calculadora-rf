@echo off
REM Agenda a atualizacao do IPCA 3x/dia (10h, 12h, 17h). Duplo-clique UMA vez.
cd /d "%~dp0"
python scripts\atualizar_ipca.py --agendar
echo.
pause
