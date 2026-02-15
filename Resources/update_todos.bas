Sub ConvertAllQ1s
    Dim oCSV As Object, oCSVSheet As Object, oSheet As Object, oCell As Object
    Dim csvArgs(2) As New com.sun.star.beans.PropertyValue
    Dim iRow As Integer, convertedCount As Integer
    Dim sWorksheet As String, sCoord As String, sText As String
    Dim bRedoAll As Boolean

    bRedoAll = False
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

	    ' Loop through CSV rows
	    iRow = 0
	    Do While oCSVSheet.getCellByPosition(0, iRow).String <> ""
	        fromFileDir    = oCSVSheet.getCellByPosition(0, iRow).String
	        toFileDir    = oCSVSheet.getCellByPosition(1, iRow).String
	        toFileName    = oCSVSheet.getCellByPosition(2, iRow).String
	        sDataPath = toFileDir + toFileName + ".csv"
	       	sOutputPath = toFileDir + toFileName +  ".xlsx"
	        success = RunWorkbookUpdate(sMasterPath, sDataPath, sOutputPath)
			convertedCount = convertedCount + success
	        iRow = iRow + 1
	    Loop

    End If

    ' Close CSV immediately after data transfer
    oCSV.close(True)

    MsgBox "Converted " + convertedCount, 64, "Success"

    RefreshGroupStatus()
End Sub

Function RunWorkbookUpdate(sMasterPath As String, sDataPath As String, sOutputPath As String) As Integer
	RunWorkbookUpdate = 0
    Dim sOutputURL as String
    sOutputURL = ConvertToUrl(sOutputPath)

	Dim bOutputExists as Boolean, bDataExists as Boolean
	bOutputExists =  FileExists(sOutputPath)

	If not bOutputExists then
		bDataExists =  FileExists(sDataPath)

		if not bDataExists then
			print("Can't open " + sDataPath)
			Exit Function
		End If

	    Dim oDoc As Object

	    ' 1. Load the target XLSX
	  	oDoc = StarDesktop.loadComponentFromURL(ConvertToURL(sMasterPath), "_blank", 0, Array())

	    ' 2. Save as the destination file
	    SaveWorkbook(oDoc, sOutputURL)

	    ' 3. Delegate CSV handling entirely to the data sub
	    success = ImportAndProcessCSV(oDoc, sDataPath)

	    ' 4. Save as .xlsx
	    if success then
	    	RunWorkbookUpdate = 1
		    SaveWorkbook(oDoc, sOutputURL)
			oDoc.close(True)

			sDataUrl = ConvertToURL(sDataPath)
			If FileExists(sDataUrl) Then
			    Kill(sDataUrl)
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


    ImportAndProcessCSV = ProcessCSV(oCSV, oTargetDoc)

End Function

Function ProcessCSV(oCSV As Object, oTargetDoc As Object)
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
                If Left(sText, 1) = "=" Then
                    oCell.Formula = sText
                Else
                    oCell.String = sText
                End If
            else
            	oCell.Value = Val(sText)
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

Sub RefreshGroupStatus
    CloseGroupStatusReport()
    RunDriveLookup()
    OpenGroupStatusReport()
 End Sub

Sub CloseGroupStatusReport
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

Sub RunDriveLookup
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

Function GetPythonDir
    where = "g:\\ /S"
    'where = ReadStringFromFile("GoogleDrive_Path_Options.txt")

    GetPythonDir = None
    if where = "g:\\ /S" then
        GetPythonDir = "C:\Users\peter\PycharmProjects\DirectoryChangeNotifier\\"
    else
        GetPythonDir = "D:\yonay\PycharmProjects\DirectoryChangeNotifier\\"
    end if
End Function

Function GetGroupDataDir
    where = "g:\\ /S" ' local computer
    'where = ReadStringFromFile("GoogleDrive_Path_Options.txt")

    GetGroupDataDir = None
    if where = "g:\\ /S" then
        GetGroupDataDir = "A:/East Kingdom Exchequer Test/"	' local Computer
    else
    	GetGroupDataDir = "G:/My Drive/" 					' Remote Computer
    end if
End Function

Sub OpenGroupStatusReport
    sReportPath = GetGroupDataDir()
    sTargetTitle = "Group Status.csv"
    sStatusReportFilePath = sReportPath + sTargetTitle

End Sub

Sub RefreshGroupStatus2
    Dim sFileUrl As String
    Dim oDoc As Object
    Dim sBatchPath As String

    ' 1. Define the CSV File URL and Batch File Path
    ' Change "C:\path\to\" to the actual folder path
    sFileUrl = ConvertToURL("C:\path\to\Group Status.csv")
    sBatchPath = "C:\path\to\Update Group Status.bat"

    oDoc = ThisComponent

    ' 2. Close the CSV File
    If HasUnoInterfaces(oDoc, "com.sun.star.util.XCloseable") Then
        oDoc.close(True)
    Else
        oDoc.dispose()
    End If

    ' Optional: Wait for file handle to release
    Wait 1000

    ' 3. Execute the Batch File
    ' 1 = Normal window, True/False = Wait for it to finish
    Shell(sBatchPath, 1, sArgs, True)

    ' 4. Open the CSV file again
    Dim mArgs(0) As New com.sun.star.beans.PropertyValue
    mArgs(0).Name = "Hidden"
    mArgs(0).Value = False

    StarDesktop.loadComponentFromURL(sFileUrl, "_blank", 0, mArgs())
End Sub
