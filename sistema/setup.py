#!/usr/bin/env python
"""
SETUP UNICO — prepara o RF_Calc do zero apos clonar o repositorio.

Rode (Windows, Excel FECHADO):

    cd sistema
    python setup.py

ou de duplo-clique em  setup.py

O que faz, em ordem (cada passo e idempotente; pode rodar de novo):
  1. Instala as dependencias (requirements.txt).
  2. Cria o banco local rf.db (esquema).
  3. Gera o calendario de feriados  -> data/fluxos/_feriados.csv   (offline)
  4. Baixa o CDI diario do BACEN     -> data/fluxos/_cdi.csv        (publico)
  5. Baixa a curva DI x Pre da B3    -> data/fluxos/_curva_di.csv   (publico)
  6. Constroi/instala o add-in RF_Calc.xlam (liga AccessVBOM temporariamente).
  7. Se existir config.json com credenciais -> importa os fluxos dos ativos.
     (sem config.json o add-in ja funciona; faltam so os CSV de cada ativo.)

Depois: reabra o Excel — as funcoes RF_* carregam sozinhas.
"""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent          # .../sistema
sys.path.insert(0, str(BASE))                   # p/ importar src e scripts
sys.path.insert(0, str(BASE / "scripts"))

OK, FALHA, PULAR = "[ OK ]", "[FALHA]", "[PULAR]"


def passo(n, titulo):
    print(f"\n{'='*60}\n{n}. {titulo}\n{'='*60}")


def instalar_dependencias():
    passo(1, "Instalando dependencias (requirements.txt)")
    req = BASE / "requirements.txt"
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(OK, "dependencias instaladas")
    else:
        print(FALHA, "pip retornou erro:\n", r.stdout[-800:], r.stderr[-800:])
    return r.returncode == 0


def criar_banco():
    passo(2, "Criando banco local rf.db")
    try:
        from src.db import init_db
        init_db()
        print(OK, "esquema do rf.db criado")
        return True
    except Exception as e:
        print(FALHA, e)
        return False


def gerar_feriados():
    passo(3, "Gerando calendario de feriados (offline)")
    try:
        from importar_fluxos import gerar_feriados_csv
        gerar_feriados_csv()
        print(OK, "_feriados.csv gerado")
        return True
    except Exception as e:
        print(FALHA, e)
        return False


def baixar_cdi():
    passo(4, "Baixando CDI diario do BACEN (publico)")
    try:
        from rotina_diaria import atualizar_cdi
        atualizar_cdi()
        print(OK, "_cdi.csv atualizado")
        return True
    except Exception as e:
        print(FALHA, e)
        return False


def baixar_curva():
    passo(5, "Baixando curva DI x Pre da B3 (publico)")
    try:
        from src.sync_b3_curve import sync_curva_di
        sync_curva_di()
        print(OK, "_curva_di.csv atualizado")
        return True
    except Exception as e:
        print(FALHA, e)
        return False


def construir_addin():
    passo(6, "Construindo o add-in RF_Calc.xlam")
    # Excel precisa estar fechado
    try:
        saida = subprocess.run(["tasklist", "/FI", "IMAGENAME eq EXCEL.EXE"],
                               capture_output=True, text=True).stdout.upper()
        if "EXCEL.EXE" in saida:
            print(FALHA, "o Excel esta ABERTO — feche-o e rode o setup de novo.")
            return False
    except Exception:
        pass
    # liga AccessVBOM temporariamente, builda, reverte
    import winreg
    sec = r"Software\Microsoft\Office\16.0\Excel\Security"
    anterior = None
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, sec)
        try:
            anterior, _ = winreg.QueryValueEx(key, "AccessVBOM")
        except FileNotFoundError:
            anterior = 0
        winreg.SetValueEx(key, "AccessVBOM", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)

        from addin import build_xlam
        rc = build_xlam.main()
    except Exception as e:
        print(FALHA, e)
        rc = 99
    finally:
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, sec)
            winreg.SetValueEx(key, "AccessVBOM", 0, winreg.REG_DWORD, int(anterior or 0))
            winreg.CloseKey(key)
        except Exception:
            pass
    if rc == 0:
        print(OK, "RF_Calc.xlam gerado e auto-load registrado")
        return True
    if rc == 2:
        print(FALHA, "habilite 'Confiar no acesso ao modelo de objeto do VBA' e tente de novo.")
    return False


def _tem_credenciais():
    """True se ha login/senha (via credenciais.txt ou config.json)."""
    try:
        from src.api_client import load_config
        api = load_config().get("api", {})
        login = str(api.get("login", ""))
        return bool(login) and "SEU_LOGIN" not in login
    except Exception:
        return False


def importar_fluxos_ativos(importar):
    passo(7, "Fluxos dos ativos (API calculadorarendafixa)")
    if not importar:
        print(PULAR, "import de ativos nao solicitado (evita carga na API).")
        print("       Os dados publicos (feriados, CDI, curva B3) ja bastam para o add-in.")
        print("       Para baixar os fluxos de cada ativo, rode UMA vez:")
        print("         python setup.py --importar      (ou: python scripts/importar_todos.py)")
        return None
    if not _tem_credenciais():
        print(PULAR, "sem credenciais da CALC.")
        print("       1) renomeie  credenciais.txt.exemplo  ->  credenciais.txt")
        print("       2) preencha login e senha nesse arquivo (fica fora do git)")
        print("       3) rode de novo:  python setup.py --importar")
        return None
    try:
        from importar_todos import main as importar_main
        importar_main(["deb", "cri", "cra"])
        print(OK, "fluxos dos ativos importados")
        return True
    except Exception as e:
        print(FALHA, e)
        return False


def main():
    importar = "--importar" in sys.argv
    print("RF_Calc — SETUP UNICO" + ("  (com import de ativos)" if importar else ""))
    print("Pasta:", BASE)
    (BASE / "data" / "fluxos").mkdir(parents=True, exist_ok=True)  # clone limpo
    instalar_dependencias()
    criar_banco()
    gerar_feriados()
    baixar_cdi()
    baixar_curva()
    addin_ok = construir_addin()
    importar_fluxos_ativos(importar)

    print("\n" + "=" * 60)
    print("SETUP CONCLUIDO.")
    if addin_ok:
        print(">> Reabra o Excel: as funcoes RF_* carregam sozinhas.")
    print("   Dados publicos (feriados, CDI, curva B3) ja estao na pasta de fluxos.")
    print("   Conferir se voce tem todo o universo da B3 no PC:")
    print("     python scripts/verificar_cadastro.py            (relata o que falta)")
    print("     python scripts/verificar_cadastro.py --baixar   (baixa os que faltam)")
    print("   Atualizar tudo no dia a dia:  python scripts/rotina_diaria.py")
    print("=" * 60)
    input("\nPressione Enter para sair...")


if __name__ == "__main__":
    main()
