# =====================================================================
#  Instalador do add-in RF_Calc (Excel) — NAO precisa de Python.
#  Copia o .xlam, registra o auto-load e aponta para a pasta de dados
#  (rede UNC ou OneDrive). Rode pelo instalar.bat (duplo-clique).
# =====================================================================
$ErrorActionPreference = "Stop"
$dist = Split-Path -Parent $MyInvocation.MyCommand.Path

function Versao-Excel {
    foreach ($v in "16.0", "15.0", "14.0") {
        if (Test-Path "HKCU:\Software\Microsoft\Office\$v\Excel") { return $v }
    }
    return "16.0"
}

Write-Host "=== Instalando RF_Calc ===" -ForegroundColor Cyan

# --- 1) Excel precisa estar fechado (o .xlam fica em uso) ---
if (Get-Process EXCEL -ErrorAction SilentlyContinue) {
    Write-Host "Feche o Excel e rode de novo." -ForegroundColor Yellow
    return
}

# --- 2) copia o add-in para a pasta de AddIns do usuario ---
$addins = Join-Path $env:APPDATA "Microsoft\AddIns"
New-Item -ItemType Directory -Force -Path $addins | Out-Null
Copy-Item (Join-Path $dist "RF_Calc.xlam") (Join-Path $addins "RF_Calc.xlam") -Force
Write-Host "[ok] add-in copiado para $addins"

# --- 3) registra o auto-load (Excel carrega o add-in ao abrir) ---
$ver = Versao-Excel
$key = "HKCU:\Software\Microsoft\Office\$ver\Excel\Options"
New-Item -Path $key -Force | Out-Null
Set-ItemProperty -Path $key -Name "OPEN" -Value '/R "RF_Calc.xlam"'
Write-Host "[ok] auto-load registrado (Office $ver)"

# --- 4) descobre a pasta de dados (rf_fluxos_dir.txt ou pergunta) ---
$dados = ""
$pathFile = Join-Path $dist "rf_fluxos_dir.txt"
if (Test-Path $pathFile) {
    $dados = (Get-Content $pathFile -Encoding UTF8 |
              Where-Object { $_ -and ($_ -notmatch '^\s*#') } |
              Select-Object -First 1)
    if ($dados) { $dados = $dados.Trim() }
}
if (-not $dados) {
    Write-Host ""
    Write-Host "Cole o caminho da pasta de fluxos (onde estao os .csv)."
    Write-Host "  Ex. rede:     \\servidor\rendafixa\fluxos"
    Write-Host "  Ex. OneDrive: C:\Users\voce\OneDrive - Empresa\RendaFixa\fluxos"
    $dados = (Read-Host "Caminho").Trim('"').Trim()
}

# --- 5) grava a config que o add-in le em runtime ---
$cfg = Join-Path $addins "rf_fluxos.txt"
Set-Content -Path $cfg -Value $dados -Encoding UTF8
Write-Host "[ok] caminho dos dados: $dados"

# --- 6) valida e, se for OneDrive, fixa os arquivos (sempre offline) ---
if (Test-Path $dados) {
    if ($dados -match "OneDrive") {
        Write-Host "OneDrive detectado: fixando arquivos p/ ficarem sempre disponiveis offline..."
        & attrib +P /S /D "$dados\*" 2>$null
        Write-Host "[ok] arquivos fixados (pode levar uns minutos p/ o OneDrive baixar tudo)"
    }
} else {
    Write-Host "[ATENCAO] a pasta nao foi encontrada agora: $dados" -ForegroundColor Yellow
    Write-Host "          Verifique a rede/VPN/permissao. O add-in funcionara quando ela estiver acessivel."
}

Write-Host ""
Write-Host "PRONTO. Feche e abra o Excel: as funcoes RF_* carregam sozinhas." -ForegroundColor Green
Write-Host "Teste numa celula:  =RF_LISTAR()"
