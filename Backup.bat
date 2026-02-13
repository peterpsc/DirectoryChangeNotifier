set base=A:\SourceCode
set from=C:\Users\peter\PycharmProjects
set to=%base%\PycharmProjects
xcopy "%from%\*.*" "%to%\*.*" /D /c /i /h /k /y /s /EXCLUDE:backup.exclude
rem xcopy "%to%\*.*" "%from%\*.*" /D /c /i /h /k /y /s /EXCLUDE:backup.exclude

