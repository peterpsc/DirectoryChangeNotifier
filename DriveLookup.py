import os
import shutil
from datetime import datetime
from os.path import exists
from pathlib import Path
from typing import Any

from colorama import Fore

import Persistence
import PrintHelper
from DirChangeNotifier import DirChangeNotifier
from OldWorkbookToDataForNew import OldWorkbookToDataForNew

COPY_G_TO_A = False
REDO_ALL = True
PROCESS_SPECIFIC = None
PROCESS_SPECIFIC = ["Gryphonwald"]
PROCESS_SPECIFIC = ["Hawke's Reache", "Østgarðr", "Appleholm", "Midland Vale", "Northpass", "Hartshorn-dale"]

PREFIX = "TEST "


# Negative Reports.csv, Out Of Balance.csv, Missing.csv, Todos.csv, Group Status.csv are in G:/My Drive/

class DriveLookup:
    def __init__(self, notification_name: str, report_path):
        self.notification_name = notification_name
        self.report_path = report_path
        notification_names = Persistence.get_lines("NotificationNames.txt")
        self.dcn = DirChangeNotifier(notification_names)
        self.this_year = datetime.now().strftime("%Y")
        self.previous_year = f"{int(self.this_year) - 1}"
        self.previous_year_dir = f"\\{int(self.this_year) - 1}\\"
        self.this_year_dir = f"\\{self.this_year}\\"

    def get_last_year_folders(self):
        path_options = self.dcn.get_dir_change_path_options(self.notification_name)
        ignore_paths = self.dcn.get_ignore_paths(self.notification_name)
        all_directories = self.dcn.get_dir_paths(path_options, ignore_paths)
        filtered_directories = []
        for directory in all_directories:
            if f"{self.previous_year_dir}Quarterly Reports" in directory:
                filtered_directories.append(directory)

        result = self.remove_extra_directories(filtered_directories)

        return result

    def remove_extra_directories(self, filtered_directories):
        extra_directories = []
        result = []

        for directory in reversed(filtered_directories):
            subdirectory = directory.split("\\")[-1]
            if subdirectory == "Quarterly Reports" and directory not in extra_directories:
                result.append(directory)
            elif "4" in subdirectory and "Q" in subdirectory:
                extra_directories.append(directory)
                result.append(directory)
            else:
                sub_directory = directory.partition("\\Quarterly Reports")[0] + "\\Quarterly Reports"
                extra_directories.append(sub_directory)

        return reversed(result)

    def find_all_Q4s_missing_todos(self, folders):
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

                new_q1_file_path = f"{new_dir}\\{PREFIX}{new_file_name}.xlsx"
                if exists(new_q1_file_path):
                    print(f"File {new_q1_file_path} already exists")
                    continue
                todos.append(todo)
            else:
                missing.append(folder)

        return all, q4s, missing, todos

    def find_q4_file_name(self, folder):
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

    def create_convert_data(self, todos):
        formatted_rows = []
        formatted_row = ["Hyperlink", "Hyperlink", "2025 Q4", "2026 Q1 dir", "Filename"]
        formatted_rows.append(formatted_row)

        for todo in todos:
            formatted_row = []
            from_dir = self.get_from_dir(todo[0])
            to_dir = self.get_to_dir(from_dir)
            hyperlink = Persistence.create_hyperlink(todo[0], "2025 Q4")
            formatted_row.append(hyperlink)
            hyperlink = Persistence.create_hyperlink(to_dir, "2026 Q1 dir")
            formatted_row.append(hyperlink)
            formatted_row.append(todo[0])
            formatted_row.append(to_dir)
            formatted_row.append(todo[2])
            formatted_rows.append(formatted_row)
        return formatted_rows

    def save_to_convert(self, to_convert):
        file_path = Persistence.get_file_path(f"{self.report_path}To Convert.csv", Persistence.FILE_PATH)
        if not to_convert:
            Persistence.remove_file(file_path, Persistence.FILE_PATH)
            return

        data = self.create_convert_data(to_convert)
        Persistence.save_list(data, file_path, Persistence.FILE_PATH)


    def get_old_file_path_new_dir(self, folder, file_name) -> Any:
        old_file_path = f'{folder}\\{file_name}'
        new_dir = self.get_to_dir(folder)
        this_year_dirs_split = new_dir.split("\\")
        group_name = this_year_dirs_split[- 4]
        group_name, full_group_name, group_type = OldWorkbookToDataForNew.lookup_group_full_name_type(group_name)
        new_file_name = f"{self.this_year} Q1 {full_group_name}"
        return old_file_path, new_dir, new_file_name

    def get_to_dir(self, from_dir) -> Any:
        to_dir = from_dir.partition(f"{self.previous_year_dir}")[0]
        to_dir = f"{to_dir}\\{self.this_year}\\Quarterly Reports\\"

        return to_dir

    def process_Todos(self, todos):
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
                    from_dir = self.get_from_dir(from_file_path)
                    out_of_balance.append(from_dir)

        return to_convert, out_of_balance, negative_reports, bugs

    def get_from_dir(self, from_file_path) -> Any:
        last_backslash_index = from_file_path.rfind('\\')
        from_dir = from_file_path[:last_backslash_index]
        return from_dir

    def delete_all_q1_test_workbooks(self, folders):
        for folder in folders:
            for file_name in os.listdir(folder):
                if file_name.startswith(f"TEST {self.this_year} Q1") and file_name.endswith(".xlsx"):
                    file_path = folder + "\\" + file_name
                    print(f"Deleting {file_path}")
                    os.remove(file_path)

    def copy_g_to_a(self, all, q4s):
        # from_file_path = 'g:\\My Drive\\East Kingdom Exchequer'
        from_file_path = 'g:\\Shared drives'
        l = len(from_file_path)
        to_file_path = 'a:\\East Kingdom Exchequer Test'
        for from_group_path in all:
            to_group_path = f"{to_file_path}{from_group_path[l:]}"
            os.makedirs(to_group_path, exist_ok=True)
            to_new_group_path = to_group_path.partition(f"\\Quarterly Reports")[0] + "\\Quarterly Reports"
            to_new_group_path = to_new_group_path.replace(self.previous_year_dir, self.this_year_dir)
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

        to_convert, out_of_balance, negative_reports, bugs = self.process_Todos(todos)

        self.save_to_convert(to_convert)

        data = self.create_group_status_data(all, out_of_balance, negative_reports, bugs)
        Persistence.save_list(data, group_status_file_path, Persistence.FILE_PATH)
        os.startfile(group_status_file_path)

    def delete_old_status_report(self):
        group_status_file_path = Persistence.get_file_path(f"{self.report_path}Group Status.csv", Persistence.FILE_PATH)
        try:
            Persistence.remove(group_status_file_path, Persistence.FILE_PATH)
        except:
            PrintHelper.printInBox("Please close the Group Status.csv first", force_style=PrintHelper.CENTER,
                                   color=Fore.RED)
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
            new_data_file_name = f"{self.this_year} Q1 {full_group_name}.csv"
            q4_path = None
            if q4_file_name is not None:
                q4_path = group + "\\" + q4_file_name
            to_dir = self.get_to_dir(f"{group_last_dir}")
            group_last_dir = group_last_dir + self.previous_year_dir
            group_dir = to_dir.partition(f"\\Quarterly Reports")[0]

            hyperlink_group = Persistence.create_hyperlink(group_dir, f"{group_name}")
            formatted_row.append(hyperlink_group)

            if full_group_name:
                hyperlink_group = Persistence.create_hyperlink(group_dir, f"{full_group_name}")
            else:
                hyperlink_group = Persistence.create_hyperlink(group_dir, f"UNKNOWN: {group_name}")
            formatted_row.append(hyperlink_group)

            hyperlink_last_dir = Persistence.create_hyperlink(group_last_dir, f"{self.previous_year} dir")
            formatted_row.append(hyperlink_last_dir)

            if q4_path and q4_path in negative_reports:
                hyperlink_q4_negative = Persistence.create_hyperlink(q4_path, f"Negative Report")
                formatted_row.append(hyperlink_q4_negative)
            elif group in out_of_balance:
                hyperlink_q4_oob = Persistence.create_hyperlink(q4_path, f"Out of Balance")
                formatted_row.append(hyperlink_q4_oob)
            elif q4_path is None:
                formatted_row.append("MISSING")
            else:
                hyperlink_q4 = Persistence.create_hyperlink(q4_path, f"{self.previous_year} Q4")
                formatted_row.append(hyperlink_q4)

            hyperlink_q1_dir = Persistence.create_hyperlink(to_dir, f"{self.this_year} Q1 dir")
            formatted_row.append(hyperlink_q1_dir)

            q1_file_name = f"{PREFIX}{self.this_year} Q1 {full_group_name}.xlsx"
            q1_path = f"{to_dir}{q1_file_name}"
            q1_data_path = f"{to_dir}\\{new_data_file_name}"
            hyperlink_status = Persistence.create_hyperlink(q1_data_path, f"TO CONVERT")
            print(q1_path)
            if q4_path and q4_path in negative_reports:
                hyperlink_status = hyperlink_q4_negative
            elif exists(q1_path):
                hyperlink_status = Persistence.create_hyperlink(q1_path, f"{q1_file_name}")
            elif q4_path is None:
                hyperlink_status = "MISSING"
            elif group in bugs or "None" in q1_data_path:
                hyperlink_status = "BUG"
            elif group in out_of_balance:
                hyperlink_status = hyperlink_q4_oob
            formatted_row.append(hyperlink_status)

            formatted_rows.append(formatted_row)
        return formatted_rows

    def get_group_dir_name_full(self, group_last_dir) -> tuple[Any, Any]:
        group_dir = group_last_dir.partition(f"{self.previous_year_dir}Quarterly Reports")[0]
        group_dir_split = group_dir.split("\\")
        group_name = group_dir_split[- 1]
        group_name = OldWorkbookToDataForNew.substitute_group_name(group_name)
        full_group_name = OldWorkbookToDataForNew.lookup_full_group_name(group_name)

        return group_dir, group_name, full_group_name

def getDriveLookup():
    global driveLU

    where = Persistence.get_line("GoogleDrive_Path_Options.txt")
    if where == "g:\\ /S":
        driveLU = DriveLookup("Test", "a:\\East Kingdom Exchequer Test\\")
    else:
        driveLU = DriveLookup("GoogleDrive", "g:\\My Drive\\")


if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("DriveLookup")

    getDriveLookup()

    folders = driveLU.get_last_year_folders()
    if PROCESS_SPECIFIC:
        result = []
        for folder in folders:
            group_dir, group_name, full_group_name = driveLU.get_group_dir_name_full(folder)
            if group_name in PROCESS_SPECIFIC:
                result.append(folder)
        folders = result

    if REDO_ALL:
        driveLU.delete_all_q1_test_workbooks(folders)

    group_status_file_path = driveLU.delete_old_status_report()
    if group_status_file_path is not None:
        all, q4s, missing, todos = driveLU.find_all_Q4s_missing_todos(folders)
        if COPY_G_TO_A:
            driveLU.copy_g_to_a(all, q4s)
        else:
            driveLU.save_status(all, todos)

    PrintHelper.printInBox()
