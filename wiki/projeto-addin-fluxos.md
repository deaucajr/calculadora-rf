---
tipo: projeto
tags: [renda-fixa, excel, vba, addin, debentures, cri, cra, ntn-b, di-futuro, fi-analytics]
fontes: []
atualizado: 2026-06-15
---

# Add-in Excel de Renda Fixa (RF_Calc v3)

Sistema local para precificar QUALQUER ativo de renda fixa brasileiro. Fonte primária: FI Analytics. VNA calculado localmente.

## Arquitetura v3

```
FI Analytics (fonte primária)
    ↓
sync_engine.py  ← baixa fluxos, calcula VNA local, salva CSV + SQLite
    ↓
fluxos/<TICKER>.csv  ← formato otimizado (TAB, % Tai por evento)
    ↓
RF_Calc.xlam (VBA)  ← lazy load, funções RF_*
    ↓
Excel  ← =RF_PU(), =RF_FLUXO(), =RF_GROSSUP(), etc.
```

## Fontes de dados

| Prioridade | Fonte | Propósito |
|-----------|-------|-----------|
| 🔴 Primária | FI Analytics | Fluxos, M2M, gross-up, DI equivalente, juros incorporados |
| 🟡 Mercado | BACEN (SGS) | CDI diário (série 12), IPCA mensal (série 433) |
| 🟢 Enriquecimento | ANBIMA Data | Características, ratings, amortizações |
| 🟢 Histórica | B3 TaxaSwap | Curva DI histórica (desde 2006) |

## Diferenciais vs. versão anterior (B3-only)

1. **Juros incorporados**: FI Analytics já considera accrued interest no PU
2. **VNA local**: não depende mais do VNA da B3; cálculo próprio com IPCA/CDI do BACEN
3. **Gross-up**: taxa com ajuste tributário disponível
4. **DI equivalente**: taxas equivalentes em CDI+ e %CDI direto da API
5. **NTN-B e DI Futuro**: unificados nas funções RF_* (não mais funções separadas)
6. **% Tai por evento**: cada linha do fluxo mostra % de juros e % de amortização

## Formato CSV v3

```
ticker<TAB>EGIEA6
tipo<TAB>DEB
indexador<TAB>IPCA
emissor<TAB>EGIE
method<TAB>IPCA
inicio_rentabilidade<TAB>2021-06-15
vencimento<TAB>2031-06-15
vne<TAB>1000
taxa_ref<TAB>6.2474
data_fluxo<TAB>2026-06-15
vna<TAB>1448.562894
vna_factor<TAB>1.4485628940
fonte<TAB>FI_Analytics
m2m<TAB>1448.562894
duration<TAB>4.231
di_equiv_add<TAB>-1.15
di_equiv_mult<TAB>98.5
taxed_rate<TAB>7.35

DATA<TAB>EVENTO<TAB>VF<TAB>PV<TAB>DU<TAB>TAI_PCT<TAB>AMORT_PCT
2026-12-15<TAB>J<TAB>65.000000<TAB>63.214500<TAB>125<TAB>6.5000000000<TAB>0.0000000000
2027-06-15<TAB>J<TAB>65.000000<TAB>61.108700<TAB>250<TAB>6.5000000000<TAB>0.0000000000
2027-12-15<TAB>J+A<TAB>565.000000<TAB>515.427800<TAB>375<TAB>6.5000000000<TAB>50.0000000000
```

## Conexões

- [[tema-curva-di-historica]] — Metodologia da curva DI histórica
- [[visao-geral]] — Estado atual do projeto
