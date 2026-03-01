import shutil
from os.path import exists
from typing import Any

import Persistence
from PrintHelper import print_red

CONVERTER_THE_RED = "Converter the Red"


def getHostFlavor() -> tuple[Any, Any, Any]:
    deployed_converter_path = "G:\\Shared drives\\Exchequer Reporting\\"
    if exists(deployed_converter_path):  # Deployed
        converter_path = f"{deployed_converter_path}{CONVERTER_THE_RED}.lst"
        if not exists(converter_path):
            print_red(f"Missing: {converter_path}")
            ctr_deployed_path = f"D:\\yonay\\PycharmProjects\\DirectoryChangeNotifier\\Resources\\{CONVERTER_THE_RED} Deployed.lst"
            shutil.copy2(ctr_deployed_path, converter_path)
    else:
        test_converter_path = "A:\\East Kingdom Exchequer Test\\Exchequer Reporting\\"
        converter_path = f"{test_converter_path}{CONVERTER_THE_RED}.lst"
        if not exists(converter_path):
            print_red(f"Missing: {converter_path}")
            ctr_test_path = f"C:\\Users\\peter\\PycharmProjects\\DirectoryChangeNotifier\\Resources\\{CONVERTER_THE_RED} Test.lst"
            shutil.copy2(ctr_test_path, converter_path)

    converter_lines = Persistence.get_lines(converter_path, Persistence.FILE_PATH)
    notification_name = converter_lines[0]
    group_data_path = converter_lines[1]
    status_report_path = converter_lines[2]
    return group_data_path, notification_name, status_report_path
