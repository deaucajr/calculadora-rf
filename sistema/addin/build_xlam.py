#!/usr/bin/env python
"""
Gera RF_Calc.xlam LIMPO a partir de RF_Calc.bas (sem modulo duplicado) e
registra o auto-load no Excel. Requer Excel fechado e "Confiar no acesso ao
modelo de objeto de projeto do VBA" habilitado (temporario).

Uso: python excel/build_xlam.py
"""
import os
import sys
import time
import winreg
from pathlib import Path

import win32com.client as win32

BASE = Path(__file__).resolve().parent
BAS = BASE / "RF_Calc.bas"
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
        vbproj.VBComponents.Import(str(BAS))

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

    registrar_autoload()
    print("Pronto. Reabra o Excel: o add-in carrega sozinho (funcoes RF_*).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
