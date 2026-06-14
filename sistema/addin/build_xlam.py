#!/usr/bin/env python
"""
Gera RF_Calc.xlam LIMPO a partir de RF_Calc.bas (sem modulo duplicado) e
registra o auto-load no Excel. Requer Excel fechado e "Confiar no acesso ao
modelo de objeto de projeto do VBA" habilitado (temporario).

Uso: python excel/build_xlam.py
"""
import os
import re
import sys
import time
import winreg
from pathlib import Path

import win32com.client as win32

BASE = Path(__file__).resolve().parent
BAS = BASE / "RF_Calc.bas"
sys.path.insert(0, str(BASE.parent))           # p/ importar src.paths
# pasta dos CSV de fluxo desta maquina (config 'fluxos_dir' ou data/fluxos), c/ barra final
try:
    from src.paths import fluxos_dir
    FLUXOS_DIR_LOCAL = str(fluxos_dir()) + os.sep
except Exception:
    FLUXOS_DIR_LOCAL = str(BASE.parent / "data" / "fluxos") + os.sep


def _bas_com_caminho_local() -> Path:
    """Grava um .bas temporario com a const FLUXOS_DIR apontando p/ a pasta local
    desta maquina. Torna o add-in portavel apos clonar de outra origem."""
    txt = BAS.read_text(encoding="utf-8", errors="replace")
    novo = re.sub(
        r'(Private Const FLUXOS_DIR As String = _\s*\r?\n\s*")[^"]*(")',
        lambda m: m.group(1) + FLUXOS_DIR_LOCAL + m.group(2),
        txt, count=1)
    tmp = BASE / "_RF_Calc_build.bas"
    tmp.write_text(novo, encoding="utf-8")
    return tmp
XLAM = Path(os.environ["APPDATA"]) / "Microsoft" / "AddIns" / "RF_Calc.xlam"
OLD_XLAM = Path(os.environ["APPDATA"]) / "Microsoft" / "AddIns" / "DEB_Calc.xlam"
MODULE_NAME = "RF_Calc"
XL_OPENXML_ADDIN = 55  # .xlam (NAO usar 18 = .xla antigo)


def registrar_autoload():
    """Aponta a chave OPEN do Excel para o RF_Calc.xlam (auto-carrega ao abrir)."""
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Office\16.0\Excel\Options")
    winreg.SetValueEx(key, "OPEN", 0, winreg.REG_SZ, f'/R "{XLAM.name}"')
    winreg.CloseKey(key)
    print('Auto-load registrado: OPEN = /R "RF_Calc.xlam"')


def main():
    if not BAS.exists():
        print(f"ERRO: nao achei {BAS}")
        return 1
    for old in (XLAM, OLD_XLAM):
        if old.exists():
            try:
                old.unlink()
                print(f"Removido: {old.name}")
            except PermissionError:
                print(f"ERRO: feche o Excel ({old.name} em uso) e rode de novo.")
                return 1

    excel = win32.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        wb = excel.Workbooks.Add()
        try:
            vbproj = wb.VBProject
        except Exception:
            print("\nERRO: 'Confiar no acesso ao modelo de objeto de projeto do VBA' "
                  "esta DESABILITADO. Habilite e rode de novo.")
            wb.Close(SaveChanges=False)
            return 2

        for comp in list(vbproj.VBComponents):
            if comp.Name == MODULE_NAME:
                vbproj.VBComponents.Remove(comp)
        bas_local = _bas_com_caminho_local()
        try:
            vbproj.VBComponents.Import(str(bas_local))
            print(f"FLUXOS_DIR ajustado p/ {FLUXOS_DIR_LOCAL}")
        finally:
            bas_local.unlink(missing_ok=True)

        # Title/descricao do add-in (evita entrada "sem titulo" no dialogo)
        try:
            wb.Title = "Calculadora Renda Fixa (RF_Calc)"
            wb.BuiltinDocumentProperties("Title").Value = "Calculadora Renda Fixa (RF_Calc)"
            wb.BuiltinDocumentProperties("Comments").Value = "Funcoes RF_* para precificar renda fixa"
        except Exception:
            pass

        wb.IsAddin = True
        wb.SaveAs(str(XLAM), FileFormat=XL_OPENXML_ADDIN)
        wb.Close(SaveChanges=False)
        print(f"OK: gerado {XLAM}")
    finally:
        excel.Quit()
        time.sleep(1)

    # copia distribuivel p/ sistema/dist (commitado p/ os colegas instalarem)
    try:
        import shutil
        dist = BASE.parent / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        shutil.copy2(XLAM, dist / "RF_Calc.xlam")
        print(f"OK: copia distribuivel em {dist / 'RF_Calc.xlam'}")
    except Exception as e:
        print(f"(aviso) nao copiei p/ dist: {e}")

    registrar_autoload()
    print("Pronto. Reabra o Excel: o add-in carrega sozinho (funcoes RF_*).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
