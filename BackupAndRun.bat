cd C:\Users\peter\PycharmProjects\DirectoryChangeNotifier
git pull
call Backup.bat

SET "MY_PYTHON=C:\Users\peter\AppData\Local\Programs\Python\Python314\python.exe"
SET PYTHONPATH=
SET PYTHONHOME=
"%MY_PYTHON%" "C:\Users\peter\PycharmProjects\DirectoryChangeNotifier\DriveLookup.py" %*
pause