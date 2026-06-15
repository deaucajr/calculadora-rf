"""
SUBSTITUIDO pelo fluxo Excel.

Use o CADASTRO_ATIVO.xlsx:
  1. Abra  sistema/dist/CADASTRO_ATIVO.xlsx
  2. Preencha a aba 'Identificacao' (campos amarelos)
  3. Cole o fluxo na aba 'Fluxo_de_Caixa'  (Data | Paga Juros | % Amort | Taxa)
  4. Salve e rode:
       python scripts/importar_planilha.py CADASTRO_ATIVO.xlsx

Para gerar um novo template em branco:
  python scripts/gerar_template_ativo.py
"""
print(__doc__)
