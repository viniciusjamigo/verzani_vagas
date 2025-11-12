Attribute VB_Name = "ModuleDashboard"
Option Explicit

' --- FERRAMENTAS DE DIAGNOSTICO E LIMPEZA ---

Sub PadronizarCabecalhos()
    ' OBJETIVO: Remover acentos e cedilhas de todos os cabecalhos (linha 1) da aba "BD".
    Dim ws As Worksheet
    Dim ultColuna As Long
    Dim i As Long
    Dim cabecalhoOriginal As String
    Dim cabecalhoAlterado As String
    Dim alteracoesFeitas As Long
    
    alteracoesFeitas = 0
    
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets("BD")
    On Error GoTo 0
    
    If ws Is Nothing Then
        MsgBox "A planilha 'BD' nao foi encontrada.", vbCritical
        Exit Sub
    End If
    
    ' Garante que a planilha esta ativa para o usuario ver
    ws.Activate
    
    ultColuna = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    
    If ultColuna = 1 And IsEmpty(ws.Cells(1, 1).Value) Then
        MsgBox "A linha de cabecalho (linha 1) na aba 'BD' parece estar vazia. Nenhum cabecalho foi processado.", vbExclamation
        Exit Sub
    End If

    For i = 1 To ultColuna
        If Not IsEmpty(ws.Cells(1, i).Value) Then
            cabecalhoOriginal = ws.Cells(1, i).Value
            cabecalhoAlterado = RemoverAcentos(cabecalhoOriginal)
            
            If cabecalhoOriginal <> cabecalhoAlterado Then
                ws.Cells(1, i).Value = cabecalhoAlterado
                alteracoesFeitas = alteracoesFeitas + 1
            End If
        End If
    Next i
    
    MsgBox "Verificacao de cabecalhos concluida." & vbCrLf & vbCrLf & _
           "Total de colunas processadas: " & ultColuna & vbCrLf & _
           "Cabecalhos alterados: " & alteracoesFeitas, vbInformation
End Sub

Sub LimparNomesRecrutadores()
    ' OBJETIVO: Padronizar TODAS as variacoes de "BRUNA SO..." para "BRUNA SOUZA".
    Dim ws As Worksheet
    Dim ultLinha As Long
    Dim i As Long
    Dim cel As Range
    Dim contador As Long
    
    contador = 0
    
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets("BD")
    On Error GoTo 0
    
    If ws Is Nothing Then
        MsgBox "A planilha 'BD' nao foi encontrada.", vbCritical
        Exit Sub
    End If
    
    ultLinha = ws.Cells(ws.Rows.Count, "B").End(xlUp).Row
    
    Application.ScreenUpdating = False
    
    For i = 2 To ultLinha
        Set cel = ws.Cells(i, "B")
        ' Verifica se a celula comeca com "BRUNA SO"
        If Left(Trim(cel.Value), 8) = "BRUNA SO" Then
            If cel.Value <> "BRUNA SOUZA" Then
                cel.Value = "BRUNA SOUZA"
                contador = contador + 1
            End If
        End If
    Next i
    
    Application.ScreenUpdating = True
    
    MsgBox "Limpeza de nomes de recrutadores concluida." & vbCrLf & vbCrLf & _
           "Celulas alteradas: " & contador, vbInformation
End Sub

Sub VerificarRecrutador()
    ' OBJETIVO: Procurar por "BRUNA SOUZA" na coluna B (Recrutador) entre as linhas 2 e 10000.
    Dim ws As Worksheet
    Dim i As Long
    Dim valorLimpo As String
    
    On Error Resume Next
    Set ws = ThisWorkbook.Worksheets("BD")
    On Error GoTo 0
    
    If ws Is Nothing Then
        MsgBox "A planilha 'BD' nao foi encontrada.", vbCritical
        Exit Sub
    End If
    
    Application.StatusBar = "Verificando dados... Por favor, aguarde."
    
    For i = 2 To 10000
        ' Aplica a mesma limpeza que a macro principal faria
        valorLimpo = Trim(Application.WorksheetFunction.Clean(ws.Cells(i, 2).Value))
        
        If valorLimpo = "BRUNA SOUZA" Then
            Application.StatusBar = False
            MsgBox "SUCESSO! Encontrada correspondencia exata para 'BRUNA SOUZA' na linha " & i & ".", vbInformation, "Verificacao Concluida"
            Exit Sub
        End If
        
        ' Para nao percorrer linhas vazias desnecessariamente
        If ws.Cells(i, 1).Value = "" And ws.Cells(i + 1, 1).Value = "" Then
            Exit For
        End If
    Next i
    
    Application.StatusBar = False
    MsgBox "FALHA. A verificacao percorreu 10.000 linhas e NAO encontrou uma correspondencia para 'BRUNA SOUZA' na coluna B, mesmo apos a limpeza dos dados.", vbCritical, "Verificacao Falhou"
End Sub

Private Function RemoverAcentos(ByVal texto As String) As String
    ' Metodo final e definitivo, usando codigos Unicode (AscW) para ser imune a bugs de codificacao do VBE.
    Dim resultado As String
    Dim i As Long
    Dim charAtual As String
    Dim codigoChar As Integer
    
    resultado = ""
    
    For i = 1 To Len(texto)
        charAtual = Mid(texto, i, 1)
        codigoChar = AscW(charAtual)
        
        Select Case codigoChar
            ' Maiusculas
            Case 193, 192, 194, 195, 196: resultado = resultado & "A" ' ÁÀÂÃÄ
            Case 201, 200, 202, 203: resultado = resultado & "E" ' ÉÈÊË
            Case 205, 204, 206, 207: resultado = resultado & "I" ' ÍÌÎÏ
            Case 211, 210, 212, 213, 214: resultado = resultado & "O" ' ÓÒÔÕÖ
            Case 218, 217, 219, 220: resultado = resultado & "U" ' ÚÙÛÜ
            Case 199: resultado = resultado & "C" ' Ç
            ' Minusculas
            Case 225, 224, 226, 227, 228: resultado = resultado & "a" ' áàâãä
            Case 233, 232, 234, 235: resultado = resultado & "e" ' éèêë
            Case 237, 236, 238, 239: resultado = resultado & "i" ' íìîï
            Case 243, 242, 244, 245, 246: resultado = resultado & "o" ' óòôõö
            Case 250, 249, 251, 252: resultado = resultado & "u" ' úùûü
            Case 231: resultado = resultado & "c" ' ç
            Case Else
                ' Se nao for um acento mapeado, mantem o caractere original
                resultado = resultado & charAtual
        End Select
    Next i
    
    RemoverAcentos = resultado
End Function


' --- MACRO PRINCIPAL DO DASHBOARD ---

Sub CriarDashboardDrogariaAraujo()

    ' --- 1. CONFIGURACAO INICIAL ---
    Dim wb As Workbook
    Dim wsBD As Worksheet
    Dim wsDashboard As Worksheet
    Dim ptCache1 As PivotCache, ptCache2 As PivotCache ' Cache independente para cada tabela
    Dim pt As PivotTable
    Dim ultLinha As Long
    Dim ultColuna As Long
    Dim FonteDados As Range
    Dim TabelaResumo As Range
    Dim chtObj As ChartObject
    Dim cht As Chart
    Dim rngDadosGrafico As Range
    Dim rngLabelsGrafico As Range
    
    Application.ScreenUpdating = False
    
    Set wb = ThisWorkbook
    On Error Resume Next
    Set wsBD = wb.Worksheets("BD")
    On Error GoTo 0
    
    If wsBD Is Nothing Then
        MsgBox "A planilha 'BD' nao foi encontrada. Verifique o nome da aba e tente novamente.", vbCritical, "Erro"
        Application.ScreenUpdating = True
        Exit Sub
    End If
    
    If wsBD.AutoFilterMode Then
        wsBD.AutoFilterMode = False
    End If
    
    Application.DisplayAlerts = False
    On Error Resume Next
    wb.Worksheets("Dashboard").Delete
    On Error GoTo 0
    Application.DisplayAlerts = True

    Set wsDashboard = wb.Worksheets.Add(After:=wsBD)
    wsDashboard.Name = "Dashboard"
    
    ' --- CRIAR COLUNA DE LIMPEZA TEMPORARIA ---
    ultLinha = wsBD.Cells(wsBD.Rows.Count, 1).End(xlUp).Row
    ultColuna = wsBD.Cells(1, wsBD.Columns.Count).End(xlToLeft).Column
    
    Dim colLimpeza As Long
    colLimpeza = ultColuna + 1
    
    wsBD.Cells(1, colLimpeza).Value = "Recrutador_Limpo"
    wsBD.Range(wsBD.Cells(2, colLimpeza), wsBD.Cells(ultLinha, colLimpeza)).FormulaR1C1 = "=TRIM(CLEAN(RC2))"
    wsBD.Columns(colLimpeza).Value = wsBD.Columns(colLimpeza).Value

    ' --- 2. PREPARACAO DOS DADOS E TABELA DINAMICA ---
    
    Set FonteDados = wsBD.Cells(1, 1).Resize(ultLinha, colLimpeza)

    ' Cria o PRIMEIRO Cache da Tabela Dinamica
    Set ptCache1 = wb.PivotCaches.Create(SourceType:=xlDatabase, SourceData:=FonteDados)
    
    ' Cria uma aba temporaria para a Tabela Dinamica
    Dim wsTemp As Worksheet
    Set wsTemp = wb.Worksheets.Add
    wsTemp.Visible = xlSheetVeryHidden ' Esconde a aba temporaria
    
    ' Cria a Tabela Dinamica na aba temporaria usando o Cache 1
    Set pt = ptCache1.CreatePivotTable(TableDestination:=wsTemp.Cells(1, 1), TableName:="TD_Vagas")

    ' --- 3. CONFIGURACAO DA TABELA DINAMICA ---
    With pt
        Dim pf As PivotField
        Dim pi As PivotItem

        ' --- FILTRO ROBUSTO PARA RECRUTADOR (METODO .Visible) ---
        Set pf = .PivotFields("Recrutador_Limpo")
        pf.Orientation = xlPageField
        pf.ClearAllFilters
        pf.EnableMultiplePageItems = True
        
        On Error Resume Next ' Ignora o erro se um item nao for encontrado ao tentar esconde-lo
        For Each pi In pf.PivotItems
            If pi.Name <> "BRUNA SOUZA" Then
                pi.Visible = False
            End If
        Next pi
        
        ' Verificacao de Erro: Se todos os itens foram escondidos, o item desejado nao existia no cache.
        If pf.VisibleItems.Count = 0 Then
            On Error GoTo 0
            Application.DisplayAlerts = False
            wsTemp.Delete: wsDashboard.Delete: wsBD.Columns(colLimpeza).Delete
            Application.DisplayAlerts = True: Application.ScreenUpdating = True
            MsgBox "ERRO AO FILTRAR: Nao foi possivel encontrar o recrutador 'BRUNA SOUZA' no Cache da Tabela Dinamica.", vbCritical, "Filtro Falhou"
            Exit Sub
        End If
        On Error GoTo 0

        ' --- FILTRO ROBUSTO PARA GRUPO ECONOMICO (METODO .Visible) ---
        Set pf = .PivotFields("Grupo Economico")
        pf.Orientation = xlPageField
        pf.ClearAllFilters
        pf.EnableMultiplePageItems = True

        On Error Resume Next
        For Each pi In pf.PivotItems
            If pi.Name <> "DROGARIA ARAUJO" Then
                pi.Visible = False
            End If
        Next pi
        
        ' Verificacao de Erro
        If pf.VisibleItems.Count = 0 Then
            On Error GoTo 0
            Application.DisplayAlerts = False
            wsTemp.Delete: wsDashboard.Delete: wsBD.Columns(colLimpeza).Delete
            Application.DisplayAlerts = True: Application.ScreenUpdating = True
            MsgBox "ERRO AO FILTRAR: Nao foi possivel encontrar o 'Grupo Economico' chamado 'DROGARIA ARAUJO' no Cache da Tabela Dinamica.", vbCritical, "Filtro Falhou"
            Exit Sub
        End If
        On Error GoTo 0
        
        ' Configura Linhas
        .PivotFields("Status da Vaga").Orientation = xlRowField
        ' .PivotFields("Descricao do Motivo").Orientation = xlRowField ' Removido para simplificar a tabela
        
        With .PivotFields("Dias em Aberto")
            .Orientation = xlDataField
            .Function = xlAverage
            .Name = "Media de Dias"
            .NumberFormat = "0"
        End With
        
        With .PivotFields("Dias em Aberto")
            .Orientation = xlDataField
            .Function = xlMin
            .Name = "Min Dias"
        End With
        
        With .PivotFields("Dias em Aberto")
            .Orientation = xlDataField
            .Function = xlMax
            .Name = "Max Dias"
        End With
        
        With .PivotFields("Status da Vaga")
            .Orientation = xlDataField
            .Function = xlCount
            .Name = "Qtd Vagas"
        End With
        
        .RowAxisLayout xlTabularRow
        .ShowDrillIndicators = False
        .PivotCache.Refresh
    End With
    
    DoEvents

    pt.TableRange1.Copy
    wsDashboard.Cells(3, 2).PasteSpecial Paste:=xlPasteValuesAndNumberFormats
    wsDashboard.Cells(3, 2).PasteSpecial Paste:=xlPasteColumnWidths
    Set TabelaResumo = wsDashboard.Cells(3, 2).CurrentRegion
    
    On Error Resume Next
    TabelaResumo.Rows("Grand Total").Delete
    Dim cel As Range
    For Each cel In TabelaResumo.Columns(1).Cells
        If InStr(1, cel.Value, "Total") > 0 Then
            cel.EntireRow.Delete
        End If
    Next cel
    On Error GoTo 0
    
    ' A aba temporaria NAO sera deletada aqui. Apenas no final.
    
    ' --- 4. FORMATACAO E CRIACAO DOS GRAFICOS ---
    
    wsDashboard.Cells(1, 2).Value = "Dashboard - Recrutadora: BRUNA SOUZA | Grupo: DROGARIA ARAUJO"
    wsDashboard.Cells(1, 2).Font.Bold = True
    wsDashboard.Cells(1, 2).Font.Size = 16
    
    Set rngLabelsGrafico = wsDashboard.Range("B4", wsDashboard.Cells(wsDashboard.Rows.Count, "B").End(xlUp))
    Set rngDadosGrafico = wsDashboard.Range("C4", wsDashboard.Cells(wsDashboard.Rows.Count, "C").End(xlUp)) ' Coluna ajustada de D para C
    
    Set chtObj = wsDashboard.ChartObjects.Add(Left:=50, Top:=TabelaResumo.Top + TabelaResumo.Height + 30, Width:=500, Height:=300)
    Set cht = chtObj.Chart
    With cht
        .ChartType = xlBarClustered
        .HasTitle = True
        .ChartTitle.Text = "Media de Dias em Aberto por Status"
        .SetSourceData Source:=Union(rngLabelsGrafico, rngDadosGrafico)
        .HasLegend = False
        .Axes(xlValue).HasTitle = True
        .Axes(xlValue).AxisTitle.Text = "Media de Dias"
    End With
    
    Set rngDadosGrafico = wsDashboard.Range("F4", wsDashboard.Cells(wsDashboard.Rows.Count, "F").End(xlUp)) ' Coluna ajustada de G para F
    
    Set chtObj = wsDashboard.ChartObjects.Add(Left:=600, Top:=chtObj.Top, Width:=500, Height:=300)
    Set cht = chtObj.Chart
    With cht
        .ChartType = xlColumnClustered
        .HasTitle = True
        .ChartTitle.Text = "Quantidade de Vagas por Status"
        .SetSourceData Source:=Union(rngLabelsGrafico, rngDadosGrafico)
        .HasLegend = False
    End With

    Dim pt2 As PivotTable
    Dim TabelaGrafico3 As Range

    ' CRIA UM SEGUNDO PIVOTCACHE INDEPENDENTE PARA A SEGUNDA TABELA
    Set ptCache2 = wb.PivotCaches.Create(SourceType:=xlDatabase, SourceData:=FonteDados)
    
    ' Cria a segunda Tabela Dinamica usando o Cache 2
    Set pt2 = ptCache2.CreatePivotTable(TableDestination:=wsDashboard.Range("J20"), TableName:="TD_Grafico3")
    With pt2
        .PivotFields("Status da Vaga").Orientation = xlRowField
        .PivotFields("Descricao do Motivo").Orientation = xlColumnField
        .PivotFields("Status da Vaga").Orientation = xlDataField
        .PivotFields("Status da Vaga").Name = "Contagem"
    End With

    DoEvents
    Set TabelaGrafico3 = pt2.TableRange1
    
    ' SOLUCAO: Redimensiona o intervalo de dados para excluir a linha e a coluna de "Total Geral"
    If pt2.RowGrand And pt2.ColumnGrand Then
        Set TabelaGrafico3 = TabelaGrafico3.Resize(TabelaGrafico3.Rows.Count - 1, TabelaGrafico3.Columns.Count - 1)
    ElseIf pt2.RowGrand Then
        Set TabelaGrafico3 = TabelaGrafico3.Resize(TabelaGrafico3.Rows.Count - 1)
    ElseIf pt2.ColumnGrand Then
        Set TabelaGrafico3 = TabelaGrafico3.Resize(, TabelaGrafico3.Columns.Count - 1)
    End If

    Set chtObj = wsDashboard.ChartObjects.Add(Left:=50, Top:=chtObj.Top + chtObj.Height + 30, Width:=1050, Height:=400)
    Set cht = chtObj.Chart
    With cht
        .SetSourceData Source:=TabelaGrafico3
        .ChartType = xlBarStacked100
        .HasTitle = True
        .ChartTitle.Text = "Composicao dos Motivos de Vaga por Status"
        .HasLegend = True
        .Legend.Position = xlBottom
    End With

    pt2.TableRange1.Font.Color = RGB(255, 255, 255)
    
    ' --- 5. FINALIZACAO ---
    ' ORDEM DE LIMPEZA FINAL E DEFINITIVA (A Prova de Falhas)
    
    ' PASSO 1 e 2 Removidos: O Grafico 3 e a Tabela Dinamica 2 nao serao mais excluidos.
    'On Error Resume Next
    'chtObj.Delete
    'On Error GoTo 0
    
    'On Error Resume Next
    'pt2.TableRange1.Delete
    'On Error GoTo 0
    
    ' PASSO 3 (CRUCIAL): Liberar todas as variaveis de objeto da memoria.
    ' Isso forca o Excel a "desconectar" as dependencias antes de deletar a planilha.
    Set cht = Nothing
    Set chtObj = Nothing
    Set pt = Nothing
    Set pt2 = Nothing
    Set ptCache1 = Nothing
    Set ptCache2 = Nothing

    ' PASSO 4: Excluir a planilha temporaria (wsTemp).
    ' Agora que todos os objetos foram liberados, a planilha pode ser deletada.
    Application.DisplayAlerts = False
    wsTemp.Delete
    Application.DisplayAlerts = True
    
    ' PASSO 5: Excluir a coluna de limpeza.
    wsBD.Columns(colLimpeza).Delete
    
    wsDashboard.Activate
    Application.ScreenUpdating = True
    
    MsgBox "Dashboard atualizado com sucesso!", vbInformation, "Concluido"

End Sub
