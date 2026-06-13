# Log da Wiki

Log cronológico append-only. Nunca edite entradas passadas.
Formato: `## [YYYY-MM-DD] tipo | descrição`

Para buscar as últimas entradas: `grep "^## \[" log.md | tail -10`

---

## [2026-06-12] criação | Wiki inicializada

- Estrutura criada: `raw/`, `wiki/`, `CLAUDE.md`, `index.md`, `log.md`
- Tema: Negócios / trabalho
- Vault Obsidian já existente aproveitado
- Nenhuma fonte ingerida ainda

## [2026-06-12] criação | Add-in renda fixa v2 (pasta de fluxos)

- Criados: importar_fluxos.py, fluxos/ (_importar, _feriados), excel/DEB_Calc2.bas
- Página [[projeto-addin-fluxos]] criada com arquitetura, layout e métodos
- Validado com EGIEA6: PU motor vs B3 dif 1e-6, DU 100% igual à API

## [2026-06-12] atualização | Add-in v3: PU = cotação x VNA(data)

- Corrigido erro em datas != import: FC%=VF/VNA é data-independente; PU=cotação×VNA(data)
- importar_fluxos.py acumula tabela VNA (1 ponto/data); DEB_Calc2.bas reescrito
- DV01 agora analítico (dur.modif×PU×0,0001); dicas de argumento via MacroOptions
- Validado EGIEA6 11/06 taxa=2: 1448,562894 = B3 (dif 0,000000)

## [2026-06-13] atualização | Add-in instalado e corrigido (build automatico)

- build_xlam.py gera .xlam limpo via COM (corrige FileFormat 55 e modulo duplicado)
- Bug VNAData (ByRef Variant vs Double()) corrigido: funcoes de calculo voltaram
- Validado via COM no .xlam instalado: PU/VNA/duration/taxa exatos (EGIEA6)
- AccessVBOM habilitado p/ gerar e revertido a 0 (seguranca restaurada)

## [2026-06-13] atualizacao | Reformulacao: conserto Excel, RF_, lazy CSV, CDI multi-data

- Excel fechava sozinho: chave OPEN apontava p/ DEB-CALC3.xlam fantasma -> removida (consertado)
- Funcoes renomeadas DEB_* -> RF_* (renda fixa, nao so debenture)
- Storage migrado p/ CSV + lazy load (leve, escala p/ milhares de ativos)
- CDI/%CDI: storage multi-data (blocos FLUXOD por data) + calculo no VBA
- Bug locale corrigido: CDbl("100.0") vira 1000 em pt-BR -> usar Val()
- keep_awake.py: impede hibernacao (ativo 10h)
- importar_todos.py: importacao em massa (3483 ativos) + rotina_diaria.py (agendavel)
- Validado via COM: IPCA exato qualquer data; CDI exato nas datas importadas

## [2026-06-13] validacao | 80/80 batendo; 4 tipos de ativo precificados

- Bug classificacao: indexador vinha do getbonddetails.method; deve vir do calcPU.method
- corrigir_csvs.py: reclassificou 1646 CDI (mal salvos como IPCA) SEM API (deteccao Sum PV vs Sum VF/(1+t)^du)
- DI-PERC (% do CDI): ajuste multiplicativo com CDI diario (_cdi.csv); distincao por magnitude da taxa (>=50)
- Massa: 3469 ativos importados. Validacao 20 papeis x 4 datas = 80/80 dentro de 0.01
- IPCA/PRE/DI-SPREAD exatos (1e-6); DI-PERC ~0.005 (CDI spot vs curva projetada)
- RF_TAXA: intervalo ampliado p/ 0.0001-300 (cobre % do CDI)

## [2026-06-13] curva DI | Curva implicita resolve DI-PERC com exatidao

- Endpoints B3 (taxas referenciais/TxRef1/ajustes) mortos (404/JS) - scraping inviavel
- SOLUCAO: curva DI esta implicita nos PV de cada papel (FD_i = VF_i/PV_i)
- PvCdi (VBA) / _pu_perc_curva (validador): deriva CDI forward por segmento, reaplica %
- DI-PERC: residuo caiu de ~0.009 (CDI spot) para ~1e-5 (curva implicita)
- Nao precisa baixar curva externa; validado 80/80 + add-in via COM
