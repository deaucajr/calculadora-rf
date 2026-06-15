"""
RF_Calc — Instalador rapido (requer internet e acesso ao GitHub)
================================================================

O que faz:
  1. Instala o add-in RF_Calc.xlam no Excel (registro automatico)
  2. Baixa o projeto do GitHub para C:\\Users\\<voce>\\RF_Calc
  3. Instala as dependencias Python (pip)
  4. Baixa dados publicos (feriados, CDI diario, curva DI B3)
  5. Importa os fluxos de todos os ativos (DEB, CRI, CRA) — requer credenciais

Uso:
  python instalar.py              # instala tudo (sem importar ativos)
  python instalar.py --importar   # instala + importa fluxos via API

Pre-requisitos:
  - Python 3.8+
  - Excel instalado e FECHADO
  - Conexao com a internet
  - (para --importar) credenciais da API calculadorarendafixa.com.br

Se voce NAO tem acesso a internet no computador destino:
  Use o instalador autossuficiente (instalar_offline.py) gerado pelo
  script tools/gerar_instalador_offline.py
"""
import os
import sys
import shutil
import subprocess
import winreg
import urllib.request
import urllib.error
import zipfile
import tempfile
from pathlib import Path

REPO_ZIP    = "https://github.com/deaucajr/calculadora-rf/archive/refs/heads/main.zip"
INSTALL_DIR = Path(os.environ.get("USERPROFILE", "C:\\Users\\Public")) / "RF_Calc"
OK, FALHA, PULAR = "[ OK ]", "[FALHA]", "[PULAR]"


def passo(n, titulo):
    print(f"\n{'='*60}\n{n}. {titulo}\n{'='*60}")


def versao_excel():
    for v in ("16.0", "15.0", "14.0"):
        try:
            winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           f"Software\\Microsoft\\Office\\{v}\\Excel")
            return v
        except FileNotFoundError:
            continue
    return "16.0"


def instalar_addin():
    passo(1, "Instalando add-in RF_Calc no Excel")

    saida = subprocess.run(["tasklist", "/FI", "IMAGENAME eq EXCEL.EXE"],
                           capture_output=True, text=True).stdout.upper()
    if "EXCEL.EXE" in saida:
        print(FALHA, "Feche o Excel e rode de novo.")
        return False

    dist = Path(__file__).resolve().parent
    xlam_bin = dist / "RF_Calc.xlam.bin"
    xlam     = dist / "RF_Calc.xlam"
    origem   = xlam_bin if xlam_bin.exists() else xlam if xlam.exists() else None
    if origem is None:
        print(FALHA, f"RF_Calc.xlam.bin nao encontrado em: {dist}")
        return False

    addins = Path(os.environ["APPDATA"]) / "Microsoft" / "AddIns"
    addins.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, addins / "RF_Calc.xlam")
    print(OK, f"add-in copiado para {addins}")

    ver = versao_excel()
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                           f"Software\\Microsoft\\Office\\{ver}\\Excel\\Options")
    winreg.SetValueEx(key, "OPEN", 0, winreg.REG_SZ, '/R "RF_Calc.xlam"')
    winreg.CloseKey(key)
    print(OK, f"auto-load registrado (Office {ver})")
    return True


def baixar_projeto():
    passo(2, "Baixando projeto do GitHub")
    print(f"Destino: {INSTALL_DIR}")

    if INSTALL_DIR.exists() and (INSTALL_DIR / "requirements.txt").exists():
        print(OK, "projeto ja instalado (pulando download)")
        return True

    print("Baixando... (alguns segundos)")
    try:
        tmp_zip = Path(tempfile.mktemp(suffix=".zip"))
        urllib.request.urlretrieve(REPO_ZIP, tmp_zip)
        print(OK, "download concluido")
    except urllib.error.URLError as e:
        print(FALHA, f"sem acesso ao GitHub: {e}")
        print("       Verifique a conexao e tente de novo.")
        print("       Sem internet? Use o instalador offline: instalar_offline.py")
        return False

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(tmp_zip, "r") as z:
                z.extractall(tmpdir)
            extraido = next(Path(tmpdir).iterdir())
            if INSTALL_DIR.exists():
                shutil.rmtree(INSTALL_DIR)
            shutil.copytree(extraido / "sistema", INSTALL_DIR)
        tmp_zip.unlink(missing_ok=True)
        print(OK, f"projeto instalado em {INSTALL_DIR}")
        return True
    except Exception as e:
        print(FALHA, f"erro ao extrair: {e}")
        return False


def instalar_dependencias():
    passo(3, "Instalando dependencias Python")
    req = INSTALL_DIR / "requirements.txt"
    if not req.exists():
        print(FALHA, "requirements.txt nao encontrado")
        return False
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(OK, "dependencias instaladas")
        return True
    print(FALHA, r.stderr[-600:])
    return False


def configurar_dados():
    passo(4, "Criando banco e baixando dados publicos (CDI, curva B3)")
    fluxos = INSTALL_DIR / "data" / "fluxos"
    fluxos.mkdir(parents=True, exist_ok=True)
    (INSTALL_DIR / "data" / "fluxos_manual").mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(INSTALL_DIR))
    sys.path.insert(0, str(INSTALL_DIR / "scripts"))

    try:
        from src.db import init_db
        init_db()
        print(OK, "banco rf.db criado")
    except Exception as e:
        print(FALHA, f"banco: {e}")

    try:
        from importar_fluxos import gerar_feriados_csv
        gerar_feriados_csv()
        print(OK, "feriados gerados")
    except Exception as e:
        print(FALHA, f"feriados: {e}")

    try:
        from rotina_diaria import atualizar_cdi
        atualizar_cdi()
        print(OK, "CDI atualizado")
    except Exception as e:
        print(FALHA, f"CDI: {e}")

    try:
        from src.sync_b3_curve import sync_curva_di
        sync_curva_di()
        print(OK, "curva DI B3 atualizada")
    except Exception as e:
        print(FALHA, f"curva B3: {e}")

    # Aponta o add-in para a pasta de fluxos correta
    cfg = Path(os.environ["APPDATA"]) / "Microsoft" / "AddIns" / "rf_fluxos.txt"
    cfg.write_text(str(fluxos), encoding="utf-8")
    print(OK, f"add-in apontando para: {fluxos}")


def importar_ativos():
    passo(5, "Importando ativos da API (DEB, CRI, CRA)")
    cred = INSTALL_DIR / "credenciais.txt"
    if not cred.exists():
        print(PULAR, "credenciais nao encontradas.")
        print(f"  1. Copie e renomeie: credenciais.txt.exemplo -> credenciais.txt")
        print(f"     Pasta: {INSTALL_DIR}")
        print("  2. Preencha login e senha")
        print("  3. Rode de novo: python instalar.py --importar")
        return

    try:
        from importar_todos import main as m
        m(["deb", "cri", "cra"])
        print(OK, "fluxos importados")
    except Exception as e:
        print(FALHA, e)


def main():
    importar = "--importar" in sys.argv
    print("RF_Calc — INSTALADOR")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Destino: {INSTALL_DIR}")

    addin_ok   = instalar_addin()
    projeto_ok = baixar_projeto()

    if not projeto_ok:
        print("\n[!] Nao foi possivel baixar o projeto. Verifique a internet.")
        input("\nPressione Enter para sair...")
        return

    instalar_dependencias()
    configurar_dados()

    if importar:
        importar_ativos()
    else:
        print(f"\n{PULAR} Para importar os fluxos dos ativos, rode:")
        print(f"       python {Path(__file__).name} --importar")

    print("\n" + "="*60)
    print("INSTALACAO CONCLUIDA.")
    if addin_ok:
        print(">> Reabra o Excel — as funcoes RF_* carregam sozinhas.")
    print(">> Teste numa celula: =RF_LISTAR()")
    print(f">> Projeto em: {INSTALL_DIR}")
    print("="*60)
    input("\nPressione Enter para sair...")


if __name__ == "__main__":
    main()
