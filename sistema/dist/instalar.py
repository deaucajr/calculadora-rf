"""
Instala o add-in RF_Calc no Excel.
Duplo-clique aqui (com o Excel FECHADO).
Sem dependencias externas — pode ser enviado por email.
"""
import os
import shutil
import subprocess
import sys
import winreg
from pathlib import Path


def versao_excel():
    for v in ("16.0", "15.0", "14.0"):
        try:
            winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           f"Software\\Microsoft\\Office\\{v}\\Excel")
            return v
        except FileNotFoundError:
            continue
    return "16.0"


def main():
    dist = Path(__file__).resolve().parent

    print("=== Instalando RF_Calc ===")

    # 1. Excel precisa estar fechado
    saida = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq EXCEL.EXE"],
        capture_output=True, text=True
    ).stdout.upper()
    if "EXCEL.EXE" in saida:
        print("Feche o Excel e rode de novo.")
        input("\nPressione Enter para sair...")
        return

    # 2. Copia o add-in para a pasta de AddIns do usuario
    addins = Path(os.environ["APPDATA"]) / "Microsoft" / "AddIns"
    addins.mkdir(parents=True, exist_ok=True)
    shutil.copy2(dist / "RF_Calc.xlam", addins / "RF_Calc.xlam")
    print(f"[ok] add-in copiado para {addins}")

    # 3. Registra o auto-load no registro do Windows
    ver = versao_excel()
    key_path = f"Software\\Microsoft\\Office\\{ver}\\Excel\\Options"
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
    winreg.SetValueEx(key, "OPEN", 0, winreg.REG_SZ, '/R "RF_Calc.xlam"')
    winreg.CloseKey(key)
    print(f"[ok] auto-load registrado (Office {ver})")

    # 4. Le a pasta de dados de rf_fluxos_dir.txt (ou pede ao usuario)
    dados = ""
    path_file = dist / "rf_fluxos_dir.txt"
    if path_file.exists():
        for linha in path_file.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#"):
                dados = linha
                break

    if not dados:
        print()
        print("Cole o caminho da pasta de fluxos (onde estao os .csv).")
        print(r"  Ex. rede:     \\servidor\rendafixa\fluxos")
        print(r"  Ex. OneDrive: C:\Users\voce\OneDrive - Empresa\RendaFixa\fluxos")
        dados = input("Caminho: ").strip().strip('"')

    # 5. Grava a config que o add-in le em runtime
    cfg = addins / "rf_fluxos.txt"
    cfg.write_text(dados, encoding="utf-8")
    print(f"[ok] caminho dos dados: {dados}")

    # 5b. Garante as pastas irmas (fluxos_manual / fluxos_antigo)
    try:
        pai = Path(dados.rstrip("\\")).parent
        for sub in ("fluxos_manual", "fluxos_antigo"):
            (pai / sub).mkdir(parents=True, exist_ok=True)
        print(f"[ok] pastas manual/antigo prontas em {pai}")
    except Exception:
        pass

    # 6. Valida e, se for OneDrive, fixa os arquivos offline
    dados_path = Path(dados)
    if dados_path.exists():
        if "onedrive" in dados.lower():
            print("OneDrive detectado: fixando arquivos p/ ficarem sempre disponiveis offline...")
            subprocess.run(
                ["attrib", "+P", "/S", "/D", f"{dados}\\*"],
                capture_output=True
            )
            print("[ok] arquivos fixados (pode levar uns minutos p/ o OneDrive baixar tudo)")
    else:
        print(f"[ATENCAO] a pasta nao foi encontrada agora: {dados}")
        print("          Verifique a rede/VPN/permissao. O add-in funcionara quando ela estiver acessivel.")

    print()
    print("PRONTO. Feche e abra o Excel: as funcoes RF_* carregam sozinhas.")
    print("Teste numa celula:  =RF_LISTAR()")
    input("\nPressione Enter para sair...")


if __name__ == "__main__":
    main()
