Attribute VB_Name = "DEB_Calc2"
' ============================================================
'  CALCULADORA RENDA FIXA v3  -  ADD-IN
'  Le os fluxos de arquivos Excel na pasta FLUXOS_DIR.
'  Cada ativo = 1 arquivo <TICKER>.xlsx (gerado por importar_fluxos.py).
'
'  MODELO (papeis IPCA/PRE):
'    PU(data,taxa) = [ Soma FC_i% / (1+taxa/100)^(du_i/252) ] * VNA(data)
'    - "cotacao" (o somatorio) e' calculada EXATA em qualquer data;
'    - VNA(data) vem da aba VNA do arquivo (1 ponto por data importada),
'      com interpolacao geometrica entre pontos. Importe a data desejada
'      (python importar_fluxos.py TICKER AAAA-MM-DD) para deixa-la EXATA.
'    Papeis CDI: so calculam na DATA_FLUXO do arquivo (ajuste de spread sobre PV).
'
'  FUNCOES (taxa em % a.a., ex: 6.2474; data obrigatoria):
'    DEB_PU       (ticker, taxa, data)  -> PU
'    DEB_TAXA     (ticker, pu,   data)  -> taxa implicita (% a.a.)
'    DEB_DURATION (ticker, taxa, data)  -> duration Macaulay (anos)
'    DEB_DV01     (ticker, taxa, data)  -> DV01 em R$ por +1 bp (positivo)
'    DEB_VNA      (ticker, data)        -> VNA na data (interpolado)
'    DEB_FLUXO    (ticker, taxa, data)  -> tabela do fluxo (array dinamico)
'    DEB_INFO     (ticker, campo)       -> info do cabecalho ou "VNA_DATAS"
'    DEB_LISTAR   ()                    -> ativos carregados
'
'  MACROS (Alt+F8):
'    DEB_ATUALIZAR  -> recarrega os arquivos da pasta
'    DEB_EXPORTAR   -> gera planilha formatada VF->PV para enviar
' ============================================================
Option Explicit

' >>> AJUSTE AQUI SE MUDAR A PASTA <<<
Private Const FLUXOS_DIR As String = _
    "C:\Users\Nitro 5\OneDrive\Documentos\Claude_code\Projeto_calculadora_excel\Codigo_Fluxo\sistema\fluxos\"

Private gAtivos As Object      ' ticker -> Array(hdr, flows2D, vDates(), vVals())
Private gFeriados As Object    ' CLng(date) -> True

' ================= CARGA =================

Public Sub Auto_Open()
    On Error Resume Next
    CarregarTudo
    RegistrarFuncoes      ' dicas de argumento (IntelliSense via fx)
End Sub

Public Sub DEB_ATUALIZAR()
    CarregarTudo
    RegistrarFuncoes
    MsgBox gAtivos.Count & " ativos carregados de:" & vbCrLf & FLUXOS_DIR, _
           vbInformation, "RF Calc"
End Sub

Private Sub CarregarTudo()
    Set gAtivos = CreateObject("Scripting.Dictionary")
    Set gFeriados = CreateObject("Scripting.Dictionary")

    Dim scrn As Boolean: scrn = Application.ScreenUpdating
    Application.ScreenUpdating = False
    On Error GoTo Fim

    CarregarFeriados

    Dim f As String
    f = Dir(FLUXOS_DIR & "*.xlsx")
    Do While f <> ""
        If Left(f, 1) <> "_" And Left(f, 1) <> "~" Then CarregarAtivo FLUXOS_DIR & f
        f = Dir()
    Loop
Fim:
    Application.ScreenUpdating = scrn
End Sub

Private Sub CarregarFeriados()
    Dim wb As Workbook, ws As Worksheet, i As Long, lastR As Long
    On Error GoTo Sai
    Set wb = Workbooks.Open(FLUXOS_DIR & "_feriados.xlsx", ReadOnly:=True, AddToMru:=False)
    Set ws = wb.Worksheets(1)
    lastR = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    For i = 2 To lastR
        If IsDate(ws.Cells(i, 1).Value) Then gFeriados(CLng(CDate(ws.Cells(i, 1).Value))) = True
    Next i
Sai:
    If Not wb Is Nothing Then wb.Close SaveChanges:=False
End Sub

Private Sub CarregarAtivo(caminho As String)
    Dim wb As Workbook, ws As Worksheet
    On Error GoTo Sai
    Set wb = Workbooks.Open(caminho, ReadOnly:=True, AddToMru:=False)
    Set ws = wb.Worksheets("Fluxo")

    ' Cabecalho chave/valor ate a linha "DATA | EVENTO"
    Dim hdr As Object: Set hdr = CreateObject("Scripting.Dictionary")
    Dim hr As Long, i As Long
    For i = 1 To 60
        If UCase(Trim(CStr(ws.Cells(i, 1).Value))) = "DATA" _
           And UCase(Trim(CStr(ws.Cells(i, 2).Value))) = "EVENTO" Then
            hr = i: Exit For
        End If
        Dim k As String: k = UCase(Trim(CStr(ws.Cells(i, 1).Value)))
        If k <> "" Then hdr(k) = ws.Cells(i, 2).Value
    Next i
    If hr = 0 Then GoTo Sai

    Dim tk As String: tk = UCase(Trim(CStr(hdr("TICKER"))))
    If tk = "" Then GoTo Sai

    ' Fluxos: 1=Data 2=Evento 3=VF 4=PV 5=DU 6=FC%
    Dim lastR As Long: lastR = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    Dim n As Long: n = lastR - hr
    If n < 1 Then GoTo Sai
    Dim fl() As Variant: ReDim fl(1 To n, 1 To 6)
    Dim r As Long
    For r = 1 To n
        fl(r, 1) = CDate(ws.Cells(hr + r, 1).Value)
        fl(r, 2) = CStr(ws.Cells(hr + r, 2).Value)
        fl(r, 3) = Num0(ws.Cells(hr + r, 3).Value)
        fl(r, 4) = Num0(ws.Cells(hr + r, 4).Value)
        fl(r, 5) = CLng(Num0(ws.Cells(hr + r, 5).Value))
        fl(r, 6) = Num0(ws.Cells(hr + r, 6).Value)
    Next r

    ' Aba VNA -> arrays ordenados
    Dim vDates() As Double, vVals() As Double, m As Long
    Dim wv As Worksheet
    On Error Resume Next
    Set wv = wb.Worksheets("VNA")
    On Error GoTo Sai
    If Not wv Is Nothing Then
        Dim vl As Long: vl = wv.Cells(wv.Rows.Count, 1).End(xlUp).Row
        m = vl - 1
        If m >= 1 Then
            ReDim vDates(1 To m): ReDim vVals(1 To m)
            For r = 1 To m
                vDates(r) = CDbl(CDate(wv.Cells(r + 1, 1).Value))
                vVals(r) = Num0(wv.Cells(r + 1, 2).Value)
            Next r
            OrdenaVNA vDates, vVals
        End If
    End If

    gAtivos(tk) = Array(hdr, fl, vDates, vVals)
Sai:
    If Not wb Is Nothing Then wb.Close SaveChanges:=False
End Sub

Private Function Num0(v As Variant) As Double
    If IsNumeric(v) Then Num0 = CDbl(v) Else Num0 = 0
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
    Dim d As Date, n As Long
    If d1 <= d0 Then ContaDU = 0: Exit Function
    For d = d0 + 1 To d1
        If EhDiaUtil(d) Then n = n + 1
    Next d
    ContaDU = n
End Function

' ================= VNA(data) =================
' Exato nas datas importadas; interpolacao/extrapolacao geometrica por dias uteis.
Private Function VNAData(vDates As Variant, vVals As Variant, _
                         dCalc As Date) As Double
    On Error GoTo Falha
    Dim m As Long
    m = UBound(vDates) - LBound(vDates) + 1
    Dim x As Double: x = CDbl(dCalc)
    Dim lo As Long: lo = LBound(vDates)
    Dim hi As Long: hi = UBound(vDates)

    If m = 1 Then VNAData = vVals(lo): Exit Function

    ' match exato
    Dim i As Long
    For i = lo To hi
        If vDates(i) = x Then VNAData = vVals(i): Exit Function
    Next i

    Dim a As Long, b As Long
    If x < vDates(lo) Then
        a = lo: b = lo + 1            ' extrapola para tras
    ElseIf x > vDates(hi) Then
        a = hi - 1: b = hi            ' extrapola para frente
    Else
        For i = lo To hi - 1          ' bracket
            If x >= vDates(i) And x <= vDates(i + 1) Then a = i: b = i + 1: Exit For
        Next i
    End If

    Dim duAB As Long, duAX As Long
    duAB = ContaDU(CDate(vDates(a)), CDate(vDates(b)))
    If duAB = 0 Then VNAData = vVals(a): Exit Function
    duAX = ContaDU(CDate(vDates(a)), dCalc)   ' negativo logico se x<a: tratamos via sinal
    Dim frac As Double
    If x < vDates(a) Then
        frac = -CDbl(ContaDU(dCalc, CDate(vDates(a)))) / duAB
    Else
        frac = CDbl(duAX) / duAB
    End If
    VNAData = vVals(a) * (vVals(b) / vVals(a)) ^ frac
    Exit Function
Falha:
    VNAData = 0
End Function

' ================= MOTOR =================

Private Function PegaAtivo(ticker As String, ByRef hdr As Object, ByRef fl As Variant, _
                           ByRef vDates As Variant, ByRef vVals As Variant) As Boolean
    Dim tk As String: tk = UCase(Trim(ticker))
    If gAtivos Is Nothing Then CarregarTudo
    If Not gAtivos.Exists(tk) Then Exit Function
    Dim a As Variant: a = gAtivos(tk)
    Set hdr = a(0): fl = a(1): vDates = a(2): vVals = a(3)
    PegaAtivo = True
End Function

' Cotacao (somatorio dos FC% descontados) e PU. Retorna via ByRef.
Private Sub CalcCore(hdr As Object, fl As Variant, vDates As Variant, vVals As Variant, _
                     taxa As Double, dCalc As Date, _
                     ByRef cotacao As Double, ByRef pu As Double, ByRef ehErro As Boolean)
    ehErro = False
    cotacao = 0: pu = 0
    Dim i As Long, t As Double, du As Long

    If UCase(CStr(hdr("INDEXADOR"))) = "CDI" Then
        ' CDI: so na DATA_FLUXO, ajuste marginal sobre PV
        If CLng(dCalc) <> CLng(CDate(hdr("DATA_FLUXO"))) Then ehErro = True: Exit Sub
        Dim y0 As Double: y0 = CDbl(hdr("TAXA_REF"))
        For i = 1 To UBound(fl, 1)
            t = fl(i, 5) / 252#
            pu = pu + fl(i, 4) * ((1 + y0 / 100) / (1 + taxa / 100)) ^ t
        Next i
        cotacao = pu   ' nao ha VNA separado p/ CDI
        pu = Int(pu * 1000000#) / 1000000#
        Exit Sub
    End If

    ' IPCA / PRE
    For i = 1 To UBound(fl, 1)
        du = ContaDU(dCalc, CDate(fl(i, 1)))
        If du > 0 Then cotacao = cotacao + fl(i, 6) / (1 + taxa / 100) ^ (du / 252#)
    Next i
    Dim vna As Double: vna = VNAData(vDates, vVals, dCalc)
    If vna <= 0 Then ehErro = True: Exit Sub
    pu = Int(cotacao * vna * 1000000#) / 1000000#   ' truncamento T|06 (B3)
End Sub

' ================= UDFs =================

Public Function DEB_PU(ticker As String, taxa As Double, dataCalc As Variant) As Variant
    On Error GoTo Erro
    Dim hdr As Object, fl As Variant, vDates As Variant, vVals As Variant
    If Not PegaAtivo(ticker, hdr, fl, vDates, vVals) Then DEB_PU = CVErr(xlErrNA): Exit Function
    Dim cot As Double, pu As Double, e As Boolean
    CalcCore hdr, fl, vDates, vVals, taxa, CDate(dataCalc), cot, pu, e
    If e Then DEB_PU = CVErr(xlErrNum) Else DEB_PU = pu
    Exit Function
Erro:
    DEB_PU = CVErr(xlErrValue)
End Function

Public Function DEB_TAXA(ticker As String, pu As Double, dataCalc As Variant) As Variant
    On Error GoTo Erro
    Dim hdr As Object, fl As Variant, vDates As Variant, vVals As Variant
    If Not PegaAtivo(ticker, hdr, fl, vDates, vVals) Then DEB_TAXA = CVErr(xlErrNA): Exit Function
    Dim d As Date: d = CDate(dataCalc)
    Dim lo As Double, hi As Double, mid As Double
    Dim cot As Double, pLo As Double, pHi As Double, pMid As Double, e As Boolean
    lo = 0.0001: hi = 99
    CalcCore hdr, fl, vDates, vVals, lo, d, cot, pLo, e
    If e Then DEB_TAXA = CVErr(xlErrNum): Exit Function
    CalcCore hdr, fl, vDates, vVals, hi, d, cot, pHi, e
    If pu > pLo Or pu < pHi Then DEB_TAXA = CVErr(xlErrNum): Exit Function
    Dim it As Long
    For it = 1 To 100
        mid = (lo + hi) / 2
        CalcCore hdr, fl, vDates, vVals, mid, d, cot, pMid, e
        If pMid > pu Then lo = mid Else hi = mid
        If hi - lo < 0.0000001 Then Exit For
    Next it
    DEB_TAXA = Round((lo + hi) / 2, 6)
    Exit Function
Erro:
    DEB_TAXA = CVErr(xlErrValue)
End Function

Public Function DEB_DURATION(ticker As String, taxa As Double, dataCalc As Variant) As Variant
    On Error GoTo Erro
    Dim dur As Double, pu As Double, e As Boolean
    DurPU ticker, taxa, CDate(dataCalc), dur, pu, e
    If e Then DEB_DURATION = CVErr(xlErrNum) Else DEB_DURATION = dur
    Exit Function
Erro:
    DEB_DURATION = CVErr(xlErrValue)
End Function

' DV01 analitico = duration_modificada * PU * 0.0001
'   = duration / (1+taxa/100) * PU / 10000   (R$ por +1 bp; valor positivo)
Public Function DEB_DV01(ticker As String, taxa As Double, dataCalc As Variant) As Variant
    On Error GoTo Erro
    Dim dur As Double, pu As Double, e As Boolean
    DurPU ticker, taxa, CDate(dataCalc), dur, pu, e
    If e Then DEB_DV01 = CVErr(xlErrNum): Exit Function
    DEB_DV01 = dur / (1 + taxa / 100) * pu / 10000#
    Exit Function
Erro:
    DEB_DV01 = CVErr(xlErrValue)
End Function

' Calcula duration (Macaulay) e PU juntos. VNA cancela na duration.
Private Sub DurPU(ticker As String, taxa As Double, d As Date, _
                  ByRef dur As Double, ByRef pu As Double, ByRef ehErro As Boolean)
    ehErro = False: dur = 0: pu = 0
    Dim hdr As Object, fl As Variant, vDates As Variant, vVals As Variant
    If Not PegaAtivo(ticker, hdr, fl, vDates, vVals) Then ehErro = True: Exit Sub

    Dim cot As Double, e As Boolean
    CalcCore hdr, fl, vDates, vVals, taxa, d, cot, pu, e
    If e Then ehErro = True: Exit Sub

    Dim ehCDI As Boolean: ehCDI = (UCase(CStr(hdr("INDEXADOR"))) = "CDI")
    Dim y0 As Double: If ehCDI Then y0 = CDbl(hdr("TAXA_REF"))
    Dim somaPV As Double, somaTPV As Double, i As Long, t As Double, du As Long, pvi As Double
    For i = 1 To UBound(fl, 1)
        If ehCDI Then
            t = fl(i, 5) / 252#
            pvi = fl(i, 4) * ((1 + y0 / 100) / (1 + taxa / 100)) ^ t
        Else
            du = ContaDU(d, CDate(fl(i, 1)))
            If du <= 0 Then GoTo Prox
            t = du / 252#
            pvi = fl(i, 6) / (1 + taxa / 100) ^ t   ' VNA cancela
        End If
        somaPV = somaPV + pvi
        somaTPV = somaTPV + t * pvi
Prox:
    Next i
    If somaPV <= 0 Then ehErro = True Else dur = somaTPV / somaPV
End Sub

Public Function DEB_VNA(ticker As String, dataCalc As Variant) As Variant
    On Error GoTo Erro
    Dim hdr As Object, fl As Variant, vDates As Variant, vVals As Variant
    If Not PegaAtivo(ticker, hdr, fl, vDates, vVals) Then DEB_VNA = CVErr(xlErrNA): Exit Function
    Dim v As Double: v = VNAData(vDates, vVals, CDate(dataCalc))
    If v <= 0 Then DEB_VNA = CVErr(xlErrNum) Else DEB_VNA = v
    Exit Function
Erro:
    DEB_VNA = CVErr(xlErrValue)
End Function

' Tabela do fluxo descontado (array). Excel 365 derrama sozinho.
Public Function DEB_FLUXO(ticker As String, taxa As Double, dataCalc As Variant) As Variant
    On Error GoTo Erro
    Dim hdr As Object, fl As Variant, vDates As Variant, vVals As Variant
    Dim d As Date: d = CDate(dataCalc)
    If Not PegaAtivo(ticker, hdr, fl, vDates, vVals) Then DEB_FLUXO = CVErr(xlErrNA): Exit Function

    Dim ehCDI As Boolean: ehCDI = (UCase(CStr(hdr("INDEXADOR"))) = "CDI")
    Dim vna As Double
    If ehCDI Then
        If CLng(d) <> CLng(CDate(hdr("DATA_FLUXO"))) Then DEB_FLUXO = CVErr(xlErrNum): Exit Function
        vna = 1
    Else
        vna = VNAData(vDates, vVals, d)
        If vna <= 0 Then DEB_FLUXO = CVErr(xlErrNum): Exit Function
    End If
    Dim y0 As Double: If ehCDI Then y0 = CDbl(hdr("TAXA_REF"))

    Dim n As Long: n = UBound(fl, 1)
    Dim out() As Variant: ReDim out(0 To n, 1 To 5)
    out(0, 1) = "DATA": out(0, 2) = "EVENTO": out(0, 3) = "DU"
    out(0, 4) = "VF": out(0, 5) = "PV @ " & taxa & "%"

    Dim i As Long, rr As Long, du As Long, vf As Double, pvi As Double
    For i = 1 To n
        If ehCDI Then
            du = fl(i, 5)
            vf = fl(i, 3)
            pvi = fl(i, 4) * ((1 + y0 / 100) / (1 + taxa / 100)) ^ (du / 252#)
        Else
            du = ContaDU(d, CDate(fl(i, 1)))
            If du <= 0 Then GoTo Prox
            vf = fl(i, 6) * vna                                   ' VF na data
            pvi = fl(i, 6) * vna / (1 + taxa / 100) ^ (du / 252#) ' PV na data
        End If
        rr = rr + 1
        out(rr, 1) = fl(i, 1): out(rr, 2) = fl(i, 2): out(rr, 3) = du
        out(rr, 4) = vf: out(rr, 5) = pvi
Prox:
    Next i
    DEB_FLUXO = out
    Exit Function
Erro:
    DEB_FLUXO = CVErr(xlErrValue)
End Function

Public Function DEB_INFO(ticker As String, campo As String) As Variant
    On Error GoTo Erro
    Dim hdr As Object, fl As Variant, vDates As Variant, vVals As Variant
    If Not PegaAtivo(ticker, hdr, fl, vDates, vVals) Then DEB_INFO = CVErr(xlErrNA): Exit Function
    Dim k As String: k = UCase(Trim(campo))
    If k = "VNA_DATAS" Then
        Dim s As String, i As Long
        For i = LBound(vDates) To UBound(vDates)
            s = s & IIf(s = "", "", ", ") & Format(CDate(vDates(i)), "DD/MM/YYYY")
        Next i
        DEB_INFO = s: Exit Function
    End If
    If hdr.Exists(k) Then DEB_INFO = hdr(k) Else DEB_INFO = "campo invalido"
    Exit Function
Erro:
    DEB_INFO = CVErr(xlErrValue)
End Function

Public Function DEB_LISTAR() As Variant
    If gAtivos Is Nothing Then CarregarTudo
    If gAtivos.Count = 0 Then DEB_LISTAR = "nenhum ativo em " & FLUXOS_DIR: Exit Function
    Dim out() As Variant: ReDim out(1 To gAtivos.Count, 1 To 1)
    Dim kk As Variant, i As Long
    For Each kk In gAtivos.Keys
        i = i + 1: out(i, 1) = kk
    Next kk
    DEB_LISTAR = out
End Function

' ================= DICAS DE ARGUMENTO (IntelliSense via fx) =================
Private Sub RegistrarFuncoes()
    On Error Resume Next
    Const CAT As String = "Renda Fixa"
    Application.MacroOptions Macro:="DEB_PU", _
        Description:="PU do ativo na data, dada a taxa (% a.a.).", Category:=CAT, _
        ArgumentDescriptions:=Array( _
            "Ticker do ativo (ex: ""EGIEA6"")", _
            "Taxa de desconto em % a.a. (ex: 6,2474)", _
            "Data de calculo (ex: ""11/06/2026"" ou referencia a celula)")
    Application.MacroOptions Macro:="DEB_TAXA", _
        Description:="Taxa implicita (% a.a.) na data, dado o PU.", Category:=CAT, _
        ArgumentDescriptions:=Array( _
            "Ticker do ativo (ex: ""EGIEA6"")", _
            "PU de mercado (ex: 1448,562894)", _
            "Data de calculo (ex: ""11/06/2026"")")
    Application.MacroOptions Macro:="DEB_DURATION", _
        Description:="Duration de Macaulay (anos) na data, dada a taxa.", Category:=CAT, _
        ArgumentDescriptions:=Array( _
            "Ticker do ativo", "Taxa em % a.a.", "Data de calculo")
    Application.MacroOptions Macro:="DEB_DV01", _
        Description:="DV01 em R$ por +1 bp (dur.modif. x PU x 0,0001).", Category:=CAT, _
        ArgumentDescriptions:=Array( _
            "Ticker do ativo", "Taxa em % a.a.", "Data de calculo")
    Application.MacroOptions Macro:="DEB_VNA", _
        Description:="VNA do ativo na data (exato nas datas importadas; interpola entre elas).", _
        Category:=CAT, _
        ArgumentDescriptions:=Array("Ticker do ativo", "Data de calculo")
    Application.MacroOptions Macro:="DEB_FLUXO", _
        Description:="Tabela do fluxo descontado (matriz: Data|Evento|DU|VF|PV).", Category:=CAT, _
        ArgumentDescriptions:=Array("Ticker do ativo", "Taxa em % a.a.", "Data de calculo")
    Application.MacroOptions Macro:="DEB_INFO", _
        Description:="Info do cabecalho (EMISSOR, VENCIMENTO...) ou ""VNA_DATAS"".", Category:=CAT, _
        ArgumentDescriptions:=Array("Ticker do ativo", "Campo (ex: ""EMISSOR"")")
    Application.MacroOptions Macro:="DEB_LISTAR", _
        Description:="Lista os ativos carregados da pasta de fluxos.", Category:=CAT
End Sub

' ================= EXPORTAR =================
Public Sub DEB_EXPORTAR()
    Dim tk As String, sTaxa As String, sData As String
    tk = UCase(Trim(InputBox("Ticker:", "Exportar fluxo")))
    If tk = "" Then Exit Sub
    sTaxa = InputBox("Taxa (% a.a., ex: 6,2474):", "Exportar fluxo")
    If sTaxa = "" Then Exit Sub
    sData = InputBox("Data de calculo (DD/MM/AAAA):", "Exportar fluxo", Format(Date, "DD/MM/YYYY"))
    If sData = "" Then Exit Sub

    Dim taxa As Double: taxa = CDbl(sTaxa)
    Dim d As Date: d = CDate(sData)
    Dim tbl As Variant: tbl = DEB_FLUXO(tk, taxa, d)
    If IsError(tbl) Then
        MsgBox "Falha: confira ticker/data. CDI so calcula na DATA_FLUXO do arquivo." & vbCrLf & _
               "Para data exata em IPCA, importe-a: python importar_fluxos.py " & tk & " AAAA-MM-DD", _
               vbExclamation
        Exit Sub
    End If

    Dim hdr As Object, fl As Variant, vD As Variant, vV As Variant
    PegaAtivo tk, hdr, fl, vD, vV

    Dim wb As Workbook: Set wb = Workbooks.Add
    Dim ws As Worksheet: Set ws = wb.Worksheets(1)
    ws.Name = Left(tk, 31)
    With ws
        .Range("A1") = "FLUXO DE CAIXA DESCONTADO  -  " & tk
        .Range("A1").Font.Bold = True: .Range("A1").Font.Size = 14
        .Range("A3") = "Emissor:":      .Range("B3") = hdr("EMISSOR")
        .Range("A4") = "Indexador:":    .Range("B4") = hdr("INDEXADOR")
        .Range("A5") = "Data calculo:": .Range("B5") = d: .Range("B5").NumberFormat = "DD/MM/YYYY"
        .Range("A6") = "Taxa:":         .Range("B6") = taxa & "% a.a."
        .Range("A7") = "VNA:":          .Range("B7") = DEB_VNA(tk, d): .Range("B7").NumberFormat = "#,##0.000000"
        .Range("A3:A7").Font.Bold = True

        Dim n As Long: n = UBound(tbl, 1)
        Dim i As Long, j As Long
        For i = 0 To n
            For j = 1 To 5
                .Cells(9 + i, j) = tbl(i, j)
            Next j
        Next i
        .Range(.Cells(9, 1), .Cells(9, 5)).Font.Bold = True
        .Range(.Cells(9, 1), .Cells(9, 5)).Interior.Color = RGB(217, 225, 242)
        .Range(.Cells(10, 1), .Cells(9 + n, 1)).NumberFormat = "DD/MM/YYYY"
        .Range(.Cells(10, 4), .Cells(9 + n, 5)).NumberFormat = "#,##0.000000"

        Dim rTot As Long: rTot = 10 + n
        .Cells(rTot, 4) = "PU ="
        .Cells(rTot, 4).Font.Bold = True
        .Cells(rTot, 5).Formula = "=SUM(" & .Range(.Cells(10, 5), .Cells(9 + n, 5)).Address & ")"
        .Cells(rTot, 5).Font.Bold = True
        .Cells(rTot, 5).NumberFormat = "#,##0.000000"
        .Columns("A:E").AutoFit
    End With
    MsgBox "Planilha gerada. Salve onde quiser (Ctrl+S).", vbInformation
End Sub
