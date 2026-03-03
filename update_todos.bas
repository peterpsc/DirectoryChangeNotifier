Public  gNotificationName As String
Public	gGroupDataPath As String
Public	gStatusReportPath As String
Public	gTestStatusReportPath As String
Public  gPythonPath As String
Public  gMasterWorkbookPath As String
Public  gUpdateBatchPath As String
Public  gToConvertPath As String

Sub InitializeGlobals()
    CheckFileExists(gToConvertPath)
    lines = GetFileLines(gToConvertPath)
    gNotificationName = lines(0)
    gGroupDataPath = lines(1)
	gStatusReportPath = lines(2)
	gTestStatusReportPath = lines(3)
    gPythonPath = lines(4)
    gMasterWorkbookPath = lines(5)
    gUpdateBatchPath = lines(6)
    gToConvertPath = lines(7)
End Sub

Function DoesFileExist(filePath)
    fileURL = ConvertToUrl(filePath)
    DoesFileExist = FileExists(fileURL)
End Function

Sub CheckFileExists(filePath)
    If not DoesFileExist(filePath) Then
        MsgBox "Missing: " & filePath, 48, "File Check Result"
    	End
    End If
End Sub

Sub	InitializeAllConverterPath(sName)
    converterTheRed = "Converter the Red.lst"
    deployedConverterPath = "G:\Shared drives\Exchequer Reporting\"
    if FileExists(deployedConverterPath) Then ' Deployed
        gToConvertPath = deployedConverterPath + converterTheRed
        if not DoesFileExist(gToConvertPath) Then
            print("Missing: " + converterPath)
        end if
    else: ' Test
        testConverterPath = "A:\East Kingdom Exchequer Test\Exchequer Reporting\"
        gToConvertPath = testConverterPath + converterTheRed
    End if
    InitializeGlobals(sName)
End Sub


Sub	InitializeGlobalResources()
    converterTheRed = "Converter the Red.lst"
    deployedConverterPath = "D:\yonay\PycharmProjects\DirectoryChangeNotifier\Resources\"

    if FileExists(deployedConverterPath) Then ' Deployed
        gToConvertPath = deployedConverterPath + converterTheRed
        if not DoesFileExist(gToConvertPath) Then
            print("Missing: " + gToConvertPath)
        end if
    else: ' Test
        testConverterPath =  "C:\Users\peter\PycharmProjects\DirectoryChangeNotifier\Resources\"
        gToConvertPath = testConverterPath + converterTheRed
    End if
    InitializeGlobals(Resources)
End Sub


Sub ConvertTest()
	InitializeGlobalResources()
	q4FilePaths = Array("A:\East Kingdom Exchequer Test\Other\2025\Quarterly Reports\Another Kingdom-Q4.xlsm")
	groupName = "Test"
	q1FilePaths = ConvertQ4s(q4FilePaths, "C:\Users\peter\PycharmProjects\DirectoryChangeNotifier\Test Data\", groupName)
	CreateGroupStatus(q1FilePaths, groupName)
End Sub

Sub ConvertResources()
	InitializeGlobalResources()
	ConvertQ1s("Resources")
End Sub

Sub ConvertSpecific()
	sName = "Specific"
	InitializeAllConverterPath(sName)
	ConvertQ1s(sName)
End Sub

Sub ConvertOther()
	sName = "Other"
	InitializeAllConverterPath(sName)
	ConvertQ1s(sName)
End Sub

Sub ConvertAll()
	sName = "All"
	InitializeAllConverterPath(sName)
	ConvertQ1s(sName)
End Sub

Sub ConvertQ1s(sName)
    Dim oCSV As Object, oCSVSheet As Object, oSheet As Object, oCell As Object
    Dim csvArgs(2) As New com.sun.star.beans.PropertyValue
    Dim iRow As Integer, convertedCount As Integer
    Dim sWorksheet As String, sCoord As String, sText As String
    Dim bRedoAll As Boolean

    converted_count = 0

    ' Configure and Open CSV
    csvArgs(0).Name = "FilterName" : csvArgs(0).Value = "Text - txt - csv (StarCalc)"
    csvArgs(1).Name = "FilterOptions" : csvArgs(1).Value = "44,34,76,1"
    csvArgs(2).Name = "Hidden" : csvArgs(2).Value = True

	Dim toConvertPath As String
	toConvertPath = gStatusReportPath + sName + gToConvertPath
	CheckFileExists(toConvertPath)

   	oCSV = StarDesktop.loadComponentFromURL(ConvertToURL(toConvertPath), "_blank", 0, csvArgs())
    oCSVSheet = oCSV.Sheets(0)

	If (Not GlobalScope.BasicLibraries.isLibraryLoaded("Tools")) Then
	    GlobalScope.BasicLibraries.LoadLibrary("Tools")
	End If

    iNumRows = GetLastRow(oCSVSheet)
    bRedoAll = iNumRows > 0

    ' Loop through CSV rows
    iRow = 1 'skip Column Names
    Do While oCSVSheet.getCellByPosition(0, iRow).String <> ""
        fromFileDir    = oCSVSheet.getCellByPosition(0, iRow).String
        toFileDir    = oCSVSheet.getCellByPosition(1, iRow).String
        toFileName    = oCSVSheet.getCellByPosition(2, iRow).String
        sDataPath = toFileDir + toFileName + ".csv"
       	sOutputPath = toFileDir + toFileName +  ".xlsx"
        success = RunWorkbookUpdate(sMasterPath, sDataPath, sOutputPath, bRedoAll)
		convertedCount = convertedCount + success
        iRow = iRow + 1
    Loop

    ' Close CSV immediately after data transfer
    oCSV.close(True)

    ' MsgBox "Converted " + convertedCount, 64, "Success"

    ' CloseGroupStatusReport(sName) ' # TODO FIX ME update as you go

    Dim oShell As Object
    Set oShell = CreateObject("WScript.Shell")
    oShell.CurrentDirectory = gPythonPath

    ' Syntax: .Run(Command, WindowStyle, WaitOnReturn)
    ' WindowStyle 1 = Normal, 0 = Hidden
    ' WaitOnReturn False = Don't wait for it to finish
    oShell.Run "cmd.exe /k " & gUpdateBatchPath, 1, False

    Wait 2000
End Sub


Function GetLastRow(oSheet As Object) As Long
    Dim oCursor As Object

    ' Create a cursor and move it to the very last used cell
    oCursor = oSheet.createCursor()
    oCursor.gotoEndOfUsedArea(False)

    ' Return the 0-based index of the last row
    ' If you want the "Count" (1-based), use: .EndRow + 1
    GetLastRow = oCursor.RangeAddress.EndRow
End Function

Function RunWorkbookUpdate(sMasterPath As String, sDataPath As String, sOutputPath As String, bRedoAll As Boolean) As Integer
    ' bRedoAll = True: if there is a .csv file, Convert it
    bDeleteAfterConvert = True  ' True will delete .csv after conversion

	RunWorkbookUpdate = 0
    Dim sOutputURL as String
    sOutputURL = ConvertToUrl(sOutputPath)

	Dim bOutputExists as Boolean, bDataExists as Boolean
	bOutputExists =  FileExists(sOutputPath)

	If bRedoAll or not bOutputExists then
		bDataExists =  FileExists(sDataPath)

		if not bDataExists then
			' print("Can't open " + sDataPath)
			Exit Function
		End If

	    Dim oDoc As Object

	  	oDoc = StarDesktop.loadComponentFromURL(ConvertToURL(gMasterWorkbookPath), "_blank", 0, Array())

	    success = ImportAndProcessCSV(oDoc, sDataPath)

	    if success then
	    	RunWorkbookUpdate = 1
		    SaveWorkbook(oDoc, sOutputURL)
			oDoc.close(True)

			sDataUrl = ConvertToURL(sDataPath)
			If bDeleteAfterConvert and FileExists(sDataUrl) Then
			    On Error Resume Next
			    Kill(sDataUrl)
			    If Err <> 0 Then
                    MsgBox "Cannot delete '" & sPath & "' because it is open in another program.", 48, "File Locked"
                    Err = 0 ' Reset the error object
                Else
                    ' Optional: Success message
                End If
			End If
		Else
		    oDoc.close(True)
	    End if
	End if
End Function

Sub SaveWorkbook(oTargetDoc As Object, sOutputURL As String)
    Dim args(1) As New com.sun.star.beans.PropertyValue

    args(0).Name = "Overwrite"
    args(0).Value = True

    ' Standard filter for .xlsx
    args(1).Name = "FilterName"
    args(1).Value = "Calc MS Excel 2007 XML"

    ' Use storeToURL to avoid "Save As" session conflicts on Shared Drives
    On Local Error GoTo ErrorHandler
    oTargetDoc.storeToURL(sOutputURL, args())
    Exit Sub

ErrorHandler:
    MsgBox "Error " & Err & ": " & Error$ & Chr(13) & "Path: " & sURL
End Sub

Function ImportAndProcessCSV(oTargetDoc As Object, sDataPath As String)
    ImportAndProcessCSV = False
    Dim oCSV As Object
    Dim csvArgs(2) As New com.sun.star.beans.PropertyValue

    ' Configure and Open CSV
    csvArgs(0).Name = "FilterName" : csvArgs(0).Value = "Text - txt - csv (StarCalc)"
    csvArgs(1).Name = "FilterOptions" : csvArgs(1).Value = "44,34,76,1,1/4,2/4,3/4,4/4,5/4"
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


    ImportAndProcessCSV = ProcessCSV(oCSV, oTargetDoc)

End Function

Function ProcessCSV(oCSV As Object, oTargetDoc As Object)
	TYPE_STRING   = "string"
	TYPE_FORMULA  = "formula"
	TYPE_CURRENCY = "currency"
	TYPE_DATE     = "date"
	TYPE_INTEGER  = "integer"
	TYPE_ZIP      = "zip"
	TYPE_STATE    = "state"

    ProcessCSV = False
    Dim oCSVSheet As Object, oSheet As Object, oCell As Object
    Dim iRow As Integer
    Dim sWorksheet As String, sCoord As String, sText As String
    Dim oProt As New com.sun.star.util.CellProtection
    Dim locked As Boolean, asString As Boolean

    oCSVSheet = oCSV.Sheets(0)

    ' Loop through CSV rows
    iRow = 1
    Do While oCSVSheet.getCellByPosition(0, iRow).String <> ""
        sWorksheet = oCSVSheet.getCellByPosition(0, iRow).String
        sCoord     = oCSVSheet.getCellByPosition(1, iRow).String
        sText      = oCSVSheet.getCellByPosition(2, iRow).String
       	if left(sText,1) = "'" then
        	sText = Mid(sText, 2)
        end if
        sType	   = LCase(oCSVSheet.getCellByPosition(3, iRow).String)
        sLocked	   = LCase(oCSVSheet.getCellByPosition(4, iRow).String)
        locked = False

        If sLocked = "true" Then locked = True

        If oTargetDoc.Sheets.hasByName(sWorksheet) Then
            oSheet = oTargetDoc.Sheets.getByName(sWorksheet)
            oCell = oSheet.getCellRangeByName(sCoord)
            if sType = TYPE_STRING or sType = TYPE_ZIP or sType = TYPE_STATE then
                oCell.String = sText
            else
                If sType = TYPE_FORMULA Then
                   	sText = RemoveOuterQuotes(sText)
                    oCell.Formula = sText
                else
	               	If sType = TYPE_CURRENCY then
	               		oCell.Value = Val(sText)
               		else
               			if  sType = TYPE_INTEGER then
               				Dim nInt As Long
    						nInt = CLng(sText)
   							oCell.Value = nInt
   							SetAndFormatInteger(oCell, sText)
               			else
			           		if sType = TYPE_DATE Then
			           		    SetAndFormatMMDDYYYY(oCell, sText)
	             		    Else
	         					print("Invalid Type: " + sType)
	              			End If
	              		End If
               		End If
               	End If
            End if
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
	sDataUrl = ConvertToUrl(sDataPath)
	If FileExists(sDataUrl) Then
    	Kill(sDataUrl)
    End If

    ProcessCSV = True

End Function

Sub SetAndFormatInteger(oTargetCell As Object, sValue As String)
    Dim nVal As Long
    Dim nKey As Long
    Dim sFormat As String : sFormat = "###0"
    Dim aLocale As New com.sun.star.lang.Locale

    ' 1. Safety Check: Only convert if it's actually a number
    If IsNumeric(sValue) Then
        nVal = CLng(sValue)
        oTargetCell.Value = nVal

        ' 2. Handle the NumberFormat logic
        nKey = ThisComponent.NumberFormats.queryKey(sFormat, aLocale, True)
        If nKey = -1 Then
            nKey = ThisComponent.NumberFormats.addNew(sFormat, aLocale)
        End If

        oTargetCell.NumberFormat = nKey
    Else
        ' If it's not a number, just put the text in the cell
        oTargetCell.String = sValue
    End If
End Sub

Sub SetAndFormatMMDDYYYY(oTargetCell As Object, sText As String)
    Dim dDate As Date
    Dim nKey As Long
    Dim sFormat As String : sFormat = "MM/DD/YYYY"
    Dim aLocale As New com.sun.star.lang.Locale
    Dim oFormats As Object

    If Trim(sText) = "" Or Not IsDate(sText) Then Exit Sub

    ' 2. Convert the "MM/DD/YYYY" string to a real Date value
    ' DateValue handles "MM/DD/YYYY" reliably in most locales
    dDate = DateValue(sText)
    oTargetCell.Value = dDate

    ' 3. Access the document's number format collection
    oFormats = ThisComponent.getNumberFormats()

    ' 4. Query or add the MM/DD/YYYY display format
    nKey = oFormats.queryKey(sFormat, aLocale, True)
    If nKey = -1 Then
        nKey = oFormats.addNew(sFormat, aLocale)
    End If

    ' 5. Apply the format ID to the cell
    oTargetCell.NumberFormat = nKey
End Sub

Function RemoveOuterQuotes(ByVal txt As String) As String
    Dim quote As String
    quote = Chr(34) ' Character code for double quote "

    If Left(txt, 1) = quote And Right(txt, 1) = quote Then
        RemoveOuterQuotes = Mid(txt, 2, Len(txt) - 2)
    Else
        RemoveOuterQuotes = txt
    End If
End Function

Sub CloseGroupStatusReport(sName)
    Dim oComponents As Object
    Dim oEnum As Object
    Dim oComp As Object
    Dim sTargetTitle As String

    sTargetTitle = sName + " Group Status.csv" ' The exact window title to look for

    ' 1. Get all open LibreOffice windows
    oComponents = StarDesktop.getComponents()
    oEnum = oComponents.createEnumeration()

    ' 2. Loop through open documents to find the match
    Do While oEnum.hasMoreElements()
        oComp = oEnum.nextElement()

        ' Check if the component is a spreadsheet and matches the title
        If oComp.supportsService("com.sun.star.sheet.SpreadsheetDocument") Then
            If oComp.Title = sTargetTitle Then
                oComp.close(True) ' Close it (True = deliver ownership)
                Exit Do ' Stop looking once found and closed
            End If
        End If
    Loop
End Sub

Sub RunDriveLookup()
    ' Path to the executable
    Dim sExePath As String
    dir = GetPythonDir()
    sExePath = dir +"DriveLookup.bat"

    ' Optional: Arguments for the program
    Dim sArgs As String
    sArgs = ""

    ' 1 = Normal window, True/False = Wait for it to finish
    Shell(sExePath, 1, sArgs, True)
End Sub

Function GetFileLines(ByVal sFileName As String) As Variant
    Dim iFileNum As Integer
    Dim sLine As String
    Dim aLines() As String
    Dim iCounter As Long

    iFileNum = FreeFile() ' Get available file handle
    iCounter = 0

    ' Open the file for reading
    Open ConvertToURL(sFileName) For Input As #iFileNum

    Do While Not EOF(iFileNum)
        Line Input #iFileNum, sLine
        ' Resize the array to hold the new line
        ReDim Preserve aLines(iCounter)
        aLines(iCounter) = sLine
        iCounter = iCounter + 1
    Loop

    Close #iFileNum

    ' Return the populated array
    GetFileLines = aLines()
End Function

Sub OpenGroupStatusReport(sName)
    sReportPath = GetGroupDataDir()
    sTargetTitle = sName + " Group Status.csv"
    sStatusReportFilePath = sReportPath + sTargetTitle
End Sub

Function GetOrOpenWorkbook(sFilePath As String) As Objectf '# TODO FIX ME
    Dim oComponents As Object, oEnum As Object, oComp As Object
    Dim sURL As String

    sURL = ConvertToURL(sFilePath)
    oComponents = StarDesktop.Components
    oEnum = oComponents.createEnumeration()

    ' 1. Search existing open workbooks
    Do While oEnum.hasMoreElements()
        oComp = oEnum.nextElement()
        ' Check if the component has a URL and if it matches
        If HasUnoInterfaces(oComp, "com.sun.star.frame.XModel") Then
            If oComp.URL = sURL Then
                GetOrOpenWorkbook = oComp
                Exit Function
            End If
        End If
    Loop

    ' 2. Open new one if not found
    Dim args(0) As New com.sun.star.beans.PropertyValue
    GetOrOpenWorkbook = StarDesktop.loadComponentFromURL(sURL, "_blank", 0, args())
End Function

Sub FindAndReplaceInRow(nSearchCol As Long, nReplaceCol As Long, sSearch As String, sReplaceValue As String) '# TODO FIX ME
    Dim oSheet As Object, oCellSearch As Object, oCellReplace As Object
    Dim iRow As Long
'
    oSheet = ThisComponent.CurrentController.ActiveSheet
    iRow = 0 ' Starting row

    Do
        oCellSearch = oSheet.getCellByPosition(nSearchCol, iRow)

        ' 1. Stop if we hit a blank cell
        If oCellSearch.Type = com.sun.star.table.CellContentType.EMPTY Then
            Print "Value not found before reaching a blank row."
            Exit Do
        End If

        ' 2. Check for match
        If oCellSearch.String = sSearch Then
            ' Get the cell in the same row but different column
            oCellReplace = oSheet.getCellByPosition(nReplaceCol, iRow)
            oCellReplace.String = sReplaceValue

            Print "Success: Updated Row " & (iRow + 1)
            Exit Do
        End If

        iRow = iRow + 1
    Loop
End Sub