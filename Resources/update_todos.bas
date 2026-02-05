Sub UpdateTodos
    Dim oCSV As Object, oCSVSheet As Object, oSheet As Object, oCell As Object
    Dim csvArgs(2) As New com.sun.star.beans.PropertyValue
    Dim iRow As Integer
    Dim sWorksheet As String, sCoord As String, sText As String
    Dim bRedoAll As Boolean
    bRedoAll = False


    ' Configure and Open CSV
    csvArgs(0).Name = "FilterName" : csvArgs(0).Value = "Text - txt - csv (StarCalc)"
    csvArgs(1).Name = "FilterOptions" : csvArgs(1).Value = "44,34,76,1"
    csvArgs(2).Name = "Hidden" : csvArgs(2).Value = True

    sDataPath = "g:/My Drive/Todos.csv"
    oCSV = StarDesktop.loadComponentFromURL(ConvertToURL(sDataPath), "_blank", 0, csvArgs())
    oCSVSheet = oCSV.Sheets(0)

'    sMasterPath = "D:/yonay/PycharmProjects/DirectoryChangeNotifier/Resources/SCA Exchequer Report - 2026-03.xlsx"
'    sMasterPath = "C:/Users/peter/PycharmProjects/DirectoryChangeNotifier/Resources/SCA Exchequer Report - 2026-03.xlsx"
    sMasterPath = ReadStringFromFile("g:/My Drive/EK Exchequer Master.txt")

	If (Not GlobalScope.BasicLibraries.isLibraryLoaded("Tools")) Then
	    GlobalScope.BasicLibraries.LoadLibrary("Tools")
	End If

    ' Loop through CSV rows
    iRow = 1
    Do While oCSVSheet.getCellByPosition(0, iRow).String <> ""
        toFileDir    = oCSVSheet.getCellByPosition(3, iRow).String
        sDataPath = toFileDir + "\" + oCSVSheet.getCellByPosition(4, iRow).String +  oCSVSheet.getCellByPosition(5, iRow).String + ".csv"
       	sOutputPath = toFileDir + "\TEST " + oCSVSheet.getCellByPosition(4, iRow).String +  oCSVSheet.getCellByPosition(5, iRow).String + ".xlsx"
        RunWorkbookUpdate(sMasterPath, sDataPath, sOutputPath, bRedoAll)
        iRow = iRow + 1
    Loop

    ' Close CSV immediately after data transfer
    oCSV.close(True)

	MsgBox "Done", 64, "Success"
End Sub

Sub RunWorkbookUpdate(sMasterPath As String, sDataPath As String, sOutputPath As String, bRedo As Boolean)
    Dim sOutputURL as String
    sOutputURL = ConvertToUrl(sOutputPath)

    If not FileExists(sOutputURL) or bRedo then
	    Dim oDoc As Object

	    ' 1. Load the target XLSX
	  	oDoc = StarDesktop.loadComponentFromURL(ConvertToURL(sMasterPath), "_blank", 0, Array())

	    ' 2. Save as the destination file
	    SaveWorkbook(oDoc, sOutputURL)

	    ' 3. Delegate CSV handling entirely to the data sub
	    success = ImportAndProcessCSV(oDoc, sDataPath)

	    ' 4. Save as .xlsx
	    if success then
		    SaveWorkbook(oDoc, sOutputURL)

		    oDoc.close(True)

		    sDataUrl = ConvertToUrl(sDataPath)
		    If FileExists(sDataUrl) Then
	        	Kill(sDataUrl)
	        End If
	    End if
	End If
End Sub

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
        sAsString  = LCase(oCSVSheet.getCellByPosition(3, iRow).String)
        sLocked	   = LCase(oCSVSheet.getCellByPosition(4, iRow).String)
        asString = False
        If sAsString = "true" then asString = True
        locked = False
        If sLocked = "true" Then locked = True

        If oTargetDoc.Sheets.hasByName(sWorksheet) Then
            oSheet = oTargetDoc.Sheets.getByName(sWorksheet)
            oCell = oSheet.getCellRangeByName(sCoord)
            if asString then
            	oCell.String = sText
            else
            	oCell.Value = Val(sText)
            endif
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