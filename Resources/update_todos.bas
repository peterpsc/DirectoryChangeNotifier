Sub UpdateTodos
    Dim oCSV As Object, oCSVSheet As Object, oSheet As Object, oCell As Object
    Dim csvArgs(2) As New com.sun.star.beans.PropertyValue
    Dim iRow As Integer
    Dim sWorksheet As String, sCoord As String, sText As String
    Dim bRedoAll As Boolean
    bRedoAll = True


    ' Configure and Open CSV
    csvArgs(0).Name = "FilterName" : csvArgs(0).Value = "Text - txt - csv (StarCalc)"
    csvArgs(1).Name = "FilterOptions" : csvArgs(1).Value = "44,34,76,1"
    csvArgs(2).Name = "Hidden" : csvArgs(2).Value = True

    sDataPath = "g:/My Drive/Todos.csv"
    oCSV = StarDesktop.loadComponentFromURL(ConvertToURL(sDataPath), "_blank", 0, csvArgs())
    oCSVSheet = oCSV.Sheets(0)

    sMasterPath = "D:/yonay/PycharmProjects/DirectoryChangeNotifier/Resources/SCA Exchequer Report - 2026-03.xlsx"
'    sMasterPath = "C:/Users/peter/PycharmProjects/DirectoryChangeNotifier/Resources/SCA Exchequer Report - 2026-03.xlsx"

	If (Not GlobalScope.BasicLibraries.isLibraryLoaded("Tools")) Then
	    GlobalScope.BasicLibraries.LoadLibrary("Tools")
	End If

    ' Loop through CSV rows
    iRow = 0
    Do While oCSVSheet.getCellByPosition(0, iRow).String <> ""
        toFileDir    = oCSVSheet.getCellByPosition(1, iRow).String
        sDataPath = toFileDir + "\" + oCSVSheet.getCellByPosition(2, iRow).String +  oCSVSheet.getCellByPosition(3, iRow).String + ".csv"
       	sOutputPath = toFileDir + "\TEST " + oCSVSheet.getCellByPosition(2, iRow).String +  oCSVSheet.getCellByPosition(3, iRow).String + ".xlsx"
        RunWorkbookUpdate(sMasterPath, sDataPath, sOutputPath, bRedoAll)
        iRow = iRow + 1
    Loop

    ' Close CSV immediately after data transfer
    oCSV.close(True)

    print "Done"
End Sub


Sub UpdateTowers
    sMasterPath = "C:/Users/peter/PycharmProjects/DirectoryChangeNotifier/Resources/SCA Exchequer Report - 2026-03.xlsx"
    sDataPath = "C:/Users/peter/PycharmProjects/DirectoryChangeNotifier/Resources/2026 Q1 Canton of the Towers.csv"
    sOutputPath = "C:/Users/peter/PycharmProjects/DirectoryChangeNotifier/Resources/2026 Q1 Canton of the Towers.xlsx"
    RunWorkbookUpdate(sMasterPath, sDataPath, sOutputPath)
End Sub


Sub RunWorkbookUpdate(sMasterPath As String, sDataPath As String, sOutputPath As String, bRedo As Boolean)
    Dim outputURL as String
    outputURL = ConvertToUrl(sOutputPath)

    If not FileExists(outputURL) or bRedo then
	    Dim oDoc As Object
	    Dim saveArgs(0) As New com.sun.star.beans.PropertyValue

	    ' 1. Load the target XLSX
	    oDoc = StarDesktop.loadComponentFromURL(ConvertToURL(sMasterPath), "_blank", 0, Array())

	    ' 2. Delegate CSV handling entirely to the data sub
	    success = ImportAndProcessCSV(oDoc, sDataPath)

	    ' 3. Save as .xlsx
	    if success then
		    saveArgs(0).Name = "FilterName"
		    saveArgs(0).Value = "Calc MS Excel 2007 XML"
		    oDoc.storeAsURL(outputURL, saveArgs())

		    oDoc.close(True)

		    sDataUrl = ConvertToUrl(sDataPath)
		    If FileExists(sDataUrl) Then
	        	Kill(sDataUrl)
	        End If
	    End if
	End If
End Sub


Function ImportAndProcessCSV(oTargetDoc As Object, sDataPath As String)
    Dim oCSV As Object, oCSVSheet As Object, oSheet As Object, oCell As Object
    Dim csvArgs(2) As New com.sun.star.beans.PropertyValue
    Dim iRow As Integer
    Dim sWorksheet As String, sCoord As String, sText As String
    Dim oProt As New com.sun.star.util.CellProtection
    ImportAndProcessCSV = False

    ' Configure and Open CSV
    csvArgs(0).Name = "FilterName" : csvArgs(0).Value = "Text - txt - csv (StarCalc)"
    csvArgs(1).Name = "FilterOptions" : csvArgs(1).Value = "44,34,76,1,0,0,false,true,true,false"
    csvArgs(2).Name = "Hidden" : csvArgs(2).Value = True

	oSheets = oTargetDoc.Sheets
	oSheet = oSheets.getByName("Summary")
	oTargetDoc.CurrentController.setActiveSheet(oSheet)

    sDataURL = ConvertToURL(sDataPath)
    oCSV = StarDesktop.loadComponentFromURL(sDataURL, "_blank", 0, csvArgs())
    if oCSV is Nothing    	then
    	print "Could NOT Open " + sDataPath
    	Exit Function
    end if

    oCSVSheet = oCSV.Sheets(0)

    ' Loop through CSV rows
    iRow = 1
    Do While oCSVSheet.getCellByPosition(0, iRow).String <> ""
        sWorksheet = oCSVSheet.getCellByPosition(0, iRow).String
        sCoord     = oCSVSheet.getCellByPosition(1, iRow).String
        sText      = oCSVSheet.getCellByPosition(2, iRow).String
        sLocked	   = LCase(oCSVSheet.getCellByPosition(3, iRow).String)
        locked = False
        If sLocked = "true" Then locked = True

        If oTargetDoc.Sheets.hasByName(sWorksheet) Then
            oSheet = oTargetDoc.Sheets.getByName(sWorksheet)
            oCell = oSheet.getCellRangeByName(sCoord)
            oCell.String = sText
       '     if locked Then
       '     	oProtection.IsLocked = True
    '			oCell.CellProtection = oProtection
	'		    ' Pass an empty string if no password is desired
	'		    oSheet.protect("unlock")
	'		End If
        End If
        iRow = iRow + 1
    Loop

    ' Close CSV immediately after data transfer
    oCSV.close(True)

    ImportAndProcessCSV = True
End Function