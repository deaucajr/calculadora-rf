# RF_Calc — Guia Completo de Fórmulas

Todas as fórmulas, exemplos com outputs reais e convenções de mercado.

---

## CONVENÇÕES GERAIS

| Convenção | Valor |
|-----------|-------|
| Ano comercial (dias úteis) | 252 du |
| Dias úteis por mês (ANBIMA) | 21 du |
| Truncamento B3 | 6 casas decimais (Int(PU × 1e6) / 1e6) |
| Separador CSV | TAB |
| Decimal CSV | ponto (.) |
| Datas | YYYY-MM-DD (ISO) |

---

## 1. IPCA+ e PRÉ

### Fórmula do PU

```
PU(data, taxa) = [ Σ FC_i% / (1 + taxa/100)^(du_i/252) ] × VNA(data)
```

Onde:
- `FC_i%` = VF_i / VNA(data_importação) — percentual data-independente
- `du_i` = dias úteis entre data de cálculo e data do evento i
- `VNA(data)` = VNE × fator_IPCA(data) (para IPCA+) ou constante (para PRÉ)

### Exemplo real: EGIEA6 (IPCA+)

| Parâmetro | Valor |
|-----------|-------|
| Ticker | EGIEA6 |
| Indexador | IPCA+ |
| Emissor | EGIE |
| VNE | 1000 |
| Taxa | 6,2474% a.a. |
| Data cálculo | 11/06/2026 |
| PU B3 | 1448,562894 |
| PU RF_Calc | 1448,562894 |
| **Erro** | **0,000000 R$** ✅ |

```
=RF_PU("EGIEA6"; 6,2474; "11/06/2026")
→ 1448,562894
```

### VNA (Valor Nominal Atualizado)

#### IPCA sem amortização
```
VNA(t) = VNE × Π (1 + IPCA_m/100)^(du_m/21)
```

#### IPCA com amortização (IPCA+ amortizante)
```
VNA(d) = VNA_ancora × (1 - cumul_d%) / (1 - cumul_ancora%) × IPCA(d)/IPCA(ancora)
```

Onde `cumul_x%` = soma dos percentuais de amortização até a data x.

### Exemplo: 18H0193630 (IPCA+ amortizante)

```
=RF_PU("18H0193630"; 6,5; HOJE())
→ ~1025 a 1050 (varia com a data)
```

---

## 2. CDI+ (DI-SPREAD)

### Fórmula

Fluxos importados por data. Para taxa diferente da referência:

```
PV_i(y1) = PV_i(y0) × ((1 + y0/100) / (1 + y1/100))^(du_i/252)
```

O Present Value (PV) da B3 já inclui o desconto CDI + spread.
Ao mudar o spread de y0 para y1, ajusta-se apenas a parte do spread.

### Exemplo real: BRMLA9 (CDI+)

| Parâmetro | Valor |
|-----------|-------|
| Ticker | BRMLA9 |
| Indexador | CDI+ (DI-SPREAD) |
| Spread | 1,2% a.a. |
| Taxa | 1,2% a.a. |
| Data cálculo | 13/06/2026 |

```
=RF_PU("BRMLA9"; 1,2; "13/06/2026")
→ PU com erro < 0,01 vs B3 ✅
```

---

## 3. %CDI (DI-PERC)

### Curva DI Implícita

Para ativos %CDI (taxa ≥ 50), usa-se a curva DI implícita dos próprios fluxos:

```
FD_i = VF_i / PV_i  (fator de desconto por vértice)
g = (FD_i / FD_{i-1})^(1/Δdu) - 1  (CDI forward diário)
FD_i(taxa) = Π (1 + g × taxa/100)^Δdu
PV_i = VF_i / FD_i(taxa)
```

### Exemplo real: VLHA11 (%CDI)

```
=RF_PU("VLHA11"; 98; "13/06/2026")
→ PU com erro ~0,005 vs B3 ✅
```

---

## 4. DI FUTURO (DI1F*)

### Fórmulas

```
PU = 100000 / (1 + taxa/100)^(du/252)
Taxa = ((100000 / PU)^(252/du) - 1) × 100
Duration = du / 252
```

Vencimento = primeiro dia útil do mês/ano do contrato.

### Mapeamento de meses

| Letra | Mês | Letra | Mês |
|-------|-----|-------|-----|
| F | Jan | N | Jul |
| G | Fev | Q | Ago |
| H | Mar | U | Set |
| J | Abr | V | Out |
| K | Mai | X | Nov |
| M | Jun | Z | Dez |

### Exemplo real: DI1F30

```
=RF_PU("DI1F30"; 14,40; "15/06/2026")
→ PU = 100000 / (1 + 14,40/100)^(du/252)
→ Ex: du=900 → PU ≈ 100000 / (1,144)^(900/252) ≈ 62.050,32
```

---

## 5. NTN-B

### Fórmula

```
PU = Σ [cupom_semestral / (1 + taxa/100)^(du_i/252)] + 1 / (1 + taxa/100)^(du_venc/252)
```

Cupom semestral = (1,06)^0,5 - 1 = 2,95630140987% a.s.

### Mapeamento NTN-B

| Ticker | Vencimento | Código Cetip |
|--------|-----------|--------------|
| NTN-B 24 / NTNB24 | 15/08/2024 | 76019920240815 |
| NTN-B 26 / NTNB26 | 15/08/2026 | 76019920260815 |
| NTN-B 30 / NTNB30 | 15/08/2030 | 76019920300815 |
| NTN-B 35 / NTNB35 | 15/05/2035 | 76019920350515 |
| NTN-B 40 / NTNB40 | 15/08/2040 | 76019920400815 |
| NTN-B 45 / NTNB45 | 15/05/2045 | 76019920450515 |
| NTN-B 50 / NTNB50 | 15/08/2050 | 76019920500815 |
| NTN-B 55 / NTNB55 | 15/05/2055 | 76019920550515 |
| NTN-B 60 / NTNB60 | 15/08/2060 | 76019920600815 |

Regra: ano **par** → mês 08 (Agosto); ano **ímpar** → mês 05 (Maio). Dia sempre 15.

### Exemplo
```
=RF_PU("NTN-B 30"; 6,5; "15/06/2026")
→ ~4500 a 5000 (varia com VNA do IPCA)
```

---

## 6. DURATION

### Macaulay Duration
```
D = Σ [t_i × PV_i] / Σ PV_i  (em anos, t_i = du_i/252)
```

### DV01 (sensibilidade a +1 bp)
```
DV01 = D / (1 + taxa/100) × PU × 0,0001  (em R$)
```

### Exemplo
```
=RF_DURATION("EGIEA6"; 6,2474; "11/06/2026")
→ ~4,23 anos

=RF_DV01("EGIEA6"; 6,2474; "11/06/2026")
→ ~0,058 R$
```

---

## 7. SWAP / BREAKEVEN / EQUIVALÊNCIA

### Cadeia de equivalência

```
%CDI ←A→ CDI+spread ←B→ PRÉ ←C→ IPCA+spread
```

### A: %CDI ↔ CDI+

```
spread_cdi = [(1 + CDI/100)^(pct/100 - 1) - 1] × 100
pct_cdi = [1 + ln(1 + spread/100) / ln(1 + CDI/100)] × 100
```

### B: CDI+ ↔ PRÉ
```
PRE_eq = CDI_proj + spread_cdi  (aproximação aditiva)
```

### C: Fisher (PRÉ ↔ IPCA+)
```
inflação_implícita = [(1 + PRE/100) / (1 + IPCA_real/100) - 1] × 100
IPCA_real = [(1 + PRE/100) / (1 + inflação/100) - 1] × 100
```

### Exemplos

```
=RF_INFLA_IMPLICITA(12,5; 6,5)
→ 5,63% a.a.  (inflação implícita)

=RF_BREAKEVEN_CDI(12,5; 100)
→ 12,50% a.a.  (CDI de equilíbrio)

=RF_PCT_PARA_CDI(98; 13,5)
→ -0,27% a.a.  (spread CDI+ equivalente a 98% CDI)

=RF_CDI_PARA_IPCA(2,0; 13,5; 5,2)
→ 10,05% a.a.  (CDI+2,0% equivale a IPCA+10,05%)
```

---

## 8. YTC / YTW

### Yield to Call
TIR que iguala PU aos fluxos até a data de call + preço de call.

### Yield to Worst
```
YTW = min(YTM, YTC_1, YTC_2, ..., YTC_n)
```

Datas de call vêm do cabeçalho do CSV:
```
META<tab>CALL_DATES<tab>2028-06-15,2029-06-15
META<tab>CALL_PREMIUMS<tab>0.5,0.25
```

### Exemplo
```
=RF_YTC("EGIEA6"; 1447; "15/06/2026"; "15/06/2028")
→ ~6,35%  (YTC se resgatado em 2028)

=RF_YTW("EGIEA6"; 1447; "15/06/2026")
→ ~6,35%  (menor entre YTM e YTCs)
```

---

## 9. GROSS-UP

### Fórmula
```
taxed_rate = ((1 + rate/100)^(1 - aliquota) - 1) × 100
```

Alíquota padrão IR = 15% para corporativos.

### Exemplo
```
=RF_GROSSUP("VALE33"; 1050; HOJE())
→ taxa com gross-up (se CSV tem TAXED_RATE da FI Analytics, usa valor exato)
```

---

## 10. FLUXO DE CAIXA (com % Tai)

### Saída do RF_FLUXO
```
DATA       | EVENTO | DU  | VF         | PV @ 6,5%  | %TAI    | %AMORT
2026-12-15 | J      | 125 | 65,000000  | 63,214500   | 6,5000  | 0
2027-06-15 | J      | 250 | 65,000000  | 61,108700   | 6,5000  | 0
2027-12-15 | J+A    | 375 | 565,000000 | 515,427800  | 6,5000  | 50,0000
```

### Exemplo
```
=RF_FLUXO("EGIEA6"; 6,5; HOJE())
→ Matriz 7 colunas: DATA | EVENTO | DU | VF | PV | %TAI | %AMORT
```

---

## FONTES DE DADOS

| Fonte | O que fornece | Prioridade |
|-------|--------------|------------|
| **FI Analytics** | Fluxos de caixa completos, M2M, gross-up, DI equivalente, juros incorporados | 🔴 Primária |
| **BACEN SGS** | CDI diário (série 12), IPCA mensal (série 433) | 🟡 Dados de mercado |
| **ANBIMA Data** | Características, ratings, amortizações, garantias | 🟢 Enriquecimento |
| **B3 TaxaSwap** | Curva DI histórica (desde 2006) | 🟢 Curva histórica |
| **ANBIMA Focus** | Projeções IPCA | 🟡 Projeções |

---

*RF_Calc v3 — Documentação atualizada em 2026-06-15*
