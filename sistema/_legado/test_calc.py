import sys
sys.path.insert(0, ".")
from src.calc import calc_pu, calc_yield

print("=== Validacao calculo local vs API ===\n")

# AAJR11 - PU dado yield
r1 = calc_pu("AAJR11", 3.5)
api_pu = 1178.6260
diff = abs(r1["PU"] - api_pu)
print("AAJR11 | yield=3.5%")
print(f"  PU local  : {r1['PU']:.6f}")
print(f"  PU API    : {api_pu:.6f}")
print(f"  Diferenca : {diff:.8f}  ({'OK' if diff < 0.01 else 'ATENCAO'})")
print(f"  Duration  : {r1['duration']:.4f} anos")
print()

# AAJR11 - yield dado PU
r2 = calc_yield("AAJR11", 1178.626)
print("AAJR11 | PU=1178.626")
print(f"  Yield local   : {r2['yield']:.6f}%")
print(f"  Yield contrato: 3.5%")
print(f"  Diferenca     : {abs(r2['yield'] - 3.5):.8f}")
print()

# 15L0676664 - CRI IPCA
r3 = calc_pu("15L0676664", 2.5)
api_pu3 = 9990.0513
diff3 = abs(r3["PU"] - api_pu3)
print("15L0676664 | yield=2.5%")
print(f"  PU local  : {r3['PU']:.6f}")
print(f"  PU API    : {api_pu3:.6f}")
print(f"  Diferenca : {diff3:.4f}  ({'OK' if diff3 < 1.0 else 'ATENCAO'})")
print(f"  Duration  : {r3['duration']:.4f} anos")
print()

# 25L02629706 - CRA CDI
r4 = calc_pu("25L02629706", 100.0)
api_pu4 = 1067.5808
diff4 = abs(r4["PU"] - api_pu4)
print("25L02629706 | yield=100%")
print(f"  PU local  : {r4['PU']:.6f}")
print(f"  PU API    : {api_pu4:.6f}")
print(f"  Diferenca : {diff4:.4f}  ({'OK' if diff4 < 1.0 else 'ATENCAO'})")
print(f"  Duration  : {r4['duration']:.4f} anos")
print()

print("=== Teste sensibilidade (sem chamada API) ===")
for yield_test in [2.5, 3.0, 3.5, 4.0, 5.0]:
    r = calc_pu("AAJR11", yield_test)
    print(f"  AAJR11 yield={yield_test:.1f}%  PU={r['PU']:.4f}  dur={r['duration']:.4f}")
