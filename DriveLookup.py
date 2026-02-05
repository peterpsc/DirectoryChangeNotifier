import os
from datetime import datetime
from os.path import exists
from pathlib import Path
from typing import Any

from openpyxl.styles.builtins import hyperlink

import Persistence
import PrintHelper
from DirChangeNotifier import DirChangeNotifier
from OldWorkbookToDataForNew import OldWorkbookToDataForNew

REDO_ALL = True
PREFIX = "TEST "
# All_Groups.csv, Q4s.csv, Missing.csv, Todos.csv are in G:/My Drive/
# TODO make G:/My Drive/Group Status.csv

class DriveLookup:
    def __init__(self):
        notification_names = Persistence.get_lines("NotificationNames.txt")
        self.dcn = DirChangeNotifier(notification_names)
        self.this_year = datetime.now().strftime("%Y")
        self.previous_year = f"{int(self.this_year) - 1}"
        self.previous_year_dir = f"\\{int(self.this_year) - 1}\\"
        self.this_year_dir = f"\\{self.this_year}\\"

    def get_last_year_folders(self):
        notification_name = "GoogleDrive"
        path_options = self.dcn.get_dir_change_path_options(notification_name)
        ignore_paths = self.dcn.get_ignore_paths(notification_name)
        all_directories = self.dcn.get_dir_paths(path_options, ignore_paths)
        filtered_directories = []
        for directory in all_directories:
            if self.previous_year_dir in directory:
                if "\\Quarterly Reports\\" in directory:
                    filtered_directories.append(directory)
                elif directory.endswith("\\Quarterly Reports"):
                    filtered_directories.append(directory)
        for directory in filtered_directories:
            if "\\Quarterly Reports\\" in directory:
                right_index = directory.index("\\Quarterly Reports")
                lower_directory = directory[:right_index + len("\\Quarterly Reports")]
                if lower_directory in filtered_directories:
                    filtered_directories.remove(lower_directory)

                # remove any subdirectories that don't have 4 and Q
                subdirectories = os.listdir(lower_directory)
                for subdirectory in subdirectories:
                    if "4" not in subdirectory or "Q" not in subdirectory:
                        filtered_directories.remove(lower_directory + "\\" + subdirectory)
        return filtered_directories

    def find_all_Q4s_missing_todos_q1s(self, folders):
        all = []
        q4s = []
        missing = []
        todos = []
        q1s = [] # TODO return all the Q1s created already

        for folder in folders:
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
                        q4s.append(f"{folder}\\{file_name}")
                        found = True
                        break
            group_dir = folder.partition("Quarterly Reports")[0]
            all.append(f"{group_dir}")
            if found:
                old_file_path, new_dir, new_file_name = self.get_old_file_path_new_dir(folder, file_name)
                todo = [old_file_path,new_dir,new_file_name]
                if not exists(new_dir):
                    os.makedirs(new_dir)
                new_q1_file_path = f"{new_dir}\\{PREFIX}{new_file_name}.xlsx"
                if exists(new_q1_file_path):
                    print(f"File {new_q1_file_path} already exists")
                    continue
                new_q1_file_path = f"{new_dir}\\{new_file_name}.xlsx"
                if exists(new_q1_file_path):
                    print(f"File {new_q1_file_path} already exists")
                    continue
                todos.append(todo)
            else:
                missing.append(folder)

        return all, q4s, missing, todos, q1s

    def save_missing(self, missing):
        file_path = Persistence.get_file_path("G:\My Drive\Missing.csv", Persistence.FILE_PATH)
        if not q4s:
            Persistence.remove(file_path, Persistence.FILE_PATH)
            return

        missing_data = self.create_hyperlink_data(missing, "2025 Q4 dir")
        Persistence.save_list(missing_data, file_path, path_type=Persistence.FILE_PATH)

    def create_hyperlink_data(self, path_list, title) -> list[Any]:
        formatted_rows = []
        formatted_row = ["Hyperlink", title]
        formatted_rows.append(formatted_row)

        for negative_report in path_list:
            formatted_row = []
            hyperlink = Persistence.create_hyperlink(negative_report, title)
            formatted_row.append(hyperlink)
            formatted_row.append(negative_report)
            formatted_rows.append(formatted_row)
        return formatted_rows

    def save_negative_reports(self, negative_reports):
        file_path = Persistence.get_file_path("G:\My Drive/Negative Reports.csv", Persistence.FILE_PATH)
        if not negative_reports:
            Persistence.remove(file_path, Persistence.FILE_PATH)
            return

        negative_report_data = self.create_hyperlink_data(negative_reports, "2025 Q4 Negative Report")
        Persistence.save_list(negative_report_data, file_path, path_type=Persistence.FILE_PATH)

    def save_Q4_folders(self, q4s):
        file_path = Persistence.get_file_path("G:\My Drive\Q4s.csv", Persistence.FILE_PATH)
        if not q4s:
            Persistence.remove(file_path, Persistence.FILE_PATH)
            return

        q4s_data = self.create_hyperlink_data(q4s, "2025 Q4")
        Persistence.save_list(q4s_data, file_path, path_type=Persistence.FILE_PATH)

    def save_out_of_balance(self, out_of_balance):
        file_path = Persistence.get_file_path("G:\My Drive\Out of Balance.csv", Persistence.FILE_PATH)
        if not out_of_balance:
            Persistence.remove(file_path, Persistence.FILE_PATH)
            return

        data = self.create_hyperlink_data(out_of_balance, "2025 Q4")
        Persistence.save_list(data, file_path, Persistence.FILE_PATH)


    def create_todo_data(self, todos):
        formatted_rows = []
        formatted_row = ["Hyperlink","Hyperlink", "2025 Q4", "2026 Q1 dir", "Filename"]
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

    def save_todos(self, todos):
        file_path = Persistence.get_file_path("G:\My Drive\Todos.csv", Persistence.FILE_PATH)
        if not todos:
            Persistence.remove(file_path, Persistence.FILE_PATH)
            return

        data = self.create_todo_data(todos)
        Persistence.save_list(data, file_path, Persistence.FILE_PATH)

    def save_all_groups(self, all):
        file_path = Persistence.get_file_path("G:\My Drive\All Groups.csv", Persistence.FILE_PATH)
        if not folders:
            Persistence.remove(file_path, Persistence.FILE_PATH)
            return

        data = self.create_hyperlink_data(all, "2025 Q4")
        Persistence.save_list(data, file_path, Persistence.FILE_PATH)

    def get_old_file_path_new_dir(self, folder, file_name) -> Any:
        old_file_path = f'{folder}\\{file_name}'
        new_dir = self.get_to_dir(folder)
        this_year_dirs = new_dir.split("\\")
        group_name = this_year_dirs[len(this_year_dirs) - 3]
        actual_group_name, group_type = self.get_group_name(group_name)
        new_file_name = f"{self.this_year} Q1 {actual_group_name}"
        return old_file_path, new_dir, new_file_name

    def get_group_name(self, group_name) -> Any:
        actual_group_name, group_type = OldWorkbookToDataForNew.lookup_group_name_type(group_name)
        return actual_group_name, group_type

    def get_to_dir(self, from_dir) -> Any:
        this_year_file_path = from_dir.replace(self.previous_year_dir, self.this_year_dir)
        to_dir = this_year_file_path.partition("Quarterly Reports")[0] + "Quarterly Reports"
        return to_dir

    @staticmethod
    def get_state(this_year_dirs) -> Any:
        for i in range(len(this_year_dirs)):
            subdir = this_year_dirs[i]
            if subdir == "East Kingdom Exchequer":
                state = this_year_dirs[i+1]
                return state
        return None

    def process_Todos(self, todos):
        to_convert = []
        out_of_balance = []
        negative_reports = []
        for todo in todos:
            from_file_path = todo[0]
            to_q1_path = todo[1]

            wbs = OldWorkbookToDataForNew(from_file_path,
                                          to_q1_path)

            balanced, negative = wbs.is_balanced_or_negative()
            if balanced:
                wbs.save_new_data()
                to_convert.append(todo)
            elif negative:
                negative_reports.append(from_file_path)
            else:
                from_dir = self.get_from_dir(from_file_path)
                out_of_balance.append(from_dir)
        return to_convert, out_of_balance, negative_reports

    def get_from_dir(self, from_file_path) -> Any:
        last_backslash_index = from_file_path.rfind('\\')
        from_dir = from_file_path[:last_backslash_index]
        return from_dir

    def delete_all_q1_test_workbooks(self):
        pass # TODO


def save_status():
    driveLU.save_all_groups(all)
    driveLU.save_Q4_folders(q4s)
    driveLU.save_missing(missing)
    print(f"All Groups = {all}")
    print(f"Q4s = {q4s}")
    print(f"Missing = {missing}")

    to_convert, out_of_balance, negative_reports = driveLU.process_Todos(todos)

    driveLU.save_out_of_balance(out_of_balance)
    driveLU.save_negative_reports(negative_reports)
    driveLU.save_todos(to_convert)

    print(f"Out of Balance = {out_of_balance}")
    print(f"Todos = {todos}")


if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("DriveLookup")

    driveLU = DriveLookup()
    folders = driveLU.get_last_year_folders()
    if REDO_ALL:
        driveLU.delete_all_q1_test_workbooks()

    all, q4s, missing, todos, q1s = driveLU.find_all_Q4s_missing_todos_q1s(folders)
    save_status()

