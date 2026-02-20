import os
import shutil
from os.path import exists
from pathlib import Path
from typing import Any

from colorama import Fore

import Persistence
import PlaySound
import PrintHelper
from DirChangeNotifier import DirChangeNotifier
from OldWorkbookToDataForNew import (OldWorkbookToDataForNew, LAST_YEAR, LAST_YEAR_DIR, THIS_YEAR, THIS_YEAR_DIR,
                                     THIS_YEAR_PREFIX, print_red)


def get_DirChangeNotifier() -> DirChangeNotifier:
    dcn = None
    where = Persistence.get_line("GoogleDrive_Path_Options.txt")
    if where == "g:\\ /S":
        dcn = DirChangeNotifier("Test")
    else:
        dcn = DirChangeNotifier("GoogleDrive")
    return dcn


dcn = get_DirChangeNotifier()

TIR_MARA = dcn.get_region_group_names("Tir Mara")
NORTHERN = dcn.get_region_group_names("Northern")
CENTRAL = dcn.get_region_group_names("Central")
SOUTHERN = dcn.get_region_group_names("Southern")
WESTERN = dcn.get_region_group_names("Western")
NORTHEAST = dcn.get_region_group_names("Northeast")
OTHER = dcn.get_region_group_names("Other")

PROCESS_SPECIFIC = ["Another Group"]
PROCESS_SPECIFIC = ["Havre des Glaces"]

PROCESS_SPECIFIC = dcn.append_group_names(PROCESS_SPECIFIC, ["Malagentia"])
PROCESS_SPECIFIC = TIR_MARA
PROCESS_SPECIFIC = ["Glenn Linn", "An Dubhaigeainn", "Buckland Cross"]
PROCESS_SPECIFIC = ["Carillion"]
PROCESS_SPECIFIC = ["Havre des Glaces", "Ruantallan", "Towers", "Quintavia", "Another Group"]
PROCESS_SPECIFIC = ["Concordia of the Snows"]

PROCESS_SPECIFIC = ["Carolingia", "Iron Bog"]
PROCESS_SPECIFIC = ["Malagentia"]
PROCESS_SPECIFIC = None

COPY_G_TO_A = True
DELETE_ALL_Q1 = False  # Should mostly be False, tries to delete them all, but if they are open, keep them
DELETE_ALL_Q1_DATA = True  # keep True
DEBUG = False
SAVE_STATUS_REPORT = True
COPY_A_TO_G = False  # True when it is ready
SKIP_Q1_DATA_IF_Q1_EXISTS = True
if PROCESS_SPECIFIC:
    SKIP_Q1_DATA_IF_Q1_EXISTS = len(PROCESS_SPECIFIC) > 2  # False = Recreate Q1 Data anyway

# Creates:
# Group Status.csv
# To Convert.csv
class DriveLookup:
    def __init__(self, notification_name: str, report_path, process_specific: list = None):
        self.notification_name = notification_name
        self.report_path = report_path
        self.process_specific = process_specific
        self.dcn = get_DirChangeNotifier()
        self.last_year_dirs = self.get_last_year_dirs()
        self.this_year_dirs = self.get_this_year_dirs(self.last_year_dirs)

    def get_last_year_dirs(self):
        all_directories = self.dcn.all_directories
        filtered_directories = []
        last_year_quarterly_reports = f"{LAST_YEAR_DIR}Quarterly Reports"
        for directory in all_directories:
            if last_year_quarterly_reports in directory:
                filtered_directories.append(directory)

        last_year_dirs = self.remove_extra_directories(filtered_directories)

        if self.process_specific:
            substituted_group_names = []
            for group_name in self.process_specific:
                substituted_group_name = OldWorkbookToDataForNew.substitute_group_name(group_name)
                substituted_group_names.append(substituted_group_name)

            result = []
            for folder in last_year_dirs:
                group_dir, group_name, full_group_name, branch = self.get_group_dir_name_full_region(folder)
                if group_name in substituted_group_names:
                    result.append(folder)
            last_year_dirs = result
        return last_year_dirs

    def get_this_year_dirs(self, last_year_dirs):
        this_year_dirs = []
        for last_year_dir in last_year_dirs:
            this_year_dir = self.get_this_year_dir(last_year_dir)
            this_year_dirs.append(this_year_dir)

        return this_year_dirs

    def remove_extra_directories(self, filtered_directories):
        intermediate_results = []

        for directory in filtered_directories:
            extra_dir = directory.split("\\")[-1]
            if "4" in extra_dir and "Q" in extra_dir:
                intermediate_results.append(directory)
            else:
                sub_directory = directory.partition("\\Quarterly Reports")[0] + "\\Quarterly Reports"
                if sub_directory not in intermediate_results:
                    intermediate_results.append(sub_directory)

        return intermediate_results

    def find_all_q4s_missing_todos(self):
        all = []
        q4s = []
        missing = []
        todos = []

        for last_year_dir in self.last_year_dirs:
            file_name = self.find_q4_file_name(last_year_dir)
            all.append(f"{last_year_dir}")
            if file_name:
                q4s.append(f"{last_year_dir}\\{file_name}")
                old_file_path, new_dir, new_file_name = self.get_old_file_path_new_dir(last_year_dir, file_name)
                todo = [old_file_path, new_dir, new_file_name]
                new_dir_exists = exists(new_dir)
                if not new_dir_exists:
                    os.makedirs(new_dir)

                new_q1_file_path = f"{new_dir}{new_file_name}.xlsx"
                if exists(new_q1_file_path):
                    if SKIP_Q1_DATA_IF_Q1_EXISTS:
                        print(f"File {new_q1_file_path} already exists - Skipping")
                        continue
                    print(f"File {new_q1_file_path} already exists - To Convert")
                todos.append(todo)
            else:
                missing.append(last_year_dir)

        return all, q4s, missing, todos

    @staticmethod
    def find_q4_file_name(folder):
        paths = sorted(Path(folder).iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
        found = False
        file_name = None
        for path in paths:
            # Optional: filter out directories if you only want files
            if path.is_file():
                file_name = path.name
                if (not file_name.endswith(".xlsm")
                        and not file_name.endswith(".xlsx")
                        or file_name.startswith("~")):
                    continue
                if "Q4" in file_name or "4Q" in file_name or "EOY" in file_name or "4th" in file_name or "Quarter 4" in file_name:
                    return file_name
        return None

    @staticmethod
    def create_convert_data(todos):
        formatted_rows = []

        for todo in todos:
            formatted_row = [todo[0], todo[1], todo[2]]
            formatted_rows.append(formatted_row)
        return formatted_rows

    def save_to_convert(self, to_convert, file_name="To Convert.csv"):
        to_convert_file_path = Persistence.get_file_path(f"{self.report_path}{file_name}", Persistence.FILE_PATH)
        if not to_convert:
            Persistence.remove_file(to_convert_file_path)
            return

        data = self.create_convert_data(to_convert)
        Persistence.save_list(data, to_convert_file_path, Persistence.FILE_PATH)



    @classmethod
    def fix_slashes(cls, file_path):
        result = file_path.replace('\\', '/')
        return result

    def get_old_file_path_new_dir(self, folder, file_name) -> Any:
        old_file_path = self.fix_slashes(f'{folder}\\{file_name}')
        new_dir = self.get_this_year_dir(folder)
        this_year_dirs_split = new_dir.split("/")
        group_name = this_year_dirs_split[- 4]
        group_name, full_group_name, group_type, region = OldWorkbookToDataForNew.lookup_group_full_name_type_region(
            group_name, new_dir)
        new_file_name = f"{THIS_YEAR_PREFIX}{group_name}"
        return old_file_path, new_dir, new_file_name

    @classmethod
    def get_this_year_dir(cls, last_year_dir) -> Any:
        to_dir = last_year_dir.partition(f"{LAST_YEAR_DIR}")[0]
        to_dir = cls.fix_slashes(f"{to_dir}{THIS_YEAR_DIR}Quarterly Reports\\")

        return to_dir

    @staticmethod
    def process_todos(todos):
        to_convert = []
        out_of_balance = []
        negative_reports = []
        bugs = {}
        for todo in todos:
            from_file_path = todo[0]
            to_q1_path = todo[1]

            wbs = OldWorkbookToDataForNew(from_file_path, to_q1_path)
            if wbs.error:
                bugs[from_file_path] = wbs.error
            else:
                balanced, negative = wbs.is_balanced_or_negative()
                if balanced:
                    bug = wbs.save_new_data()
                    if bug:
                        bugs[todo[0]] = bug
                    else:
                        to_convert.append(todo)
                elif negative:
                    negative_reports.append(from_file_path)
                else:
                    out_of_balance.append(from_file_path)

        return to_convert, out_of_balance, negative_reports, bugs

    def delete_all_q1_test_workbooks(self, delete_q1=False, delete_q1_data=False):
        for this_year_dir in self.this_year_dirs:
            for file_name in os.listdir(this_year_dir):
                delete = self.should_delete_file_name(file_name, delete_q1, delete_q1_data)
                if delete:
                    try:
                        file_path = this_year_dir + file_name
                        print(f"Deleting {file_path}")
                        Persistence.remove_file(file_path, path_type=Persistence.FILE_PATH)
                        if self.notification_name == "Test":  # also delete from B:
                            file_path = "B:" + file_path[2:]
                            Persistence.remove_file(file_path, path_type=Persistence.FILE_PATH)
                    except Exception as e:
                        print_red(f"Error deleting file {file_path}")

    def should_delete_file_name(self, file_name: str, delete_q1, delete_q1_data) -> bool:
        delete = False
        if self.notification_name == "Test":
            if delete_q1 and file_name.endswith(".xlsx"):
                delete = True
            if delete_q1_data and file_name.endswith(".csv"):
                delete = True
        else:
            if delete_q1 and file_name.startswith(f"{THIS_YEAR_PREFIX}") and file_name.endswith(".xlsx"):
                delete = True
            if delete_q1_data and file_name.startswith(f"{THIS_YEAR_PREFIX}") and file_name.endswith(".csv"):
                delete = True
        return delete

    @staticmethod
    def copy_g_to_a(all, q4s):
        groupDataDir = Persistence.get_line("G:/My Drive/East Kingdom Exchequer Drive.txt", Persistence.FILE_PATH)
        if groupDataDir.startswith("G:"):
            from_file_path = 'G:\\Shared drives'
            l = len(from_file_path)
            to_file_path = 'A:\\East Kingdom Exchequer Test'
            for from_group_path in all:
                to_group_path = f"{to_file_path}\\{from_group_path[l:]}"
                os.makedirs(to_group_path, exist_ok=True)
                to_new_group_path = to_group_path.partition(f"\\Quarterly Reports")[0] + "\\Quarterly Reports"
                to_new_group_path = to_new_group_path.replace(LAST_YEAR_DIR, THIS_YEAR_DIR)
                os.makedirs(to_new_group_path, exist_ok=True)
            for from_q4_path in q4s:
                if exists(from_q4_path):
                    to_q4_path = f"{to_file_path}{from_q4_path[l:]}"
                    try:
                        # This will overwrite the destination file if it already exists
                        shutil.copy2(from_q4_path, to_q4_path)
                        print(f"From File: '{from_q4_path}'\r\n  To File: '{to_q4_path}'")
                    except FileNotFoundError:
                        print("The source or destination file was not found.")
                    except PermissionError:
                        print("You don't have permission to access the source or destination file.")
                    except shutil.SameFileError:
                        print("Source and destination represent the same file.")
                    except IsADirectoryError:
                        print("The destination path is a directory but was expected to be a file path.")
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}")(from_q4_path, to_q4_path)

    def copy_a_to_g(self, all, q4s):
        groupDataDir = Persistence.get_line("G:/My Drive/East Kingdom Exchequer Drive.txt", Persistence.FILE_PATH)
        if groupDataDir.startswith("G:"):
            a_file_path = 'A:\\East Kingdom Exchequer Test\\'
            la = len(a_file_path)
            g_file_path = 'G:\\Shared drives\\'
            lg = len(g_file_path)
            for g_group_path in all:
                g_new_group_path = g_group_path.partition(f"\\Quarterly Reports")[0] + "\\Quarterly Reports"
                g_new_group_path = g_new_group_path.replace(LAST_YEAR_DIR, THIS_YEAR_DIR)
                a_new_group_path = f"{a_file_path}{g_new_group_path[lg:]}"
                file_name = self.find_q4_file_name(g_group_path)
                old_file_path, new_dir, new_file_name = self.get_old_file_path_new_dir(g_group_path, file_name)
                a_q1_path = f"{a_new_group_path}\\{new_file_name}.xlsx"
                g_q1_path = f"{g_new_group_path}\\{new_file_name}.xlsx"
                try:
                    if exists(a_q1_path) and exists(g_new_group_path):
                        shutil.copy2(a_q1_path,
                                     g_q1_path)  # This will overwrite the destination file if it already exists
                        print(f"From File: '{a_q1_path}'\r\n  To File: '{g_q1_path}'")
                except FileNotFoundError:
                    print("The source or destination file was not found.")
                except PermissionError:
                    print("You don't have permission to access the source or destination file.")
                except shutil.SameFileError:
                    print("Source and destination represent the same file.")
                except IsADirectoryError:
                    print("The destination path is a directory but was expected to be a file path.")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")(a_q1_path, g_q1_path)

    def save_status(self, all, todos):
        group_status_file_path = self.delete_old_status_report()

        to_convert, out_of_balance, negative_reports, bugs = self.process_todos(todos)

        self.save_to_convert(to_convert)

        data = self.create_group_status_data(all, out_of_balance, negative_reports, bugs)
        Persistence.save_list(data, group_status_file_path, Persistence.FILE_PATH)
        os.startfile(group_status_file_path)

    def delete_old_status_report(self):
        group_status_file_path = Persistence.get_file_path(f"{self.report_path}Group Status.csv", Persistence.FILE_PATH)
        try:
            Persistence.remove_file(group_status_file_path, Persistence.FILE_PATH)
        except Exception as e:
            PrintHelper.printInBox("Please close the Group Status.csv first", force_style=PrintHelper.CENTER,
                                   color=Fore.RED)
            sound_file_path = Persistence.get_file_path('Close the group status report.mp3', Persistence.RESOURCE_PATH)
            PlaySound.play_sound(sound_file_path)
            return None
        return group_status_file_path

    def create_group_status_data(self, all_last_year, out_of_balance, negative_reports, bugs):
        formatted_rows = []
        formatted_row = ["Region", "Group", "Full Group Name", "Hyperlink", "Hyperlink", "Hyperlink", "Status"]
        formatted_rows.append(formatted_row)

        regions = {}
        for group in all_last_year:
            self.create_status_row(regions, bugs, group, negative_reports, out_of_balance)

        # sort by region and Other is last
        for region in regions:
            if region == "Other":
                continue
            self.create_region_status(formatted_rows, region, regions)
        if "Other" in regions:
            self.create_region_status(formatted_rows, "Other", regions)

        return formatted_rows

    def create_region_status(self, formatted_rows: list[Any], region, regions: dict[Any, Any]):
        title = [""]
        formatted_rows.append(title)
        for formatted_row in regions[region]:
            formatted_rows.append(formatted_row)

    def create_status_row(self, regions, bugs, group, negative_reports, out_of_balance):
        group_last_dir, group_name, full_group_name, region = self.get_group_dir_name_full_region(group)
        q4_file_name = self.find_q4_file_name(group)
        new_data_file_name = f"{THIS_YEAR_PREFIX}{group_name}.csv"
        q4_path = None
        if q4_file_name is not None:
            q4_path = self.fix_slashes(group + "\\" + q4_file_name)
        to_dir = self.get_this_year_dir(f"{group_last_dir}")
        group_last_dir = group_last_dir + LAST_YEAR_DIR
        group_dir = to_dir.partition(f"\\Quarterly Reports")[0]

        formatted_row = []
        hyperlink_region = Persistence.create_hyperlink(group_dir, f"{region}")
        formatted_row.append(hyperlink_region)

        hyperlink_group = Persistence.create_hyperlink(group_dir, f"{group_name}")
        formatted_row.append(hyperlink_group)

        unknown = False
        if full_group_name:
            hyperlink_group = Persistence.create_hyperlink(group_dir, f"{full_group_name}")
        else:
            hyperlink_group = Persistence.create_hyperlink(group_dir, f"{group_name}")
            unknown = True
        formatted_row.append(hyperlink_group)

        hyperlink_last_dir = Persistence.create_hyperlink(group_last_dir, f"{LAST_YEAR} dir")
        formatted_row.append(hyperlink_last_dir)

        hyperlink_q4_negative = None
        hyperlink_q4_oob = None
        if q4_path and q4_path in negative_reports:
            hyperlink_q4_negative = Persistence.create_hyperlink(q4_path, f"Negative Report")
            formatted_row.append(hyperlink_q4_negative)
        elif q4_path in out_of_balance:
            hyperlink_q4_oob = Persistence.create_hyperlink(q4_path, f"Out of Balance")
            formatted_row.append(hyperlink_q4_oob)
        elif q4_path is None:
            formatted_row.append("MISSING")
        else:
            hyperlink_q4 = Persistence.create_hyperlink(q4_path, f"{LAST_YEAR} Q4")
            formatted_row.append(hyperlink_q4)

        hyperlink_q1_dir = Persistence.create_hyperlink(to_dir, f"{THIS_YEAR} Q1 dir")
        formatted_row.append(hyperlink_q1_dir)

        q1_file_name = f"{THIS_YEAR_PREFIX}{group_name}.xlsx"
        q1_path = f"{to_dir}{q1_file_name}"
        q1_data_path = f"{to_dir}{new_data_file_name}"
        hyperlink_status = None
        if exists(q1_path):
            hyperlink_status = Persistence.create_hyperlink(q1_path, f"{q1_file_name}")
        elif exists(q1_data_path):
            hyperlink_status = Persistence.create_hyperlink(q1_data_path, f"TO CONVERT")
        elif hyperlink_q4_oob:
            hyperlink_status = hyperlink_q4_oob
        elif q4_path and q4_path in negative_reports:
            hyperlink_status = hyperlink_q4_negative
        elif group in bugs:
            hyperlink_status = "BUG"
        elif q4_path is None:
            hyperlink_status = "MISSING"

        if hyperlink_status:
            formatted_row.append(hyperlink_status)

        region_rows = []
        try:
            region_rows = regions[region]
        except KeyError:
            regions[region] = region_rows

        region_rows.append(formatted_row)
        regions[region] = region_rows

    def get_group_dir_name_full_region(self, group_last_dir) -> tuple[Any, Any]:
        group_dir = group_last_dir.partition(f"{LAST_YEAR_DIR}Quarterly Reports")[0]
        group_dir_split = group_dir.split("\\")
        group_dir = self.fix_slashes(group_dir)
        group_name = group_dir_split[- 1]
        name_of_branch, full_name_of_branch, group_type, region = OldWorkbookToDataForNew.lookup_group_full_name_type_region(
            group_name, group_dir, group_name)

        return group_dir, name_of_branch, full_name_of_branch, region

def get_drive_lookup(process_specific: list = None):
    driveLU = None
    where = Persistence.get_line("GoogleDrive_Path_Options.txt")
    if where == "g:\\ /S":
        driveLU = DriveLookup("Test", "A:\\East Kingdom Exchequer Test\\", process_specific)
    else:
        driveLU = DriveLookup("GoogleDrive", "G:\\My Drive\\", process_specific)
    return driveLU

if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("DriveLookup")

    driveLU = get_drive_lookup(PROCESS_SPECIFIC)

    if DELETE_ALL_Q1 or DELETE_ALL_Q1_DATA:
        driveLU.delete_all_q1_test_workbooks(DELETE_ALL_Q1, DELETE_ALL_Q1_DATA)

    group_status_file_path = driveLU.delete_old_status_report()
    if group_status_file_path is not None:
        all, q4s, missing, todos = driveLU.find_all_q4s_missing_todos()
        if COPY_G_TO_A:
            driveLU.copy_g_to_a(all, q4s)
        if SAVE_STATUS_REPORT:
            driveLU.save_status(all, todos)
        if COPY_A_TO_G:
            driveLU.copy_a_to_g(all, q4s)

    PrintHelper.printInBox()
