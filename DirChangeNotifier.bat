cd C:\Users\peter\PycharmProjects\DirectoryChangeNotifier
git pull
xcopy A:\SourceCode\PycharmProjects\DirectoryChangeNotifier\Private\*.* .\Private /D /c /i /h /k /y /EXCLUDE:backup.exclude

py DirChangeNotifier.py

xcopy .\Private\*.* A:\SourceCode\PycharmProjects\DirectoryChangeNotifier\Private\ /D /c /i /h /k /y /EXCLUDE:backup.exclude
pause
