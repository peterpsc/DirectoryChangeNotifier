import shutil
from os.path import exists
from typing import Any

import Persistence
from PrintHelper import print_red

EXCHEQUER_REPORTING = "Exchequer Reporting\\"

TEST_PATH = "A:\\East Kingdom Exchequer Test\\"
TEST_CONVERTER_PATH = f"{TEST_PATH}{EXCHEQUER_REPORTING}"

DEPLOYED_PATH = "G:\\Shared drives\\"
DEPLOYED_CONVERTER_PATH = f"{DEPLOYED_PATH}{EXCHEQUER_REPORTING}"

CONVERTER_THE_RED = "Converter the Red"

TEST = "Test"
DEPLOYED = "Deployed"
HOSTS = [TEST, DEPLOYED]

RESOURCES = "Resources"
DEPLOY_CONVERTER_THE_RED = True


def get_host_flavor(notification_name=None) -> tuple[Any, Any, Any, Any]:
    host_type, converter_path = get_host_type_converter_path(notification_name)

    converter_lines = Persistence.get_lines(converter_path, Persistence.FILE_PATH)
    group_data_path = converter_lines[0]
    status_report_path = converter_lines[1]
    test_status_report_path = converter_lines[2]
    return host_type, group_data_path, status_report_path, test_status_report_path

def get_host_type_converter_path(notification_name=None):
    if notification_name == RESOURCES:
        host = RESOURCES
        converter_path = Persistence.get_file_path(f"{CONVERTER_THE_RED} {RESOURCES}.lst", Persistence.RESOURCE_PATH)
    else:
        host = DEPLOYED
        if exists(DEPLOYED_CONVERTER_PATH):
            converter_path = f"{DEPLOYED_CONVERTER_PATH}{CONVERTER_THE_RED}.lst"
            if DEPLOY_CONVERTER_THE_RED:
                if not exists(converter_path):
                    print_red(f"Missing: {converter_path}")
                    ctr_deployed_path = Persistence.get_file_path(f"{CONVERTER_THE_RED} {host}.lst",
                                                                  Persistence.RESOURCE_PATH)
                    assert exists(ctr_deployed_path)
                    assert exists(DEPLOYED_CONVERTER_PATH)
                    shutil.copy(ctr_deployed_path, converter_path)
        else:
            host = TEST
            converter_path = f"{TEST_CONVERTER_PATH}{CONVERTER_THE_RED}.lst"
            if DEPLOY_CONVERTER_THE_RED:
                if not exists(converter_path):
                    print_red(f"Missing: {converter_path}")
                ctr_test_path = Persistence.get_file_path(f"{CONVERTER_THE_RED} {host}.lst", Persistence.RESOURCE_PATH)
                shutil.copy2(ctr_test_path, converter_path)
    return host, converter_path

def get_host_path(file_path, host):
    if file_path is None:
        return None
    if host == TEST:
        replace = file_path.replace(DEPLOYED_PATH, TEST_PATH)
    else:
        replace = file_path.replace(TEST_PATH, DEPLOYED_PATH)
    return replace


if __name__ == '__main__':
    host, group_data_path, status_report_path, test_status_report_path = get_host_flavor()
    print(f"  Host: {host}")
    print(f" Group: {group_data_path}")
    print(f"Status:  {status_report_path}")
    print(f"  Test: {test_status_report_path}")


