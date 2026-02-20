Sub ConvertAllQ1s()
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

	sReportPath = GetGroupDataDir()
    sToConvertPath = sReportPath + "To Convert.csv"

    If not FileExists(sToConvertPath) Then
        MsgBox "The file does not exist at: " & sToConvertPath, 48, "File Check Result"
    	Exit Sub
    Else
	   	oCSV = StarDesktop.loadComponentFromURL(ConvertToURL(sToConvertPath), "_blank", 0, csvArgs())
	    oCSVSheet = oCSV.Sheets(0)

	    sMasterPath = ReadStringFromFile(sReportPath + "EK Exchequer Master.txt")

		If (Not GlobalScope.BasicLibraries.isLibraryLoaded("Tools")) Then
		    GlobalScope.BasicLibraries.LoadLibrary("Tools")
		End If

        iNumRows = GetLastRow(oCSVSheet)
        bRedoAll = iNumRows > 0
	    ' Loop through CSV rows
	    iRow = 0
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

    End If

    ' Close CSV immediately after data transfer
    oCSV.close(True)

    ' MsgBox "Converted " + convertedCount, 64, "Success"

    CloseGroupStatusReport()

	Wait 2000

    Dim oShell As Object
    Set oShell = CreateObject("WScript.Shell")
    oShell.CurrentDirectory = "C:\Users\peter\PycharmProjects\DirectoryChangeNotifier"
    sBatchPath = """C:\Users\peter\PycharmProjects\DirectoryChangeNotifier\Update Group Status.bat"""

    ' Syntax: .Run(Command, WindowStyle, WaitOnReturn)
    ' WindowStyle 1 = Normal, 0 = Hidden
    ' WaitOnReturn False = Don't wait for it to finish
    oShell.Run "cmd.exe /k " & sBatchPath, 1, False

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
			print("Can't open " + sDataPath)
			Exit Function
		End If

	    Dim oDoc As Object

	  	oDoc = StarDesktop.loadComponentFromURL(ConvertToURL(sMasterPath), "_blank", 0, Array())

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

Sub SaveWorkbook(oTargetDoc As Object, sURL As String)
    ' We now need 2 properties: Overwrite and FilterName
    Dim args(1) As New com.sun.star.beans.PropertyValue

    ' Property 1: Overwrite existing files
    args(0).Name = "Overwrite"
    args(0).Value = True

    ' Property 2: Set the filter for Excel 2007+ (.xlsx)
    args(1).Name = "FilterName"
    args(1).Value = "Calc MS Excel 2007 XML"

    ' Save
    oTargetDoc.storeAsURL(sURL, args())
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
    Dim nDay As Integer, nMonth As Integer, nYear As Integer
    Dim dDate As Date
    Dim nKey As Long
    Dim sFormat As String : sFormat = "MM/DD/YYYY"
    Dim aLocale As New com.sun.star.lang.Locale

    If Len(sText) = 10 Then
        nMonth   = CInt(Mid(sText, 1, 2))
        nDay	 = CInt(Mid(sText, 4, 2))
        nYear  	 = CInt(Mid(sText, 7, 4))

        dDate = DateSerial(nYear, nMonth, nDay)
        oTargetCell.Value = dDate

        ' Apply the NumberFormat
        nKey = ThisComponent.NumberFormats.queryKey(sFormat, aLocale, True)
        If nKey = -1 Then
            nKey = ThisComponent.NumberFormats.addNew(sFormat, aLocale)
        End If
        oTargetCell.NumberFormat = nKey
    End If
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

Function ReadStringFromFile(filePath As String) As String
    Dim fileContent As String
    Dim fileNum As Integer
    Dim lineInput As String

    ' Ensure the path is in the correct URL format (e.g., "file:///C:/Users/user/data.txt")
    ' ConvertToURL is a useful function for this
    Dim fileURL As String
    fileURL = ConvertToURL(filePath)

    ' Get the next available free file handle number
    fileNum = FreeFile()

    ' Open the file for input
    Open fileURL For Input As #fileNum

    ' Read the file line by line until the end (EOF)
    Do While Not EOF(fileNum)
        Line Input #fileNum, lineInput
        fileContent = fileContent & lineInput & Chr(10) ' Concatenate the line and a newline character (Chr(10))
    Loop

    ' Close the file
    Close #fileNum

    ' Return the complete string, removing the trailing newline
    If Len(fileContent) > 0 Then
        ReadStringFromFile = Left(fileContent, Len(fileContent) - 1)
    Else
        ReadStringFromFile = ""
    End If
End Function

Sub RefreshGroupStatus()
    CloseGroupStatusReport()
    RunDriveLookup()
    OpenGroupStatusReport()
 End Sub

Sub CloseGroupStatusReport()
    Dim oComponents As Object
    Dim oEnum As Object
    Dim oComp As Object
    Dim sTargetTitle As String

    sTargetTitle = "Group Status.csv" ' The exact window title to look for

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

Function GetPythonDir()
    where = "g:\\ /S"
    'where = ReadStringFromFile("GoogleDrive_Path_Options.txt")

    GetPythonDir = None
    if where = "g:\\ /S" then
        GetPythonDir = "C:\Users\peter\PycharmProjects\DirectoryChangeNotifier\"
    else
        GetPythonDir = "D:\yonay\PycharmProjects\DirectoryChangeNotifier\"
    end if
End Function

Function GetGroupDataDir()
    GetGroupDataDir = ReadStringFromFile("G:/My Drive/East Kingdom Exchequer Drive.txt")
End Function

Sub OpenGroupStatusReport()
    sReportPath = GetGroupDataDir()
    sTargetTitle = "Group Status.csv"
    sStatusReportFilePath = sReportPath + sTargetTitle
End Sub

Sub ConvertAllQ4sToQ1s()
    ConvertAllQ1s()

    Dim sExePath As String
    exeDir = GetPythonDir()
    sExePath = exeDir +"Update Group Status.bat"

    Wait 500
    ThisComponent.close(True)

    Dim sCommand As String
    sCommand = "cmd /c start """" """ & sExePath & """"
    Shell(sCommand, 0)

End Sub