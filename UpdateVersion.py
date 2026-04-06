import PrintHelper
from DirChangeNotifier import DirChangeNotifier

if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("UpdateVersion.py")
    dcn = DirChangeNotifier()
    dcn.update_version()
