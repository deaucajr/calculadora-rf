"""
RF_Calc — Instalador completo
Instala o add-in Excel e configura todo o sistema de dados
(feriados, CDI, curva B3, debentures/CRIs/CRAs).

Uso:
  python instalar.py              -- instala tudo (sem importar ativos)
  python instalar.py --importar   -- instala + importa debentures/CRIs/CRAs

Prerequisitos: Python 3.8+, Excel fechado, internet.
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


# ---------- 1. Add-in Excel ----------

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
    origem = (dist / "RF_Calc.xlam.bin"
              if (dist / "RF_Calc.xlam.bin").exists()
              else dist / "RF_Calc.xlam")
    if not origem.exists():
        print(FALHA, f"Arquivo do add-in nao encontrado em: {dist}")
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


# ---------- 2. Baixar projeto ----------

def baixar_projeto():
    passo(2, "Baixando projeto do GitHub")
    print(f"Destino: {INSTALL_DIR}")

    if INSTALL_DIR.exists() and (INSTALL_DIR / "requirements.txt").exists():
        print(OK, "projeto ja instalado, pulando download")
        return True

    print("Baixando... (pode demorar alguns segundos)")
    try:
        tmp_zip = Path(tempfile.mktemp(suffix=".zip"))
        urllib.request.urlretrieve(REPO_ZIP, tmp_zip)
        print(OK, "download concluido")
    except urllib.error.URLError as e:
        print(FALHA, f"Nao foi possivel baixar do GitHub: {e}")
        print("       Verifique a conexao com a internet e tente de novo.")
        return False

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(tmp_zip, "r") as z:
                z.extractall(tmpdir)
            extraido = next(Path(tmpdir).iterdir())  # calculadora-rf-main/
            if INSTALL_DIR.exists():
                shutil.rmtree(INSTALL_DIR)
            shutil.copytree(extraido / "sistema", INSTALL_DIR)
        tmp_zip.unlink(missing_ok=True)
        print(OK, f"projeto instalado em {INSTALL_DIR}")
        return True
    except Exception as e:
        print(FALHA, f"Erro ao extrair: {e}")
        return False


# ---------- 3. Dependencias ----------

def instalar_dependencias():
    passo(3, "Instalando dependencias Python (pip)")
    req = INSTALL_DIR / "requirements.txt"
    if not req.exists():
        print(FALHA, "requirements.txt nao encontrado")
        return False
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req)],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        print(OK, "dependencias instaladas")
        return True
    print(FALHA, "pip retornou erro:\n", r.stderr[-600:])
    return False


# ---------- 4. Caminho dos dados ----------

def configurar_caminho_dados():
    passo(4, "Configurando caminho da pasta de dados")
    addins = Path(os.environ["APPDATA"]) / "Microsoft" / "AddIns"
    cfg = addins / "rf_fluxos.txt"

    if cfg.exists():
        dados = cfg.read_text(encoding="utf-8").strip().splitlines()[0]
        print(OK, f"caminho ja configurado: {dados}")
        return dados

    dados_default = str(INSTALL_DIR / "data" / "fluxos")
    print(f"Pasta sugerida para os dados: {dados_default}")
    resp = input("Pressione Enter para aceitar ou cole outro caminho: ").strip().strip('"')
    dados = resp if resp else dados_default

    Path(dados).mkdir(parents=True, exist_ok=True)
    addins.mkdir(parents=True, exist_ok=True)
    cfg.write_text(dados, encoding="utf-8")
    print(OK, f"caminho configurado: {dados}")

    # Pastas irmas
    try:
        pai = Path(dados).parent
        for sub in ("fluxos_manual", "fluxos_antigo"):
            (pai / sub).mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    return dados


# ---------- 5. Banco + dados publicos ----------

def configurar_sistema(fluxos_dir):
    passo(5, "Criando banco de dados e baixando dados publicos")

    Path(fluxos_dir).mkdir(parents=True, exist_ok=True)
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
        print(OK, "curva B3 atualizada")
    except Exception as e:
        print(FALHA, f"curva B3: {e}")


# ---------- 6. Debentures / CRIs / CRAs ----------

def importar_debentures():
    passo(6, "Importando debentures/CRIs/CRAs da API")

    cred = INSTALL_DIR / "credenciais.txt"
    exemplo = INSTALL_DIR / "credenciais.txt.exemplo"

    if not cred.exists():
        print(PULAR, "sem credenciais da API.")
        if exemplo.exists():
            print(f"  1) Abra e renomeie: {exemplo}")
            print(f"     -> {cred}")
            print("  2) Preencha login e senha")
            print("  3) Rode de novo: python instalar.py --importar")
        else:
            print(f"  Crie o arquivo {cred} com login e senha da API.")
        return

    try:
        sys.path.insert(0, str(INSTALL_DIR))
        sys.path.insert(0, str(INSTALL_DIR / "scripts"))
        from importar_todos import main as importar_main
        importar_main(["deb", "cri", "cra"])
        print(OK, "ativos importados")
    except Exception as e:
        print(FALHA, e)


# ---------- main ----------

def main():
    importar = "--importar" in sys.argv
    print("RF_Calc — INSTALADOR COMPLETO")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Instalando em: {INSTALL_DIR}")

    addin_ok   = instalar_addin()
    projeto_ok = baixar_projeto()

    if not projeto_ok:
        print("\n[ATENCAO] Nao foi possivel baixar o projeto.")
        print("          Verifique a internet e tente de novo.")
        input("\nPressione Enter para sair...")
        return

    instalar_dependencias()
    fluxos_dir = configurar_caminho_dados()
    configurar_sistema(fluxos_dir)

    if importar:
        importar_debentures()
    else:
        print(f"\n{PULAR} Importacao de ativos nao solicitada.")
        print("       Para importar debentures/CRIs/CRAs, rode:")
        print(f"         python {Path(__file__).name} --importar")

    print("\n" + "="*60)
    print("INSTALACAO CONCLUIDA.")
    if addin_ok:
        print(">> Reabra o Excel: as funcoes RF_* carregam sozinhas.")
    print(">> Teste numa celula: =RF_LISTAR()")
    print(f">> Projeto instalado em: {INSTALL_DIR}")
    print("="*60)
    input("\nPressione Enter para sair...")


if __name__ == "__main__":
    main()
