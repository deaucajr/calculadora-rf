Attribute VB_Name = "RF_Calc"
' ============================================================
'  CALCULADORA DE RENDA FIXA  -  ADD-IN (RF_Calc)
'  Precifica debentures, CRIs, CRAs (IPCA, PRE, CDI, %CDI).
'  Le os dados de fluxos\<TICKER>.csv SOB DEMANDA (lazy load):
'  abertura instantanea e leve mesmo com milhares de ativos.
'
'  MODELO (IPCA/PRE):
'    PU(data,taxa) = [ Soma FC_i% / (1+taxa/100)^(du_i/252) ] * VNA(data)
'    FC% e' data-independente; VNA(data) vem dos pontos no CSV (interpola).
'  CDI/%CDI: exato na DATA_FLUXO do CSV (desconto DI embutido no PV).
'
'  FUNCOES (taxa em % a.a.; data obrigatoria):
'    RF_PU(ticker,taxa,data)  RF_TAXA(ticker,pu,data)  RF_DURATION(ticker,taxa,data)
'    RF_DV01(ticker,taxa,data) RF_CONVEXIDADE(ticker,taxa,data)
'    RF_VNA(ticker,data)      RF_FLUXO(ticker,taxa,data)
'    RF_VENCIMENTO(ticker)    RF_ATUALIZADO_EM(ticker)  RF_PROXIMO_EVENTO(ticker,data)
'    RF_SPREAD(ticker)        RF_INFO(ticker,campo)     RF_LISTAR()
'  MACROS (Alt+F8): RF_ATUALIZAR (limpa cache)   RF_EXPORTAR (planilha p/ enviar)
' ============================================================
Option Explicit

' >>> pasta dos CSV de fluxo: DEFAULT (fallback). O caminho real e resolvido em
'     runtime por FluxosDir() -> variavel de ambiente RF_FLUXOS_DIR, ou o arquivo
'     %APPDATA%\Microsoft\AddIns\rf_fluxos.txt (escrito pelo instalador), ou este. <<<
Private Const FLUXOS_DIR As String = _
    "C:\Users\Nitro 5\OneDrive\Documentos\Claude_code\Projeto_calculadora_excel\Codigo_Fluxo\sistema\data\fluxos\"
Private Const SEP As String = vbTab

Private gAtivos As Object   ' ticker -> Array(hdr, flows2D, vDates, vVals, cdi)  (cache lazy)
Private gFeriados As Object ' CLng(date) -> True
Private gCdi As Object      ' data_iso -> CDI diario (fracao); p/ DI-PERC (% do CDI)
Private gCurva As Object    ' data_iso -> curva DI B3 2D(n,2): [du, taxa_aa]  (_curva_di.csv)
Private gCfCache As Object  ' "ticker|data_iso" -> bloco sintetico CDI (cache; independe da taxa)
Private gFluxosDir As String ' caminho resolvido em runtime (cache da sessao)

' ================= INFRA / LAZY =================

Public Sub Auto_Open()
    On Error Resume Next
    RegistrarFuncoes        ' so registra dicas; nao carrega dados (leve)
End Sub

Public Sub RF_ATUALIZAR()
    Set gAtivos = Nothing
    Set gFeriados = Nothing
    Set gCdi = Nothing
    Set gCurva = Nothing
    Set gCfCache = Nothing
    gFluxosDir = ""
    RegistrarFuncoes
    MsgBox "Cache limpo. Os ativos serao recarregados sob demanda de:" & vbCrLf & FluxosDir(), _
           vbInformation, "RF Calc"
End Sub

' Pasta dos CSV resolvida em RUNTIME (nao depende do build), nesta ordem:
'   1) variavel de ambiente RF_FLUXOS_DIR
'   2) arquivo %APPDATA%\Microsoft\AddIns\rf_fluxos.txt (1a linha util = caminho)
'   3) default embutido (FLUXOS_DIR)
' Assim o MESMO .xlam funciona em qualquer maquina (rede UNC, OneDrive, local).
Private Function FluxosDir() As String
    If gFluxosDir <> "" Then FluxosDir = gFluxosDir: Exit Function
    Dim p As String
    On Error Resume Next
    p = Environ$("RF_FLUXOS_DIR")
    On Error GoTo 0
    If Trim(p) = "" Then p = LerConfigCaminho()
    If Trim(p) = "" Then p = FLUXOS_DIR
    p = Trim(p)
    If p <> "" And Right$(p, 1) <> "\" And Right$(p, 1) <> "/" Then p = p & "\"
    gFluxosDir = p
    FluxosDir = p
End Function

' Le o caminho de %APPDATA%\Microsoft\AddIns\rf_fluxos.txt (1a linha nao vazia
' e que nao comece com #). "" se nao existir.
Private Function LerConfigCaminho() As String
    Dim cfg As String, fnum As Integer, linha As String
    cfg = Environ$("APPDATA") & "\Microsoft\AddIns\rf_fluxos.txt"
    On Error GoTo Fim
    If Dir(cfg) = "" Then Exit Function
    fnum = FreeFile
    Open cfg For Input As #fnum
    Do While Not EOF(fnum)
        Line Input #fnum, linha
        linha = Trim(linha)
        If linha <> "" And Left$(linha, 1) <> "#" Then
            LerConfigCaminho = linha
            Exit Do
        End If
    Loop
Fim:
    On Error Resume Next
    Close #fnum
End Function

Private Sub GaranteFeriados()
    If Not gFeriados Is Nothing Then Exit Sub
    Set gFeriados = CreateObject("Scripting.Dictionary")
    Dim fnum As Integer, linha As String, d As Date
    On Error GoTo Fim
    fnum = FreeFile
    Open FluxosDir() & "_feriados.csv" For Input As #fnum
    Do While Not EOF(fnum)
        Line Input #fnum, linha
        linha = Trim(linha)
        If linha <> "" Then
            d = ParseISO(linha)
            If d > 0 Then gFeriados(CLng(d)) = True
        End If
    Loop
Fim:
    On Error Resume Next
    Close #fnum
End Sub

Private Sub GaranteCdi()
    If Not gCdi Is Nothing Then Exit Sub
    Set gCdi = CreateObject("Scripting.Dictionary")
    Dim fnum As Integer, linha As String, p() As String
    On Error GoTo Fim
    fnum = FreeFile
    Open FluxosDir() & "_cdi.csv" For Input As #fnum
    Do While Not EOF(fnum)
        Line Input #fnum, linha
        p = Split(linha, SEP)
        If UBound(p) >= 1 Then gCdi(p(0)) = Val(p(1))
    Loop
Fim:
    On Error Resume Next
    Close #fnum
End Sub

' CDI diario (fracao) da data, ou o ultimo disponivel antes dela.
Private Function CdiDia(d As Date) As Double
    GaranteCdi
    Dim di As String: di = IsoStr(d)
    If gCdi.Exists(di) Then CdiDia = gCdi(di): Exit Function
    Dim best As String, k As Variant
    For Each k In gCdi.Keys
        If k <= di And k > best Then best = CStr(k)
    Next k
    If best <> "" Then CdiDia = gCdi(best)
End Function

' Le fluxos\<TICKER>.csv para o cache. Retorna True se carregou.
' Cache: gAtivos(tk) = Array(hdr, fl2(IPCA/PRE), vd2, vv2, cdi)
'   cdi = Dictionary data_iso -> fluxos2D(n,4): [dataEvento, vf, pv, du]  (so p/ CDI)
Private Function CarregarAtivo(ticker As String) As Boolean
    Dim tk As String: tk = UCase(Trim(ticker))
    Dim caminho As String: caminho = FluxosDir() & tk & ".csv"
    If Dir(caminho) = "" Then Exit Function

    Dim hdr As Object: Set hdr = CreateObject("Scripting.Dictionary")
    Dim fl() As Variant, nf As Long: ReDim fl(1 To 1000, 1 To 6)
    Dim vd() As Double, vv() As Double, nv As Long
    ReDim vd(1 To 500): ReDim vv(1 To 500)
    Dim cdiTmp As Object: Set cdiTmp = CreateObject("Scripting.Dictionary")  ' data -> Collection

    Dim fnum As Integer, linha As String, p() As String
    On Error GoTo Falha
    fnum = FreeFile
    Open caminho For Input As #fnum
    Do While Not EOF(fnum)
        Line Input #fnum, linha
        If linha = "" Then GoTo Prox
        p = Split(linha, SEP)
        Select Case p(0)
            Case "META"
                If UBound(p) >= 2 Then hdr(UCase(Trim(p(1)))) = p(2)
            Case "FLUXO"
                If UBound(p) >= 6 Then
                    nf = nf + 1
                    fl(nf, 1) = ParseISO(p(1)): fl(nf, 2) = p(2)
                    fl(nf, 3) = Val(p(3)): fl(nf, 4) = Val(p(4))
                    fl(nf, 5) = CLng(Val(p(5))): fl(nf, 6) = Val(p(6))
                End If
            Case "VNA"
                If UBound(p) >= 2 Then
                    nv = nv + 1
                    vd(nv) = CDbl(ParseISO(p(1))): vv(nv) = Val(p(2))
                End If
            Case "FLUXOD"   ' CDI: data_calc, data_evento, evento, vf, pv, du
                If UBound(p) >= 6 Then
                    If Not cdiTmp.Exists(p(1)) Then cdiTmp.Add p(1), New Collection
                    cdiTmp(p(1)).Add Array(ParseISO(p(2)), Val(p(4)), Val(p(5)), CLng(Val(p(6))))
                End If
        End Select
Prox:
    Loop
    Close #fnum

    Dim i As Long, j As Long
    Dim fl2() As Variant
    If nf >= 1 Then
        ReDim fl2(1 To nf, 1 To 6)
        For i = 1 To nf
            For j = 1 To 6
                fl2(i, j) = fl(i, j)
            Next j
        Next i
    End If

    Dim vd2() As Double, vv2() As Double
    If nv >= 1 Then
        ReDim vd2(1 To nv): ReDim vv2(1 To nv)
        For i = 1 To nv
            vd2(i) = vd(i): vv2(i) = vv(i)
        Next i
        OrdenaVNA vd2, vv2
    End If

    ' Converte cdiTmp (Collections) -> cdi (Dictionary de arrays 2D)
    Dim cdi As Object: Set cdi = Nothing
    If cdiTmp.Count > 0 Then
        Set cdi = CreateObject("Scripting.Dictionary")
        Dim dkey As Variant, col As Collection, m As Long, arr() As Variant, it As Variant
        For Each dkey In cdiTmp.Keys
            Set col = cdiTmp(dkey)
            m = col.Count
            ReDim arr(1 To m, 1 To 4)
            For i = 1 To m
                it = col(i)
                arr(i, 1) = it(0): arr(i, 2) = it(1): arr(i, 3) = it(2): arr(i, 4) = it(3)
            Next i
            cdi(CStr(dkey)) = arr
        Next dkey
    End If

    If nf < 1 And cdi Is Nothing Then Exit Function
    If gAtivos Is Nothing Then Set gAtivos = CreateObject("Scripting.Dictionary")
    gAtivos(tk) = Array(hdr, fl2, vd2, vv2, cdi)
    CarregarAtivo = True
    Exit Function
Falha:
    On Error Resume Next
    Close #fnum
End Function

' "YYYY-MM-DD" a partir de uma Date (chave dos blocos CDI)
Private Function IsoStr(d As Date) As String
    IsoStr = Format(d, "YYYY-MM-DD")
End Function

' Escolhe a melhor data de bloco CDI para dCalc: a data exata se existir;
' senao a mais recente <= dCalc; senao (dCalc anterior a tudo) a mais antiga.
' Retorna "" se nao ha blocos. As chaves "YYYY-MM-DD" ordenam cronologicamente.
Private Function MelhorChaveCdi(cdi As Object, dCalc As Date) As String
    If cdi Is Nothing Then Exit Function
    Dim alvo As String: alvo = IsoStr(dCalc)
    If cdi.Exists(alvo) Then MelhorChaveCdi = alvo: Exit Function
    Dim k As Variant, best As String, menor As String
    For Each k In cdi.Keys
        If CStr(k) <= alvo Then
            If best = "" Or CStr(k) > best Then best = CStr(k)
        End If
        If menor = "" Or CStr(k) < menor Then menor = CStr(k)
    Next k
    If best <> "" Then MelhorChaveCdi = best Else MelhorChaveCdi = menor
End Function

' ============== CURVA DI x PRE (B3) — repricing de CDI em qualquer data ==============

' Carrega _curva_di.csv -> gCurva(data_iso) = 2D(n,2): [du, taxa_aa], ordenado por du.
Private Sub GaranteCurva()
    If Not gCurva Is Nothing Then Exit Sub
    Set gCurva = CreateObject("Scripting.Dictionary")
    Dim tmp As Object: Set tmp = CreateObject("Scripting.Dictionary")  ' data -> Collection(Array(du,taxa))
    Dim fnum As Integer, linha As String, p() As String
    On Error GoTo Fim
    fnum = FreeFile
    Open FluxosDir() & "_curva_di.csv" For Input As #fnum
    Do While Not EOF(fnum)
        Line Input #fnum, linha
        p = Split(linha, SEP)
        If UBound(p) >= 2 Then
            If Not tmp.Exists(p(0)) Then tmp.Add p(0), New Collection
            tmp(p(0)).Add Array(CLng(Val(p(1))), Val(p(2)))
        End If
    Loop
    Close #fnum
    Dim k As Variant, col As Collection, i As Long, arr() As Variant, it As Variant
    For Each k In tmp.Keys
        Set col = tmp(k)
        ReDim arr(1 To col.Count, 1 To 2)
        For i = 1 To col.Count
            it = col(i): arr(i, 1) = it(0): arr(i, 2) = it(1)
        Next i
        gCurva(CStr(k)) = arr   ' _curva_di.csv ja vem ordenado por du
    Next k
    Exit Sub
Fim:
    On Error Resume Next
    Close #fnum
End Sub

' Fator DI (crescimento, 100% CDI) ate du=x; interp log-linear no fator de desconto.
Private Function FdDi(curva As Variant, x As Double) As Double
    Dim n As Long: n = UBound(curva, 1)
    If x <= curva(1, 1) Then FdDi = (1 + curva(1, 2) / 100) ^ (x / 252#): Exit Function
    If x >= curva(n, 1) Then FdDi = (1 + curva(n, 2) / 100) ^ (x / 252#): Exit Function
    Dim lo As Long, hi As Long, mid As Long
    lo = 1: hi = n
    Do While hi - lo > 1                      ' busca binaria do segmento
        mid = (lo + hi) \ 2
        If curva(mid, 1) <= x Then lo = mid Else hi = mid
    Loop
    Dim a As Double, b As Double, fa As Double, fb As Double
    a = curva(lo, 1): b = curva(hi, 1)
    If a = x Then FdDi = (1 + curva(lo, 2) / 100) ^ (x / 252#): Exit Function
    If b = x Then FdDi = (1 + curva(hi, 2) / 100) ^ (x / 252#): Exit Function
    fa = (1 + curva(lo, 2) / 100) ^ (a / 252#)
    fb = (1 + curva(hi, 2) / 100) ^ (b / 252#)
    FdDi = fa * (fb / fa) ^ ((x - a) / (b - a))
End Function

' Fator a pct% do CDI ate du=x: reconstroi CDI forward da curva e reaplica pct.
Private Function FdPct(curva As Variant, x As Double, pct As Double) As Double
    If x <= 0 Then FdPct = 1: Exit Function
    Dim n As Long: n = UBound(curva, 1)
    Dim fd As Double: fd = 1
    Dim prev As Long: prev = 0
    Dim lnPrev As Double: lnPrev = 0
    Dim i As Long, v As Long, lnV As Double, dseg As Long, cdid As Double
    For i = 1 To n
        v = curva(i, 1)
        If v >= x Then Exit For
        lnV = Log(FdDi(curva, CDbl(v)))
        dseg = v - prev
        If dseg > 0 Then
            cdid = Exp((lnV - lnPrev) / dseg) - 1
            fd = fd * (1 + pct / 100 * cdid) ^ dseg
            prev = v: lnPrev = lnV
        End If
    Next i
    Dim lnX As Double: lnX = Log(FdDi(curva, x))
    Dim ds As Long: ds = CLng(x) - prev
    If ds > 0 Then
        cdid = Exp((lnX - lnPrev) / ds) - 1
        fd = fd * (1 + pct / 100 * cdid) ^ ds
    End If
    FdPct = fd
End Function

' Constroi bloco sintetico de fluxos CDI na data dCalc, ancorado no bloco de D0
' (DATA_FLUXO, ja validado) e movido pela curva da B3. Mesma forma de cf0(i,1..4).
' d0 = data-ancora (DATA_FLUXO do bloco cf0). O du de cada evento na data dCalc e
' obtido do du gravado +/- o delta de dias uteis entre dCalc e d0 (convenção do
' bloco), evitando divergencia de contagem absoluta. Em dCalc=d0 -> duD=du0 (exato).
Private Function BlocoSintetico(cf0 As Variant, y0 As Double, dCalc As Date, d0 As Date, _
                                curva0 As Variant, curvaD As Variant) As Variant
    Dim n As Long: n = UBound(cf0, 1)
    Dim tmp() As Variant: ReDim tmp(1 To n, 1 To 4)
    Dim cnt As Long: cnt = 0
    Dim desloc As Long                       ' du a somar ao du0 (>0 se dCalc antes de d0)
    If dCalc >= d0 Then desloc = -ContaDU(d0, dCalc) Else desloc = ContaDU(dCalc, d0)
    Dim i As Long, ev As Date, du0 As Long, duD As Long, rv As Double, rp As Double, r As Double
    For i = 1 To n
        ev = CDate(cf0(i, 1))
        du0 = cf0(i, 4)
        duD = du0 + desloc
        If duD > 0 Then
            cnt = cnt + 1
            tmp(cnt, 1) = ev: tmp(cnt, 4) = duD
            If y0 >= 50 Then                                   ' DI-PERC (% do CDI)
                rv = FdDi(curvaD, CDbl(duD)) / FdDi(curva0, CDbl(du0))
                rp = FdPct(curvaD, CDbl(duD), y0) / FdPct(curva0, CDbl(du0), y0)
                tmp(cnt, 2) = cf0(i, 2) * rv
                tmp(cnt, 3) = cf0(i, 3) * rp
            Else                                               ' DI-SPREAD (CDI+)
                r = (FdDi(curva0, CDbl(du0)) / FdDi(curvaD, CDbl(duD))) _
                    * (1 + y0 / 100) ^ ((du0 - duD) / 252#)
                tmp(cnt, 2) = cf0(i, 2)
                tmp(cnt, 3) = cf0(i, 3) * r
            End If
        End If
    Next i
    If cnt = 0 Then Exit Function
    Dim outc() As Variant: ReDim outc(1 To cnt, 1 To 4)
    Dim j As Long
    For i = 1 To cnt
        For j = 1 To 4
            outc(i, j) = tmp(i, j)
        Next j
    Next i
    OrdenaCf outc                                              ' garante ordem por du
    BlocoSintetico = outc
End Function

Private Sub OrdenaCf(ByRef cf As Variant)
    Dim i As Long, j As Long, k As Long, tmp As Variant
    For i = LBound(cf, 1) To UBound(cf, 1) - 1
        For j = i + 1 To UBound(cf, 1)
            If cf(j, 4) < cf(i, 4) Then
                For k = 1 To 4
                    tmp = cf(i, k): cf(i, k) = cf(j, k): cf(j, k) = tmp
                Next k
            End If
        Next j
    Next i
End Sub

' Obtem o bloco de fluxos CDI para dCalc:
'   1) bloco real, se a data foi importada;
'   2) bloco sintetico via curva B3, se ha curva p/ dCalc e p/ DATA_FLUXO;
'   3) fallback: bloco mais recente <= dCalc.
' Retorna False se nao ha nenhum bloco.
Private Function ObtemCfCdi(hdr As Object, cdi As Object, dCalc As Date, ByRef cf As Variant) As Boolean
    If cdi Is Nothing Then Exit Function
    Dim dc As String: dc = IsoStr(dCalc)
    If cdi.Exists(dc) Then cf = cdi(dc): ObtemCfCdi = True: Exit Function   ' bloco real: lookup barato

    ' cache do bloco sintetico (so depende de ticker+data, NAO da taxa) -> evita
    ' reconstruir o bloco a cada iteracao da bisseccao do RF_TAXA.
    Dim chave As String
    If hdr.Exists("TICKER") Then chave = UCase(CStr(hdr("TICKER"))) & "|" & dc
    If gCfCache Is Nothing Then Set gCfCache = CreateObject("Scripting.Dictionary")
    If chave <> "" Then If gCfCache.Exists(chave) Then cf = gCfCache(chave): ObtemCfCdi = True: Exit Function

    Dim d0s As String: d0s = CStr(hdr("DATA_FLUXO"))
    If Not cdi.Exists(d0s) Then d0s = MelhorChaveCdi(cdi, dCalc)   ' ancora alternativa
    GaranteCurva
    If Not gCurva Is Nothing And d0s <> "" Then
        If gCurva.Exists(dc) And gCurva.Exists(d0s) And cdi.Exists(d0s) Then
            Dim syn As Variant
            syn = BlocoSintetico(cdi(d0s), Val(CStr(hdr("TAXA_REF"))), dCalc, ParseISO(d0s), gCurva(d0s), gCurva(dc))
            If Not IsEmpty(syn) Then
                If chave <> "" Then gCfCache(chave) = syn
                cf = syn: ObtemCfCdi = True: Exit Function
            End If
        End If
    End If

    Dim k As String: k = MelhorChaveCdi(cdi, dCalc)               ' fallback
    If k <> "" Then cf = cdi(k): ObtemCfCdi = True
End Function

Private Function PegaAtivo(ticker As String, ByRef hdr As Object, ByRef fl As Variant, _
                           ByRef vDates As Variant, ByRef vVals As Variant, _
                           ByRef cdi As Object) As Boolean
    Dim tk As String: tk = UCase(Trim(ticker))
    GaranteFeriados
    If gAtivos Is Nothing Then Set gAtivos = CreateObject("Scripting.Dictionary")
    If Not gAtivos.Exists(tk) Then
        If Not CarregarAtivo(tk) Then Exit Function
    End If
    Dim a As Variant: a = gAtivos(tk)
    Set hdr = a(0): fl = a(1): vDates = a(2): vVals = a(3)
    If IsObject(a(4)) Then Set cdi = a(4) Else Set cdi = Nothing
    PegaAtivo = True
End Function

Private Function ParseISO(s As String) As Date
    Dim p() As String: p = Split(Trim(s), "-")
    On Error GoTo Falha
    If UBound(p) = 2 Then ParseISO = DateSerial(CInt(p(0)), CInt(p(1)), CInt(p(2)))
    Exit Function
Falha:
    ParseISO = 0
End Function

Private Sub OrdenaVNA(ByRef d() As Double, ByRef v() As Double)
    Dim i As Long, j As Long, td As Double, tv As Double
    For i = LBound(d) To UBound(d) - 1
        For j = i + 1 To UBound(d)
            If d(j) < d(i) Then
                td = d(i): d(i) = d(j): d(j) = td
                tv = v(i): v(i) = v(j): v(j) = tv
            End If
        Next j
    Next i
End Sub

' ================= DIAS UTEIS =================

Private Function EhDiaUtil(d As Date) As Boolean
    If Weekday(d, vbMonday) > 5 Then Exit Function
    If gFeriados.Exists(CLng(d)) Then Exit Function
    EhDiaUtil = True
End Function

Private Function ContaDU(d0 As Date, d1 As Date) As Long
    Dim a As Date, b As Date, d As Date, n As Long
    a = Int(d0): b = Int(d1)        ' normaliza p/ dia cheio (ignora fracao de hora)
    If b <= a Then Exit Function
    For d = a + 1 To b
        If EhDiaUtil(d) Then n = n + 1
    Next d
    ContaDU = n
End Function

' ================= VNA(data) =================
Private Function VNAData(vDates As Variant, vVals As Variant, dCalc As Date) As Double
    On Error GoTo Falha
    Dim lo As Long, hi As Long
    lo = LBound(vDates): hi = UBound(vDates)
    Dim x As Double: x = CDbl(dCalc)
    If hi = lo Then VNAData = vVals(lo): Exit Function

    Dim i As Long
    For i = lo To hi
        If vDates(i) = x Then VNAData = vVals(i): Exit Function
    Next i

    Dim a As Long, b As Long
    If x < vDates(lo) Then
        a = lo: b = lo + 1
    ElseIf x > vDates(hi) Then
        a = hi - 1: b = hi
    Else
        For i = lo To hi - 1
            If x >= vDates(i) And x <= vDates(i + 1) Then a = i: b = i + 1: Exit For
        Next i
    End If

    Dim duAB As Long: duAB = ContaDU(CDate(vDates(a)), CDate(vDates(b)))
    If duAB = 0 Then VNAData = vVals(a): Exit Function
    Dim frac As Double
    If x < vDates(a) Then
        frac = -CDbl(ContaDU(dCalc, CDate(vDates(a)))) / duAB
    Else
        frac = CDbl(ContaDU(CDate(vDates(a)), dCalc)) / duAB
    End If
    VNAData = vVals(a) * (vVals(b) / vVals(a)) ^ frac
    Exit Function
Falha:
    VNAData = 0
End Function

' ================= MOTOR =================

' Preenche pvOut(1..n) com o PV de cada fluxo do bloco CDI reprecificado a 'taxa'.
'   cf(i,1..4) = data, vf, pv, du  (assumido ordenado por du crescente, como a API retorna)
'   DI-PERC (y0>=50): curva DI implicita (FD_i = vf/pv); deriva o CDI forward por
'     segmento entre vertices e reaplica o percentual 'taxa'. Exato, sem fonte externa.
'   DI-SPREAD (y0<50): ajuste de spread aditivo sobre o PV.
Private Sub PvCdi(cf As Variant, y0 As Double, taxa As Double, ByRef pvOut() As Double)
    Dim n As Long: n = UBound(cf, 1)
    ReDim pvOut(1 To n)
    Dim i As Long
    If y0 >= 50 Then
        Dim prevDu As Long, lnPrevFD0 As Double, lnFDp1 As Double, dseg As Long, lnFD0 As Double, g As Double
        prevDu = 0: lnPrevFD0 = 0: lnFDp1 = 0
        For i = 1 To n
            lnFD0 = Log(cf(i, 2) / cf(i, 3))           ' ln(vf/pv) = ln do fator desconto a y0
            dseg = cf(i, 4) - prevDu
            If dseg > 0 Then
                g = (Exp((lnFD0 - lnPrevFD0) / dseg) - 1) * 100 / y0   ' CDI forward diario do segmento
                lnFDp1 = lnFDp1 + Log(1 + g * taxa / 100) * dseg
                prevDu = cf(i, 4): lnPrevFD0 = lnFD0
            End If
            pvOut(i) = cf(i, 2) / Exp(lnFDp1)          ' vf / FD(taxa)
        Next i
    Else
        For i = 1 To n
            pvOut(i) = cf(i, 3) * ((1 + y0 / 100) / (1 + taxa / 100)) ^ (cf(i, 4) / 252#)
        Next i
    End If
End Sub

Private Sub CalcCore(hdr As Object, fl As Variant, vDates As Variant, vVals As Variant, _
                     cdi As Object, taxa As Double, dCalc As Date, _
                     ByRef cotacao As Double, ByRef pu As Double, ByRef ehErro As Boolean)
    ehErro = False: cotacao = 0: pu = 0
    Dim i As Long, du As Long

    If UCase(CStr(hdr("INDEXADOR"))) = "CDI" Then
        Dim cf As Variant
        If Not ObtemCfCdi(hdr, cdi, dCalc, cf) Then ehErro = True: Exit Sub
        Dim y0 As Double: y0 = Val(CStr(hdr("TAXA_REF")))
        Dim pvc() As Double: PvCdi cf, y0, taxa, pvc
        For i = 1 To UBound(cf, 1)
            pu = pu + pvc(i)
        Next i
        cotacao = pu
        pu = Int(pu * 1000000#) / 1000000#
        Exit Sub
    End If

    For i = 1 To UBound(fl, 1)
        du = ContaDU(dCalc, CDate(fl(i, 1)))
        If du > 0 Then cotacao = cotacao + fl(i, 6) / (1 + taxa / 100) ^ (du / 252#)
    Next i
    Dim vna As Double: vna = VNAData(vDates, vVals, dCalc)
    If vna <= 0 Then ehErro = True: Exit Sub
    pu = Int(cotacao * vna * 1000000#) / 1000000#
End Sub

' ================= UDFs =================

Public Function RF_PU(ticker As String, taxa As Double, dataCalc As Variant) As Variant
    On Error GoTo Erro
    Dim hdr As Object, fl As Variant, vd As Variant, vv As Variant, cdi As Object
    If Not PegaAtivo(ticker, hdr, fl, vd, vv, cdi) Then RF_PU = CVErr(xlErrNA): Exit Function
    Dim cot As Double, pu As Double, e As Boolean
    CalcCore hdr, fl, vd, vv, cdi, taxa, CDate(dataCalc), cot, pu, e
    If e Then RF_PU = CVErr(xlErrNum) Else RF_PU = pu
    Exit Function
Erro:
    RF_PU = CVErr(xlErrValue)
End Function

Public Function RF_TAXA(ticker As String, pu As Double, dataCalc As Variant) As Variant
    On Error GoTo Erro
    Dim hdr As Object, fl As Variant, vd As Variant, vv As Variant, cdi As Object
    If Not PegaAtivo(ticker, hdr, fl, vd, vv, cdi) Then RF_TAXA = CVErr(xlErrNA): Exit Function
    Dim d As Date: d = CDate(dataCalc)
    Dim lo As Double, hi As Double, mid As Double, cot As Double
    Dim pLo As Double, pHi As Double, pMid As Double, e As Boolean
    lo = 0.0001: hi = 300   ' cobre DI-PERC (% do CDI, ~90-130) e spreads/taxas baixas
    CalcCore hdr, fl, vd, vv, cdi, lo, d, cot, pLo, e
    If e Then RF_TAXA = CVErr(xlErrNum): Exit Function
    CalcCore hdr, fl, vd, vv, cdi, hi, d, cot, pHi, e
    If pu > pLo Or pu < pHi Then RF_TAXA = CVErr(xlErrNum): Exit Function
    Dim it As Long
    For it = 1 To 100
        mid = (lo + hi) / 2
        CalcCore hdr, fl, vd, vv, cdi, mid, d, cot, pMid, e
        If pMid > pu Then lo = mid Else hi = mid
        If hi - lo < 0.0000001 Then Exit For
    Next it
    RF_TAXA = Round((lo + hi) / 2, 6)
    Exit Function
Erro:
    RF_TAXA = CVErr(xlErrValue)
End Function

Public Function RF_DURATION(ticker As String, taxa As Double, dataCalc As Variant) As Variant
    On Error GoTo Erro
    Dim dur As Double, pu As Double, e As Boolean
    DurPU ticker, taxa, CDate(dataCalc), dur, pu, e
    If e Then RF_DURATION = CVErr(xlErrNum) Else RF_DURATION = dur
    Exit Function
Erro:
    RF_DURATION = CVErr(xlErrValue)
End Function

Public Function RF_DV01(ticker As String, taxa As Double, dataCalc As Variant) As Variant
    On Error GoTo Erro
    Dim dur As Double, pu As Double, e As Boolean
    DurPU ticker, taxa, CDate(dataCalc), dur, pu, e
    If e Then RF_DV01 = CVErr(xlErrNum): Exit Function
    RF_DV01 = dur / (1 + taxa / 100) * pu / 10000#
    Exit Function
Erro:
    RF_DV01 = CVErr(xlErrValue)
End Function

Public Function RF_CONVEXIDADE(ticker As String, taxa As Double, dataCalc As Variant) As Variant
    On Error GoTo Erro
    Dim hdr As Object, fl As Variant, vd As Variant, vv As Variant, cdi As Object
    If Not PegaAtivo(ticker, hdr, fl, vd, vv, cdi) Then RF_CONVEXIDADE = CVErr(xlErrNA): Exit Function
    Dim d As Date: d = CDate(dataCalc)
    Dim db As Double: db = 0.1                       ' bump de 0,10 p.p. na taxa
    Dim p0 As Double, pPlus As Double, pMinus As Double, cot As Double, e As Boolean
    CalcCore hdr, fl, vd, vv, cdi, taxa, d, cot, p0, e
    If e Or p0 <= 0 Then RF_CONVEXIDADE = CVErr(xlErrNum): Exit Function
    CalcCore hdr, fl, vd, vv, cdi, taxa + db, d, cot, pPlus, e
    If e Then RF_CONVEXIDADE = CVErr(xlErrNum): Exit Function
    CalcCore hdr, fl, vd, vv, cdi, taxa - db, d, cot, pMinus, e
    If e Then RF_CONVEXIDADE = CVErr(xlErrNum): Exit Function
    Dim dy As Double: dy = db / 100#                 ' bump em fracao (anos^2)
    RF_CONVEXIDADE = (pPlus + pMinus - 2 * p0) / (p0 * dy * dy)
    Exit Function
Erro:
    RF_CONVEXIDADE = CVErr(xlErrValue)
End Function

Private Sub DurPU(ticker As String, taxa As Double, d As Date, _
                  ByRef dur As Double, ByRef pu As Double, ByRef ehErro As Boolean)
    ehErro = False: dur = 0: pu = 0
    Dim hdr As Object, fl As Variant, vd As Variant, vv As Variant, cdi As Object
    If Not PegaAtivo(ticker, hdr, fl, vd, vv, cdi) Then ehErro = True: Exit Sub
    Dim cot As Double, e As Boolean
    CalcCore hdr, fl, vd, vv, cdi, taxa, d, cot, pu, e
    If e Then ehErro = True: Exit Sub

    Dim somaPV As Double, somaTPV As Double, i As Long, t As Double, du As Long, pvi As Double
    If UCase(CStr(hdr("INDEXADOR"))) = "CDI" Then
        Dim y0 As Double: y0 = Val(CStr(hdr("TAXA_REF")))
        Dim cf As Variant
        If Not ObtemCfCdi(hdr, cdi, d, cf) Then ehErro = True: Exit Sub
        Dim pvc() As Double: PvCdi cf, y0, taxa, pvc
        For i = 1 To UBound(cf, 1)
            t = cf(i, 4) / 252#
            somaPV = somaPV + pvc(i): somaTPV = somaTPV + t * pvc(i)
        Next i
    Else
        For i = 1 To UBound(fl, 1)
            du = ContaDU(d, CDate(fl(i, 1)))
            If du <= 0 Then GoTo Prox
            t = du / 252#
            pvi = fl(i, 6) / (1 + taxa / 100) ^ t
            somaPV = somaPV + pvi: somaTPV = somaTPV + t * pvi
Prox:
        Next i
    End If
    If somaPV <= 0 Then ehErro = True Else dur = somaTPV / somaPV
End Sub

Public Function RF_VNA(ticker As String, dataCalc As Variant) As Variant
    On Error GoTo Erro
    Dim hdr As Object, fl As Variant, vd As Variant, vv As Variant, cdi As Object
    If Not PegaAtivo(ticker, hdr, fl, vd, vv, cdi) Then RF_VNA = CVErr(xlErrNA): Exit Function
    Dim v As Double: v = VNAData(vd, vv, CDate(dataCalc))
    If v <= 0 Then RF_VNA = CVErr(xlErrNum) Else RF_VNA = v
    Exit Function
Erro:
    RF_VNA = CVErr(xlErrValue)
End Function

Public Function RF_FLUXO(ticker As String, taxa As Double, dataCalc As Variant) As Variant
    On Error GoTo Erro
    Dim hdr As Object, fl As Variant, vd As Variant, vv As Variant, cdi As Object
    Dim d As Date: d = CDate(dataCalc)
    If Not PegaAtivo(ticker, hdr, fl, vd, vv, cdi) Then RF_FLUXO = CVErr(xlErrNA): Exit Function
    Dim i As Long, rr As Long, du As Long, vf As Double, pvi As Double

    If UCase(CStr(hdr("INDEXADOR"))) = "CDI" Then
        If cdi Is Nothing Then RF_FLUXO = CVErr(xlErrNum): Exit Function
        Dim cf As Variant
        If Not ObtemCfCdi(hdr, cdi, d, cf) Then RF_FLUXO = CVErr(xlErrNum): Exit Function
        Dim y0 As Double: y0 = Val(CStr(hdr("TAXA_REF")))
        Dim pvc() As Double: PvCdi cf, y0, taxa, pvc
        Dim nc As Long: nc = UBound(cf, 1)
        Dim outc() As Variant: ReDim outc(0 To nc, 1 To 5)
        outc(0, 1) = "DATA": outc(0, 2) = "EVENTO": outc(0, 3) = "DU": outc(0, 4) = "VF": outc(0, 5) = "PV @ " & taxa & "%"
        For i = 1 To nc
            du = cf(i, 4): vf = cf(i, 2)
            outc(i, 1) = cf(i, 1): outc(i, 2) = "": outc(i, 3) = du: outc(i, 4) = vf: outc(i, 5) = pvc(i)
        Next i
        RF_FLUXO = outc
        Exit Function
    End If

    Dim vna As Double: vna = VNAData(vd, vv, d)
    If vna <= 0 Then RF_FLUXO = CVErr(xlErrNum): Exit Function
    Dim n As Long: n = UBound(fl, 1)
    Dim out() As Variant: ReDim out(0 To n, 1 To 5)
    out(0, 1) = "DATA": out(0, 2) = "EVENTO": out(0, 3) = "DU": out(0, 4) = "VF": out(0, 5) = "PV @ " & taxa & "%"
    For i = 1 To n
        du = ContaDU(d, CDate(fl(i, 1)))
        If du <= 0 Then GoTo Prox
        vf = fl(i, 6) * vna
        pvi = fl(i, 6) * vna / (1 + taxa / 100) ^ (du / 252#)
        rr = rr + 1
        out(rr, 1) = fl(i, 1): out(rr, 2) = fl(i, 2): out(rr, 3) = du: out(rr, 4) = vf: out(rr, 5) = pvi
Prox:
    Next i
    RF_FLUXO = out
    Exit Function
Erro:
    RF_FLUXO = CVErr(xlErrValue)
End Function

Public Function RF_INFO(ticker As String, campo As String) As Variant
    On Error GoTo Erro
    Dim hdr As Object, fl As Variant, vd As Variant, vv As Variant, cdi As Object
    If Not PegaAtivo(ticker, hdr, fl, vd, vv, cdi) Then RF_INFO = CVErr(xlErrNA): Exit Function
    Dim k As String: k = UCase(Trim(campo))
    If k = "DATAS" Then          ' datas disponiveis (VNA p/ IPCA, blocos p/ CDI)
        Dim s2 As String, kk As Variant
        If Not cdi Is Nothing Then
            For Each kk In cdi.Keys
                s2 = s2 & IIf(s2 = "", "", ", ") & kk
            Next kk
        ElseIf IsArray(vd) Then
            Dim j As Long
            For j = LBound(vd) To UBound(vd)
                s2 = s2 & IIf(s2 = "", "", ", ") & Format(CDate(vd(j)), "DD/MM/YYYY")
            Next j
        End If
        RF_INFO = s2: Exit Function
    End If
    If k = "VNA_DATAS" Then
        Dim s As String, i As Long
        If IsArray(vd) Then
            For i = LBound(vd) To UBound(vd)
                s = s & IIf(s = "", "", ", ") & Format(CDate(vd(i)), "DD/MM/YYYY")
            Next i
        End If
        RF_INFO = s: Exit Function
    End If
    If hdr.Exists(k) Then RF_INFO = hdr(k) Else RF_INFO = "campo invalido"
    Exit Function
Erro:
    RF_INFO = CVErr(xlErrValue)
End Function

' Maior data de evento do ativo (vencimento). Retorna Date.
Private Function VencimentoAtivo(hdr As Object, fl As Variant, cdi As Object) As Date
    If hdr.Exists("VENCIMENTO") Then
        Dim dv As Date: dv = ParseISO(CStr(hdr("VENCIMENTO")))
        If dv > 0 Then VencimentoAtivo = dv: Exit Function
    End If
    Dim best As Double: best = 0
    Dim i As Long, k As Variant, arr As Variant, ev As Date
    If Not cdi Is Nothing Then
        For Each k In cdi.Keys
            arr = cdi(k)
            For i = 1 To UBound(arr, 1)
                ev = CDate(arr(i, 1)): If CDbl(ev) > best Then best = CDbl(ev)
            Next i
        Next k
    ElseIf IsArray(fl) Then
        For i = 1 To UBound(fl, 1)
            ev = CDate(fl(i, 1)): If CDbl(ev) > best Then best = CDbl(ev)
        Next i
    End If
    If best > 0 Then VencimentoAtivo = CDate(best)
End Function

' Data de vencimento do papel (Date).
Public Function RF_VENCIMENTO(ticker As String) As Variant
    On Error GoTo Erro
    Dim hdr As Object, fl As Variant, vd As Variant, vv As Variant, cdi As Object
    If Not PegaAtivo(ticker, hdr, fl, vd, vv, cdi) Then RF_VENCIMENTO = CVErr(xlErrNA): Exit Function
    Dim dv As Date: dv = VencimentoAtivo(hdr, fl, cdi)
    If dv > 0 Then RF_VENCIMENTO = dv Else RF_VENCIMENTO = CVErr(xlErrNA)
    Exit Function
Erro:
    RF_VENCIMENTO = CVErr(xlErrValue)
End Function

' Data da ultima atualizacao do fluxo (DATA_FLUXO importada).
Public Function RF_ATUALIZADO_EM(ticker As String) As Variant
    On Error GoTo Erro
    Dim hdr As Object, fl As Variant, vd As Variant, vv As Variant, cdi As Object
    If Not PegaAtivo(ticker, hdr, fl, vd, vv, cdi) Then RF_ATUALIZADO_EM = CVErr(xlErrNA): Exit Function
    Dim dt As Date
    If hdr.Exists("DATA_FLUXO") Then dt = ParseISO(CStr(hdr("DATA_FLUXO")))
    If dt > 0 Then RF_ATUALIZADO_EM = dt Else RF_ATUALIZADO_EM = CVErr(xlErrNA)
    Exit Function
Erro:
    RF_ATUALIZADO_EM = CVErr(xlErrValue)
End Function

' Proxima data de evento (cupom/amortizacao) estritamente apos dataCalc (Date).
Public Function RF_PROXIMO_EVENTO(ticker As String, dataCalc As Variant) As Variant
    On Error GoTo Erro
    Dim hdr As Object, fl As Variant, vd As Variant, vv As Variant, cdi As Object
    If Not PegaAtivo(ticker, hdr, fl, vd, vv, cdi) Then RF_PROXIMO_EVENTO = CVErr(xlErrNA): Exit Function
    Dim d As Date: d = CDate(dataCalc)
    Dim best As Double: best = 0
    Dim i As Long, ev As Date
    If UCase(CStr(hdr("INDEXADOR"))) = "CDI" Then
        Dim cf As Variant
        If Not ObtemCfCdi(hdr, cdi, d, cf) Then RF_PROXIMO_EVENTO = CVErr(xlErrNum): Exit Function
        For i = 1 To UBound(cf, 1)
            ev = CDate(cf(i, 1))
            If ev > d Then If best = 0 Or CDbl(ev) < best Then best = CDbl(ev)
        Next i
    ElseIf IsArray(fl) Then
        For i = 1 To UBound(fl, 1)
            ev = CDate(fl(i, 1))
            If ev > d Then If best = 0 Or CDbl(ev) < best Then best = CDbl(ev)
        Next i
    End If
    If best > 0 Then RF_PROXIMO_EVENTO = CDate(best) Else RF_PROXIMO_EVENTO = CVErr(xlErrNA)
    Exit Function
Erro:
    RF_PROXIMO_EVENTO = CVErr(xlErrValue)
End Function

' Taxa de referencia contratual: CDI+ -> spread (% a.a.); %CDI -> percentual do
' CDI; IPCA/PRE -> taxa de emissao. (Numero.)
Public Function RF_SPREAD(ticker As String) As Variant
    On Error GoTo Erro
    Dim hdr As Object, fl As Variant, vd As Variant, vv As Variant, cdi As Object
    If Not PegaAtivo(ticker, hdr, fl, vd, vv, cdi) Then RF_SPREAD = CVErr(xlErrNA): Exit Function
    Dim campo As String
    If UCase(CStr(hdr("INDEXADOR"))) = "CDI" Then campo = "TAXA_REF" Else campo = "TAXA_EMISSAO"
    If hdr.Exists(campo) Then RF_SPREAD = Val(CStr(hdr(campo))) Else RF_SPREAD = CVErr(xlErrNA)
    Exit Function
Erro:
    RF_SPREAD = CVErr(xlErrValue)
End Function

Public Function RF_LISTAR() As Variant
    Dim arr() As String, n As Long, f As String
    ReDim arr(1 To 10000)
    f = Dir(FluxosDir() & "*.csv")
    Do While f <> ""
        If Left(f, 1) <> "_" Then
            n = n + 1: arr(n) = Left(f, Len(f) - 4)
        End If
        f = Dir()
    Loop
    If n = 0 Then RF_LISTAR = "nenhum ativo em " & FluxosDir(): Exit Function
    Dim out() As Variant: ReDim out(1 To n, 1 To 1)
    Dim i As Long
    For i = 1 To n
        out(i, 1) = arr(i)
    Next i
    RF_LISTAR = out
End Function

' ================= DICAS DE ARGUMENTO (fx) =================
Private Sub RegistrarFuncoes()
    On Error Resume Next
    Const CAT As String = "Renda Fixa"
    Application.MacroOptions Macro:="RF_PU", Category:=CAT, _
        Description:="PU do ativo na data, dada a taxa (% a.a.).", _
        ArgumentDescriptions:=Array("Ticker (ex: ""EGIEA6"")", "Taxa em % a.a. (ex: 6,2474)", "Data (ex: ""12/06/2026"")")
    Application.MacroOptions Macro:="RF_TAXA", Category:=CAT, _
        Description:="Taxa implicita (% a.a.) na data, dado o PU.", _
        ArgumentDescriptions:=Array("Ticker", "PU de mercado", "Data de calculo")
    Application.MacroOptions Macro:="RF_DURATION", Category:=CAT, _
        Description:="Duration de Macaulay (anos).", _
        ArgumentDescriptions:=Array("Ticker", "Taxa em % a.a.", "Data de calculo")
    Application.MacroOptions Macro:="RF_DV01", Category:=CAT, _
        Description:="DV01 em R$ por +1 bp (dur.modif. x PU x 0,0001).", _
        ArgumentDescriptions:=Array("Ticker", "Taxa em % a.a.", "Data de calculo")
    Application.MacroOptions Macro:="RF_VNA", Category:=CAT, _
        Description:="VNA na data (exato nas datas importadas; interpola).", _
        ArgumentDescriptions:=Array("Ticker", "Data de calculo")
    Application.MacroOptions Macro:="RF_FLUXO", Category:=CAT, _
        Description:="Tabela do fluxo descontado (Data|Evento|DU|VF|PV).", _
        ArgumentDescriptions:=Array("Ticker", "Taxa em % a.a.", "Data de calculo")
    Application.MacroOptions Macro:="RF_INFO", Category:=CAT, _
        Description:="Info do cabecalho (EMISSOR, VENCIMENTO...) ou ""VNA_DATAS"".", _
        ArgumentDescriptions:=Array("Ticker", "Campo")
    Application.MacroOptions Macro:="RF_LISTAR", Category:=CAT, _
        Description:="Lista os ativos disponiveis na pasta de fluxos."
End Sub

' ================= EXPORTAR =================
Public Sub RF_EXPORTAR()
    Dim tk As String, sTaxa As String, sData As String
    tk = UCase(Trim(InputBox("Ticker:", "Exportar fluxo")))
    If tk = "" Then Exit Sub
    sTaxa = InputBox("Taxa (% a.a.):", "Exportar fluxo")
    If sTaxa = "" Then Exit Sub
    sData = InputBox("Data (DD/MM/AAAA):", "Exportar fluxo", Format(Date, "DD/MM/YYYY"))
    If sData = "" Then Exit Sub
    Dim taxa As Double: taxa = CDbl(sTaxa)
    Dim d As Date: d = CDate(sData)
    Dim tbl As Variant: tbl = RF_FLUXO(tk, taxa, d)
    If IsError(tbl) Then
        MsgBox "Falha: confira ticker/data. CDI so calcula na DATA_FLUXO do CSV.", vbExclamation
        Exit Sub
    End If
    Dim wb As Workbook: Set wb = Workbooks.Add
    Dim ws As Worksheet: Set ws = wb.Worksheets(1)
    ws.Name = Left(tk, 31)
    ws.Range("A1") = "FLUXO DESCONTADO - " & tk & "  @" & taxa & "%  " & Format(d, "DD/MM/YYYY")
    ws.Range("A1").Font.Bold = True
    Dim n As Long: n = UBound(tbl, 1)
    Dim i As Long, j As Long
    For i = 0 To n
        For j = 1 To 5
            ws.Cells(3 + i, j) = tbl(i, j)
        Next j
    Next i
    ws.Range(ws.Cells(3, 1), ws.Cells(3, 5)).Font.Bold = True
    ws.Cells(4 + n, 4) = "PU ="
    ws.Cells(4 + n, 5).Formula = "=SUM(" & ws.Range(ws.Cells(4, 5), ws.Cells(3 + n, 5)).Address & ")"
    ws.Cells(4 + n, 4).Font.Bold = True: ws.Cells(4 + n, 5).Font.Bold = True
    ws.Columns("A:E").AutoFit
    MsgBox "Planilha gerada. Salve onde quiser (Ctrl+S).", vbInformation
End Sub
