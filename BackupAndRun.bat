cd C:\Users\peter\PycharmProjects\DirectoryChangeNotifier
git pull
call Backup.bat

SET PYTHONPATH=
SET PYTHONHOME=
py DriveLookup.py %*
pause