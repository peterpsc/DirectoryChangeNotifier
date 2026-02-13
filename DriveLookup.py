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
                                     THIS_YEAR_PREFIX)

COPY_G_TO_A = False
PROCESS_SPECIFIC = ["Hawke's Reache", "Østgarðr", "Appleholm", "Midland Vale", "Northpass", "Hartshorn-dale"]
PROCESS_SPECIFIC = ["Stonemarche", "L'Ile du Dragon Dormant"]
PROCESS_SPECIFIC = ["An Dubhaigeainn"]
PROCESS_SPECIFIC = None
DELETE_ALL_Q1 = False
DELETE_ALL_Q1_DATA = False
DEBUG = False
SAVE_TODOS = False  # False won't save them, True will save "Todos.csv"
SAVE_STATUS_REPORT = True

# Negative Reports.csv, Out Of Balance.csv, Missing.csv, Todos.csv, Group Status.csv are in G:/My Drive/

class DriveLookup:
    def __init__(self, notification_name: str, report_path):
        self.notification_name = notification_name
        self.report_path = report_path
        notification_names = Persistence.get_lines("NotificationNames.txt")
        self.dcn = DirChangeNotifier(notification_names)

    def get_last_year_dirs(self):
        path_options = self.dcn.get_dir_change_path_options(self.notification_name)
        ignore_paths = self.dcn.get_ignore_paths(self.notification_name)
        all_directories = self.dcn.get_dir_paths(path_options, ignore_paths)
        filtered_directories = []
        for directory in all_directories:
            if f"{LAST_YEAR_DIR}Quarterly Reports" in directory:
                filtered_directories.append(directory)

        last_year_dirs = self.remove_extra_directories(filtered_directories)

        return last_year_dirs

    def get_this_year_dirs(self, last_year_dirs):
        this_year_dirs = []
        for last_year_dir in last_year_dirs:
            this_year_dir = self.get_this_year_dir(last_year_dir)
            this_year_dirs.append(this_year_dir)

        return this_year_dirs

    def remove_extra_directories(self, filtered_directories):
        extra_directories = []
        intermediate_results = []

        for directory in filtered_directories:
            subdirectory = directory.split("\\")[-1]
            if subdirectory == "Quarterly Reports" and directory not in extra_directories:
                intermediate_results.append(directory)
            elif "4" in subdirectory and "Q" in subdirectory:
                extra_directories.append(directory)
                intermediate_results.append(directory)
            else:
                sub_directory = directory.partition("\\Quarterly Reports")[0] + "\\Quarterly Reports"
                extra_directories.append(sub_directory)

        returning_directories = []
        not_wanted_directories = []
        for directory in extra_directories:
            sub_directory = directory.partition("\\Quarterly Reports")[0] + "\\Quarterly Reports"
            not_wanted_directories.append(sub_directory)
        for directory in intermediate_results:
            if directory not in not_wanted_directories:
                returning_directories.append(directory)
        return returning_directories

    def find_all_q4s_missing_todos(self, folders):
        all = []
        q4s = []
        missing = []
        todos = []

        for folder in folders:
            file_name = self.find_q4_file_name(folder)
            all.append(f"{folder}")
            if file_name:
                q4s.append(f"{folder}\\{file_name}")
                old_file_path, new_dir, new_file_name = self.get_old_file_path_new_dir(folder, file_name)
                todo = [old_file_path, new_dir, new_file_name]
                new_dir_exists = exists(new_dir)
                if not new_dir_exists:
                    os.makedirs(new_dir)

                new_q1_file_path = f"{new_dir}{new_file_name}.xlsx"
                if exists(new_q1_file_path):
                    print(f"File {new_q1_file_path} already exists")
                    continue
                todos.append(todo)
            else:
                missing.append(folder)

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
            group_name)
        new_file_name = f"{THIS_YEAR_PREFIX}{full_group_name}"
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
        bugs = []
        for todo in todos:
            from_file_path = todo[0]
            to_q1_path = todo[1]

            wbs = OldWorkbookToDataForNew(from_file_path,
                                          to_q1_path)
            if wbs.error:
                bugs.append(from_file_path)
            else:
                balanced, negative = wbs.is_balanced_or_negative()
                if balanced:
                    bug = wbs.save_new_data()
                    if bug:
                        bugs.append(bug)
                    else:
                        to_convert.append(todo)
                elif negative:
                    negative_reports.append(from_file_path)
                else:
                    out_of_balance.append(from_file_path)

        return to_convert, out_of_balance, negative_reports, bugs

    def delete_all_q1_test_workbooks(self, this_year_dirs, delete_q1=False, delete_q1_data=False):
        for this_year_dir in this_year_dirs:
            for file_name in os.listdir(this_year_dir):
                delete = self.should_delete_file_name(file_name, delete_q1, delete_q1_data)
                if delete:
                    file_path = this_year_dir + file_name
                    print(f"Deleting {file_path}")
                    Persistence.remove_file(file_path, path_type=Persistence.FILE_PATH)
                    if self.notification_name == "Test":  # also delete from B:
                        file_path = "B:" + file_path[2:]
                        Persistence.remove_file(file_path, path_type=Persistence.FILE_PATH)

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
        # from_file_path = 'g:\\My Drive\\East Kingdom Exchequer'
        from_file_path = 'g:\\Shared drives'
        l = len(from_file_path)
        to_file_path = 'a:\\East Kingdom Exchequer Test'
        for from_group_path in all:
            to_group_path = f"{to_file_path}{from_group_path[l:]}"
            os.makedirs(to_group_path, exist_ok=True)
            to_new_group_path = to_group_path.partition(f"\\Quarterly Reports")[0] + "\\Quarterly Reports"
            to_new_group_path = to_new_group_path.replace(LAST_YEAR_DIR, THIS_YEAR_DIR)
            os.makedirs(to_new_group_path, exist_ok=True)
        for from_q4_path in q4s:
            to_q4_path = f"{to_file_path}{from_q4_path[l:]}"
            try:
                # This will overwrite the destination file if it already exists
                shutil.copy2(from_q4_path, to_q4_path)
                print(f"File '{to_q4_path}' copied to '{to_q4_path}' successfully.")
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
        formatted_row = ["Group", "Full Group Name", "Hyperlink", "Hyperlink", "Hyperlink", "Status"]
        formatted_rows.append(formatted_row)

        for group in all_last_year:
            formatted_row = []
            group_last_dir, group_name, full_group_name = self.get_group_dir_name_full(group)
            q4_file_name = self.find_q4_file_name(group)
            new_data_file_name = f"{THIS_YEAR_PREFIX}{full_group_name}.csv"
            q4_path = None
            if q4_file_name is not None:
                q4_path = self.fix_slashes(group + "\\" + q4_file_name)
            to_dir = self.get_this_year_dir(f"{group_last_dir}")
            group_last_dir = group_last_dir + LAST_YEAR_DIR
            group_dir = to_dir.partition(f"\\Quarterly Reports")[0]

            hyperlink_group = Persistence.create_hyperlink(group_dir, f"{group_name}")
            formatted_row.append(hyperlink_group)

            if full_group_name:
                hyperlink_group = Persistence.create_hyperlink(group_dir, f"{full_group_name}")
            else:
                hyperlink_group = Persistence.create_hyperlink(group_dir, f"UNKNOWN: {group_name}")
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

            q1_file_name = f"{THIS_YEAR_PREFIX}{full_group_name}.xlsx"
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

            formatted_rows.append(formatted_row)
        return formatted_rows

    def get_group_dir_name_full(self, group_last_dir) -> tuple[Any, Any]:
        group_dir = group_last_dir.partition(f"{LAST_YEAR_DIR}Quarterly Reports")[0]
        group_dir_split = group_dir.split("\\")
        group_dir = self.fix_slashes(group_dir)
        group_name = group_dir_split[- 1]
        group_name = OldWorkbookToDataForNew.substitute_group_name(group_name)
        full_group_name = OldWorkbookToDataForNew.lookup_full_group_name(group_name)

        return group_dir, group_name, full_group_name


def get_drive_lookup():
    global driveLU
    where = Persistence.get_line("GoogleDrive_Path_Options.txt")
    if where == "g:\\ /S":
        driveLU = DriveLookup("Test", "a:\\East Kingdom Exchequer Test\\")
    else:
        driveLU = DriveLookup("GoogleDrive", "g:\\My Drive\\")


if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("DriveLookup")

    get_drive_lookup()

    last_year_dirs = driveLU.get_last_year_dirs()
    if PROCESS_SPECIFIC:
        result = []
        for folder in last_year_dirs:
            group_dir, group_name, full_group_name = driveLU.get_group_dir_name_full(folder)
            if group_name in PROCESS_SPECIFIC:
                result.append(folder)
        last_year_dirs = result

    if DELETE_ALL_Q1 or DELETE_ALL_Q1_DATA:
        this_year_dirs = driveLU.get_this_year_dirs(last_year_dirs)
        driveLU.delete_all_q1_test_workbooks(this_year_dirs, DELETE_ALL_Q1, DELETE_ALL_Q1_DATA)

    group_status_file_path = driveLU.delete_old_status_report()
    if group_status_file_path is not None:
        all, q4s, missing, todos = driveLU.find_all_q4s_missing_todos(last_year_dirs)
        if COPY_G_TO_A:
            driveLU.copy_g_to_a(all, q4s)
        if SAVE_TODOS:
            driveLU.save_to_convert(todos, "Todos.csv")
        if SAVE_STATUS_REPORT:
            driveLU.save_status(all, todos)

    PrintHelper.printInBox()
