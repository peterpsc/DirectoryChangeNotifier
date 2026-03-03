import os
import shutil
import sys
from os.path import exists
from pathlib import Path
from typing import Any

from colorama import Fore

import GroupFields
import Persistence
import PlaySound
import PrintHelper
from Converter import (Converter, THIS_YEAR_PREFIX, QUARTERLY_REPORTS)
from DirChangeNotifier import DirChangeNotifier
from GroupFields import (FULL_GROUP_NAME, GROUP_DIR, GROUP_TYPE, Q4_PATH, Q1_PATH, NOTE, E_REGION, LOCATION)
from GroupFields import (LAST_YEAR, LAST_YEAR_DIR, THIS_YEAR, THIS_YEAR_DIR)
from GroupFields import OTHER, ALL
from HostFlavor import get_host_flavor
from PrintHelper import print_red

#
TO_CONVERT = "TO CONVERT"
OUT_OF_BALANCE = "OUT OF BALANCE"
NEGATIVE_REPORT = "NEGATIVE REPORT"
MISSING = "MISSING"

# Which groups to Show Status
SPECIFIC = "Specific"

TIR_MARA = "Tir Mara"
NORTHEAST = "Northeast"
NORTHERN = "Northern"
CENTRAL = "Central"
SOUTHERN = "Southern"
WESTERN = "Western"


def get_DirChangeNotifier() -> DirChangeNotifier:
    dcn = DirChangeNotifier()
    return dcn


dcn = get_DirChangeNotifier()

REGIONS = [TIR_MARA, NORTHERN, CENTRAL, SOUTHERN, WESTERN, NORTHEAST]

PROCESS_SPECIFIC = ["Havre des Glaces"]
PROCESS_SPECIFIC = dcn.append_group_names(PROCESS_SPECIFIC, ["Malagentia"])
PROCESS_SPECIFIC = ["Glenn Linn", "An Dubhaigeainn", "Buckland Cross"]
PROCESS_SPECIFIC = ["Carillion"]
PROCESS_SPECIFIC = ["Havre des Glaces", "Ruantallan", "Towers", "Quintavia", "Another Group"]
PROCESS_SPECIFIC = ["Concordia of the Snows"]
PROCESS_SPECIFIC = ["Carolingia", "Iron Bog"]

PROCESS_SPECIFIC = TIR_MARA
PROCESS_SPECIFIC = OTHER
PROCESS_NAME = TIR_MARA

PROCESS_SPECIFIC = None


PROCESS_SPECIFIC = ["Hadchester", "Giggleswick", "Ravensbridge", "Panther Vale", "Gryphonwald", "Hawkes Reache",
                    "EK College of Performers", "Hartshorn-dale", "Montevale", "Bergental"]
PROCESS_SPECIFIC = ["Panther Vale", "Lions End"]

PROCESS_NAME = OTHER

PROCESS_SPECIFIC = ["Dragonship Haven"]

if PROCESS_NAME == OTHER:
    PROCESS_SPECIFIC = [OTHER]

PROCESS_SPECIFIC = ["Østgarðr"]
PROCESS_SPECIFIC = ["Settmour Swamp"]

PROCESS_NAME = SPECIFIC
PROCESS_SPECIFIC = ["Mountain Freehold"]

PROCESS_SPECIFIC = None
PROCESS_NAME = ALL

COPY_A_TO_G = False
DELETE_ALL_Q1 = False  # Should mostly be False, tries to delete them q4_file_paths, but if they are open, keep them
DELETE_ALL_Q1_DATA = True  # keep True
DEBUG = True
SKIP_Q1_DATA_IF_Q1_EXISTS = True
if PROCESS_SPECIFIC:
    SKIP_Q1_DATA_IF_Q1_EXISTS = len(PROCESS_SPECIFIC) > 2  # False = Recreate Q1 Data anyway

GROUP_STATUS = " Group Status.csv"

# Creates:
# Group Status.csv
# To Convert.csv
def init_drive_lookup():
    driveLU = DriveLookup()
    driveLU.init_region_group_names()
    driveLU.init_all_group_names()
    if DEBUG:
        driveLU.check_group_regions()

    return driveLU


class DriveLookup:
    region_group_names = {}

    def __init__(self, notification_name=None):
        self.notification_name = notification_name
        host, self.group_data_path, self.status_report_path, self.test_status_report_path = get_host_flavor(
            notification_name)
        if notification_name is None:
            self.notification_name = host
        self.last_year_dirs = self.get_last_year_dirs()
        self.group_names = {}  # fields

    def get_last_year_dirs(self):
        all_directories = dcn.all_directories
        filtered_directories = []
        last_year_quarterly_reports = f"\\{LAST_YEAR}\\Quarterly Reports"
        for directory in all_directories:
            if last_year_quarterly_reports in directory:
                filtered_directories.append(directory)

        last_year_dirs = self.remove_extra_directories(filtered_directories)
        return last_year_dirs

    def get_old_file_path_new_dir(self, folder, file_name):
        old_file_path = f'{folder}{file_name}'
        new_dir = GroupFields.get_q1_path_from_q4_file_path(folder)
        this_year_dirs_split = new_dir.split("\\")
        group_name = this_year_dirs_split[- 4]
        fields = {}
        group_name, fields = GroupFields.GroupFields.lookup_group_fields(group_name, new_dir, fields)
        full_group_name = GroupFields.get_field(fields, FULL_GROUP_NAME)
        new_file_name = f"{THIS_YEAR_PREFIX}{full_group_name}"
        return old_file_path, new_dir, new_file_name

    def init_region_group_names(self):
        for region in REGIONS:
            self.region_group_names[region] = dcn.get_region_group_names(region)
            # for group_name in self.region_group_names[region]:
            #     GroupFields.GroupFields.append_ek_group_name(group_name)

    def init_all_group_names(self):
        self.group_names = {}

        for last_year_dir in self.last_year_dirs:
            fields = {}
            group_name, fields = self.get_group_fields(last_year_dir, fields)
            if fields and group_name:
                self.group_names[group_name] = fields

    def set_field(self, group_name, field_name, field_value):
        self.group_names[group_name][field_name] = field_value

    def get_field(self, group_name, field_name):
        return self.group_names[group_name][field_name]

    def init_category_groups(self, category, group_names):
        self.category_group_names[category] = group_names

    def remove_extra_directories(self, filtered_directories):
        extra_directories = []
        unwanted_directories = []
        for directory in filtered_directories:
            group_path_qr_extra = directory.partition(f"\\{QUARTERLY_REPORTS}")
            extra = directory.split("\\")
            if len(extra):
                extra_dir = extra[-1]
                if extra_dir != QUARTERLY_REPORTS:
                    if "4" in extra_dir and "Q" in extra_dir:
                        extra_directories.append(f"{group_path_qr_extra[0]}\\{QUARTERLY_REPORTS}")
                    else:
                        unwanted_directories.append(directory)
        actual_directories = []
        for directory in filtered_directories:
            if directory in unwanted_directories:
                continue
            if directory not in extra_directories:
                actual_directories.append(directory)

        return actual_directories

    def find_all_q4s_missing_todos(self, group_names, status_report_name):
        q4_paths = []
        q4_file_paths = []
        missing = []
        todos = []

        for group_name in group_names:
            q4_path = self.group_names[group_name][Q4_PATH]
            if status_report_name == OTHER:  # TODO FIX ME
                for q4_file_name in os.listdir(q4_path):
                    q4_file_path = os.path.join(q4_path, q4_file_name)
                    if os.path.isfile(q4_file_path):
                        self.append_q4_missing_todos(q4_path, q4_file_name, q4_paths, q4_file_paths, missing, todos,
                                                     status_report_name)
            else:
                q4_file_name = self.find_q4_file_name(q4_path)
                self.append_q4_missing_todos(q4_path, q4_file_name, q4_paths, q4_file_paths, missing, todos,
                                             status_report_name)

        return q4_paths, q4_file_paths, missing, todos

    def append_q4_missing_todos(self, q4_path, q4_file_name, q4_paths, q4_file_paths, missing, todos,
                                status_report_name):
        q4_paths.append(q4_path)
        if q4_file_name:
            q4_file_path, q1_path, q1_stem = self.get_old_file_path_new_dir(q4_path, q4_file_name)
            q4_file_paths.append(q4_file_path)
            new_dir_exists = exists(q1_path)
            if not new_dir_exists:
                os.makedirs(q1_path)

            q1_file_path = f"{q1_path}{q1_stem}.xlsx"
            if exists(q1_file_path):
                if SKIP_Q1_DATA_IF_Q1_EXISTS:
                    print(f"{q1_stem}.xlsx already exists - Skipping")
                    return

            if status_report_name == OTHER:
                print(f"{q4_file_name} - To Convert")
            else:
                print(f"{q1_file_path} - To Convert")
            todo = [q4_file_path, q1_path, q1_stem]
            todos.append(todo)
        else:
            missing.append(q4_path)
            print(f"{q4_path} - {MISSING}")

    @staticmethod
    def find_q4_file_name(folder):
        paths = sorted(Path(folder).iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
        found = False
        file_name = None
        for path in paths:
            if path.is_file():  # filter out directories
                file_name = path.name
                if (not file_name.endswith(".xlsm")
                        and not file_name.endswith(".xlsx")
                        or file_name.startswith("~")):
                    continue
                if "Q4" in file_name or "4Q" in file_name or "EOY" in file_name or "4th" in file_name or "Quarter 4" in file_name:
                    return file_name
        return None

    @staticmethod
    def get_other_q1_file(q4_file_path, q1_stem):
        q4_file_name = os.path.basename(q4_file_path)
        q1_file_name = q1_stem.partition(OTHER)[0] + q4_file_name
        return q1_file_name

    @staticmethod
    def create_convert_data(formatted_rows, todos, name):
        for todo in todos:
            if name in GroupFields.READ_FROM_FILE_NAMES:
                formatted_row = [todo[0], todo[1], DriveLookup.get_other_q1_file(todo[0], todo[2])]
            else:
                formatted_row = [todo[0], todo[1], todo[2]]

            formatted_rows.append(formatted_row)


    def save_to_convert(self, to_convert, name):
        file_name = f"{name} To Convert.csv"
        to_convert_file_path = Persistence.get_file_path(f"{self.status_report_path}{file_name}", Persistence.FILE_PATH)
        if not to_convert:
            Persistence.remove_file(to_convert_file_path)
            return

        data = []
        column_names = ["Q4 File Path", "Q1 Path", "Q1 File Name"]
        data.append(column_names)
        self.create_convert_data(data, to_convert, name)
        Persistence.save_list(data, to_convert_file_path, Persistence.FILE_PATH)

    @classmethod
    def fix_slashes(cls, file_path):
        result = file_path.replace('\\', '/')
        return result

    def process_todos(self, todos):
        to_convert = []
        out_of_balance = []
        negative_reports = []
        bugs = {}
        q4_fields = {}
        for todo in todos:
            q4_file_path = todo[0]
            q1_path = todo[1]
            group_name, fields = self.get_group_fields(q4_file_path)
            q4_file_name = os.path.basename(q4_file_path)
            q4_fields[q4_file_name] = fields
            converter = Converter(q4_file_path, q1_path, group_name, fields)
            if converter.error:
                bugs[q4_file_path] = converter.error
            else:
                balanced, negative = converter.is_balanced_or_negative()
                if balanced:
                    bug = converter.save_new_data()
                    if bug:
                        bugs[todo[0]] = bug
                    else:
                        to_convert.append(todo)
                elif negative:
                    negative_reports.append(q4_file_path)
                else:
                    out_of_balance.append(q4_file_path)

        return to_convert, out_of_balance, negative_reports, bugs, q4_fields

    def delete_all_q1_test_workbooks(self, groups, delete_q1=False, delete_q1_data=False):
        if delete_q1 == False and delete_q1_data == False:
            return

        for group_name in groups:
            group_fields = self.group_names[group_name]
            this_year_path = GroupFields.get_field(group_fields, Q1_PATH)
            if not exists(this_year_path):
                group_path = this_year_path.partition(THIS_YEAR_DIR)[0] + THIS_YEAR_DIR
                os.mkdir(group_path)
                os.mkdir(this_year_path)
            for file_name in os.listdir(this_year_path):
                delete = self.should_delete_file_name(file_name, delete_q1, delete_q1_data)
                if delete:
                    try:
                        file_path = this_year_path + file_name
                        print(f"Deleting {file_path}")
                        Persistence.remove_file(file_path, path_type=Persistence.FILE_PATH)
                        if self.notification_name == "Test":  # also delete from B:
                            file_path = "B:" + file_path[2:]
                            Persistence.remove_file(file_path, path_type=Persistence.FILE_PATH)
                    except Exception as e:
                        print_red(f"Error deleting file {file_path}")

    def should_delete_file_name(self, file_name: str, delete_q1, delete_q1_data) -> bool:
        delete = False
        if delete_q1 and file_name.startswith(f"{THIS_YEAR_PREFIX}") and file_name.endswith(".xlsx"):
            delete = True
        if delete_q1_data and file_name.startswith(f"{THIS_YEAR_PREFIX}") and file_name.endswith(".csv"):
            delete = True
        return delete

    def copy_g_to_a(self):
        if self.notification_name != "Test":
            PrintHelper.printInBox("COPY_G_TO_A")
            q4_file_paths = self.get_ek_q4_file_paths()
            from_base_path = 'g:\\Shared drives\\'  # TODO make it immune to g: vs. G:
            to_q4_root_path = 'A:\\East Kingdom Exchequer Test\\'
            for from_q4_file_path in q4_file_paths:
                from_q4_path, from_q1_path, to_file_stem = self.get_old_file_path_new_dir(from_q4_file_path, "")
                from_g4_stem_file_path = from_q4_path.partition(from_base_path)[-1]
                from_g4_stem_path = os.path.dirname(from_g4_stem_file_path)
                to_q4_path = f"{to_q4_root_path}{from_g4_stem_path}"
                os.makedirs(to_q4_path, exist_ok=True)
                to_q4_path, to_q1_path, to_file_stem = self.get_old_file_path_new_dir(to_q4_path, "")
                os.makedirs(to_q1_path, exist_ok=True)
            for from_q4_file_path in q4_file_paths:
                from_q4_path, from_q1_path, to_file_stem = self.get_old_file_path_new_dir(from_q4_file_path, "")
                from_g4_stem_file_path = from_q4_path.partition(from_base_path)[-1]
                from_g4_stem_path = os.path.dirname(from_g4_stem_file_path) + "\\"
                to_q4_path = f"{to_q4_root_path}{from_g4_stem_path}"
                to_q4_path, to_q1_path, to_file_stem = self.get_old_file_path_new_dir(to_q4_path, "")
                q4_file_name = os.path.basename(from_q4_file_path)
                if exists(to_q4_path):
                    try:
                        to_q4_file_path = to_q4_path + q4_file_name
                        # This will overwrite the destination file if it already exists
                        shutil.copy2(from_q4_file_path, to_q4_file_path)
                        print(f"From File: '{from_q4_file_path}'\r\n  To File: '{to_q4_path}'")
                    except FileNotFoundError:
                        print("The source or destination file was not found.")
                    except PermissionError as e:
                        print("You don't have permission to access the source or destination file.")
                    except shutil.SameFileError:
                        print("Source and destination represent the same file.")
                    except IsADirectoryError:
                        print("The destination path is a directory but was expected to be a file path.")
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}")(from_q4_file_path, to_q4_path)
            if COPY_A_TO_G:
                self.copy_a_to_g()

            PrintHelper.print_red("Exiting after COPY_G_TO_A")
            sys.exit()

    def copy_a_to_g(self):  # TODO FIX ME
        PrintHelper.print_red("Exiting after COPY_A_TO_G")
        sys.exit(0)

    def get_ek_q4_paths(self) -> list[Any]:
        q4_paths = []
        for region in REGIONS:
            group_names = dcn.get_region_group_names(region)
            for group_name in group_names:
                q4_path = self.group_names[group_name][Q4_PATH]
                q4_paths.append(q4_path)
        return q4_paths

    def get_ek_q4_file_paths(self) -> list[Any]:
        q4_paths = self.get_ek_q4_paths()
        q4_file_paths = []
        for q4_path in q4_paths:
            q4_file_name = self.find_q4_file_name(q4_path)
            if q4_file_name:
                q4_file_path = f"{q4_path}{q4_file_name}"
                q4_file_paths.append(q4_file_path)
        return q4_file_paths

    def save_status(self, q4_paths, todos, missing, name):
        group_status_file_path = self.delete_old_status_report(name)

        to_convert, out_of_balance, negative_reports, bugs, q4_fields = self.process_todos(todos)

        self.save_to_convert(to_convert, name)

        column_names = ["Region", "Group", "Full Group Name", "Hyperlink", "Hyperlink", "Hyperlink", "Status"]
        title_row = self.create_title_row(name)
        formatted_rows = [column_names, title_row]
        data = self.create_group_status_data(formatted_rows, q4_paths, missing, out_of_balance, negative_reports, bugs,
                                             q4_fields)
        Persistence.save_list(data, group_status_file_path, Persistence.FILE_PATH)

    def delete_old_status_report(self, name):
        group_status_file_path = self.get_group_status_file_path(name)
        try:
            Persistence.remove_file(group_status_file_path, Persistence.FILE_PATH)
        except Exception as e:
            PrintHelper.printInBox(f"Please close the {name}{GROUP_STATUS}", force_style=PrintHelper.CENTER,
                                   color=Fore.RED)
            sound_file_path = Persistence.get_file_path('Close the group status report.mp3', Persistence.RESOURCE_PATH)
            PlaySound.play_sound(sound_file_path)
            raise e
        return group_status_file_path

    def get_group_status_file_path(self, name, filename_suffix=GROUP_STATUS):
        group_status_file_path = Persistence.get_file_path(f"{self.status_report_path}{name}{filename_suffix}",
                                                           Persistence.FILE_PATH)
        if not exists(self.status_report_path):
            os.makedirs(self.status_report_path)

        return group_status_file_path

    def create_group_status_data(self, formatted_rows, q4_paths, missing, out_of_balance, negative_reports, bugs,
                                 q4_fields):
        for q4_path in q4_paths:  # needed to keep track of missing
            group_name = self.get_group_from_g4_path(q4_path)
            if group_name == OTHER:  # TODO FIX ME
                self.append_other_status_rows(formatted_rows, missing, out_of_balance, negative_reports, bugs,
                                              q4_fields)
            else:
                self.append_status_row(formatted_rows, q4_path, missing, negative_reports, out_of_balance)

        return formatted_rows

    @staticmethod
    def get_group_from_g4_path(g4_path):
        group_path = g4_path.partition(f"{LAST_YEAR_DIR}")[0]
        group_name = group_path.split("\\")[-1]
        return group_name

    def create_region_status(self, formatted_rows: list[Any], region, regions: dict[Any, Any]):
        title = [f"{region}:"]
        formatted_rows.append(title)
        for formatted_row in regions[region]:
            formatted_rows.append(formatted_row)

    def append_other_status_rows(self, formatted_rows, q4_path, missing, negative_reports, out_of_balance, q4_fields):
        group_name, fields = self.get_group_fields(q4_path)
        q4_file_name = os.path.basename(q4_path)
        q4_field = q4_fields[q4_file_name]
        group_name = q4_field[FULL_GROUP_NAME]
        fields[E_REGION] = OTHER
        fields[FULL_GROUP_NAME] = group_name

        self.append_status_row(formatted_rows, q4_path, missing, negative_reports, out_of_balance)

    def append_status_row(self, formatted_rows, q4_path, missing, negative_reports, out_of_balance):
        group_name, fields = self.get_group_fields(q4_path)
        q4_file_name = self.find_q4_file_name(q4_path)
        if q4_file_name is None:
            q4_file_path = None
        else:
            q4_file_path = f"{q4_path}{q4_file_name}"
            if not exists(q4_file_path) or q4_path in missing:
                q4_file_path = None

        q1_path = GroupFields.get_field(fields, Q1_PATH)
        group_dir = q1_path.partition(f"{THIS_YEAR_DIR}{QUARTERLY_REPORTS}")[0] + "\\"

        formatted_row = [""]

        hyperlink_group = Persistence.create_hyperlink(group_dir, f"{group_name}")
        formatted_row.append(hyperlink_group)

        full_group_name = GroupFields.get_field(fields, FULL_GROUP_NAME)
        formatted_row.append(full_group_name)

        hyperlink_last_dir = Persistence.create_hyperlink(q4_path, f"{LAST_YEAR} Q4 dir")
        formatted_row.append(hyperlink_last_dir)

        hyperlink_q4_negative = None
        hyperlink_q4_oob = None

        if q4_file_path is None:
            formatted_row.append(MISSING)
        elif q4_file_path in negative_reports:
            hyperlink_q4_negative = Persistence.create_hyperlink(q4_file_path, NEGATIVE_REPORT)
            formatted_row.append(hyperlink_q4_negative)
        elif q4_file_path in out_of_balance:
            hyperlink_q4_oob = Persistence.create_hyperlink(q4_file_path, OUT_OF_BALANCE)
            formatted_row.append(hyperlink_q4_oob)
        else:
            hyperlink_q4 = Persistence.create_hyperlink(q4_file_path, f"{LAST_YEAR} Q4")
            formatted_row.append(hyperlink_q4)

        hyperlink_q1_dir = Persistence.create_hyperlink(q1_path, f"{THIS_YEAR} Q1 dir")
        formatted_row.append(hyperlink_q1_dir)

        full_group_name = GroupFields.get_field(fields, FULL_GROUP_NAME)
        q1_stem = f"{THIS_YEAR_PREFIX}{full_group_name}"
        q1_file_path = f"{q1_path}{q1_stem}.xlsx"
        q1_data_path = f"{q1_path}{q1_stem}.csv"
        hyperlink_status = None
        if q4_file_path is None:
            hyperlink_status = MISSING
        elif exists(q1_file_path):
            hyperlink_status = Persistence.create_hyperlink(q1_file_path, f"{q1_stem}.xlsx")
        elif exists(q1_data_path):
            hyperlink_status = Persistence.create_hyperlink(q1_data_path, TO_CONVERT)
        elif hyperlink_q4_oob:
            hyperlink_status = hyperlink_q4_oob
        elif q4_file_path and q4_file_path in negative_reports:
            hyperlink_status = hyperlink_q4_negative

        if hyperlink_status:
            formatted_row.append(hyperlink_status)
        else:
            formatted_row.append("BUG")

        formatted_rows.append(formatted_row)

    def get_group_fields(self, q4_path, fields={}) -> tuple[Any, Any]:
        group_dir = q4_path.partition(f"{LAST_YEAR_DIR}{QUARTERLY_REPORTS}")[0]
        group_name = self.get_group_from_g4_path(q4_path)
        group_name, fields = GroupFields.GroupFields.lookup_group_fields(group_name, group_dir, fields)
        if group_name is None or fields is None:
            return None, None
        if q4_path[-1:] != "\\":
            q4_path = q4_path + "\\"
        q1_path = GroupFields.get_q1_path_from_q4_file_path(q4_path)
        return group_name, {GROUP_DIR: group_dir,
                            FULL_GROUP_NAME: GroupFields.get_field(fields, FULL_GROUP_NAME),
                            GROUP_TYPE: GroupFields.get_field(fields, GROUP_TYPE),
                            Q4_PATH: q4_path,
                            Q1_PATH: q1_path,
                            LOCATION: GroupFields.get_field(fields, LOCATION),
                            E_REGION: GroupFields.get_field(fields, E_REGION),
                            NOTE: GroupFields.get_field(fields, NOTE)
                            }

    def delete_specific(self, groups, delete_all_q1, delete_all_q1_data):
        self.delete_all_q1_test_workbooks(groups, delete_all_q1, delete_all_q1_data)

    def process_specific(self, group_names, status_report_name=SPECIFIC):
        group_status_file_path = self.delete_old_status_report(status_report_name)

        if group_status_file_path is not None:
            q4_paths, q4_file_paths, missing, todos = self.find_all_q4s_missing_todos(group_names, status_report_name)

            self.save_status(q4_paths, todos, missing, status_report_name)

        return group_status_file_path

    def create_all_regions_status_report(self):
        all_regions_status_file_path = self.get_group_status_file_path(ALL)

        all_regions_to_convert_file_path = self.get_group_status_file_path(ALL, " To Convert.csv")
        regions_to_convert_file_paths = []
        for region in REGIONS:
            file_path = self.get_group_status_file_path(region, " To Convert.csv")
            if exists(file_path):
                regions_to_convert_file_paths.append(file_path)
        if regions_to_convert_file_paths:
            Persistence.combine_csvs(all_regions_to_convert_file_path, regions_to_convert_file_paths)

        all_regions_status_file_path = self.get_group_status_file_path(ALL)
        regions_status_file_paths = []
        for region in REGIONS:
            file_path = self.get_group_status_file_path(region)
            if exists(file_path):
                regions_status_file_paths.append(file_path)
        Persistence.combine_csvs(all_regions_status_file_path, regions_status_file_paths)

        os.startfile(all_regions_status_file_path)

    def create_status_report(self, name):
        to_convert_file_path = self.get_group_status_file_path(name, " To Convert.csv")
        all_to_convert_file_path = self.get_group_status_file_path(ALL, " To Convert.csv")
        shutil.copy2(to_convert_file_path, all_to_convert_file_path)
        status_file_path = self.get_group_status_file_path(name)
        os.startfile(status_file_path)

    def check_group_regions(self):
        all_region_group_names = []
        for region in REGIONS:
            region_group_names = self.region_group_names[region]
            for group_name in region_group_names:
                all_region_group_names.append(group_name)

        all_group_names = []
        for group_name in self.group_names:
            all_group_names.append(group_name)

        region_group_count = len(all_region_group_names)
        group_count = len(all_group_names)
        if region_group_count != group_count - 1:
            print_red(f"region_group_count {region_group_count} != group_count - 1: {group_count}")

        for region_group_name in all_region_group_names:
            found = region_group_name in all_group_names
            if not found:
                print_red(f"ERROR: e_region q4_file_path not in group_names: {region_group_name}")

        for group_name in all_group_names:
            if group_name == OTHER:
                continue
            found = group_name in all_region_group_names
            if not found:
                print_red(f"ERROR: q4_file_path not in e_region group_names: {group_name}")
        assert region_group_count == group_count - 1  # Don't count OTHER

    def create_title_row(self, name):
        title_row = []
        title_path = f"{self.status_report_path}{name}{GROUP_STATUS}"
        hyperlink = Persistence.create_hyperlink(title_path, name + ":")
        title_row.append(hyperlink)
        return title_row

if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("DriveLookup")

    driveLU: DriveLookup = init_drive_lookup()

    driveLU.copy_g_to_a()  # exits after copying, because something is wrong with workbooks generated on that computer

    if PROCESS_NAME == ALL:
        for region in REGIONS:
            group_names = dcn.get_region_group_names(region)
            driveLU.delete_specific(group_names, DELETE_ALL_Q1, DELETE_ALL_Q1_DATA)

        for region in REGIONS:
            group_names = dcn.get_region_group_names(region)
            region_status_file_path = driveLU.process_specific(group_names, region)

        driveLU.create_all_regions_status_report()
    else:
        if PROCESS_NAME == SPECIFIC:
            group_names = PROCESS_SPECIFIC
        else:
            group_names = dcn.get_region_group_names(PROCESS_NAME)

        driveLU.delete_specific(group_names, DELETE_ALL_Q1, DELETE_ALL_Q1_DATA)

        status_file_path = driveLU.process_specific(PROCESS_SPECIFIC, PROCESS_NAME)

        driveLU.create_status_report(PROCESS_NAME)

    PrintHelper.printInBox()
