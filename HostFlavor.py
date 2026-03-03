import shutil
from os.path import exists
from typing import Any

import Persistence
from PrintHelper import print_red

CONVERTER_THE_RED = "Converter the Red"
TEST = "Test"
DEPLOYED = "GoogleDrive"
RESOURCES = "Resources"
DEPLOY_CONVERTER_THE_RED = True


def get_host_flavor(notification_name=None) -> tuple[Any, Any, Any, Any]:
    if notification_name == RESOURCES:
        host = RESOURCES
        converter_path = Persistence.get_file_path(f"{CONVERTER_THE_RED} {RESOURCES}.lst", Persistence.RESOURCE_PATH)
    else:
        host = DEPLOYED
        deployed_converter_path = "G:\\Shared drives\\Exchequer Reporting\\"
        if exists(deployed_converter_path):
            converter_path = f"{deployed_converter_path}{CONVERTER_THE_RED}.lst"
            if DEPLOY_CONVERTER_THE_RED:
                if not exists(converter_path):
                    print_red(f"Missing: {converter_path}")
                ctr_deployed_path = Persistence.get_file_path(f"{CONVERTER_THE_RED} {notification_name}.lst",
                                                              Persistence.RESOURCE_PATH)
                shutil.copy2(ctr_deployed_path, converter_path)
        else:
            host = TEST
            test_converter_path = "A:\\East Kingdom Exchequer Test\\Exchequer Reporting\\"
            converter_path = f"{test_converter_path}{CONVERTER_THE_RED}.lst"
            if DEPLOY_CONVERTER_THE_RED:
                if not exists(converter_path):
                    print_red(f"Missing: {converter_path}")
                ctr_test_path = Persistence.get_file_path(f"{CONVERTER_THE_RED} {host}.lst", Persistence.RESOURCE_PATH)
                shutil.copy2(ctr_test_path, converter_path)

    converter_lines = Persistence.get_lines(converter_path, Persistence.FILE_PATH)
    group_data_path = converter_lines[0]
    status_report_path = converter_lines[1]
    test_status_report_path = converter_lines[2]
    return host, group_data_path, status_report_path, test_status_report_path


if __name__ == '__main__':
    notification_name, group_data_path, status_report_path, test_status_report_path = get_host_flavor()
    print(f"  Host: {notification_name}")
    print(f" Group: {group_data_path}")
    print(f"Status:  {status_report_path}")
    print(f"  Test: {test_status_report_path}")
