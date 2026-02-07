import os
from datetime import datetime
from os.path import exists
from pathlib import Path
from typing import Any

import Persistence
import PrintHelper
from DirChangeNotifier import DirChangeNotifier
from OldWorkbookToDataForNew import OldWorkbookToDataForNew

COPY_G_TO_A = False
REDO_ALL = False
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

    def get_this_year_folders(self):
        notification_name = "GoogleDrive"
        path_options = self.dcn.get_dir_change_path_options(notification_name)
        ignore_paths = self.dcn.get_ignore_paths(notification_name)
        all_directories = self.dcn.get_dir_paths(path_options, ignore_paths)
        filtered_directories = []
        for directory in all_directories:
            if self.this_year_dir in directory:
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
        return filtered_directories

    def find_existing_q1s(self, folders):
        q1s = []

        for folder in folders:
            paths = sorted(Path(folder).iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
            file_name = None
            for path in paths:
                if path.is_file():
                    file_name = path.name
                    if not file_name.startswith(f"{PREFIX} {self.this_year_dir} Q1 ") or not file_name.endswith(".xlsx"):
                        continue
                    q1s.append(f"{folder}\\{file_name}")

        return q1s


    def find_all_Q4s_missing_todos_bugs(self, folders):
        all = []
        q4s = []
        missing = []
        todos = []
        bugs = []

        for folder in folders:
            file_name = self.find_q4_file_name(folder)
            all.append(f"{folder}")
            if file_name:
                q4s.append(f"{folder}\\{file_name}")
                old_file_path, new_dir, new_file_name = self.get_old_file_path_new_dir(folder, file_name)
                todo = [old_file_path,new_dir,new_file_name]
                if not exists(new_dir):
                    os.makedirs(new_dir)
                if new_file_name is None:
                    bugs.append(todo)
                else:
                    new_q1_file_path = f"{new_dir}\\{PREFIX}{new_file_name}.xlsx"
                    if exists(new_q1_file_path):
                        print(f"File {new_q1_file_path} already exists")
                        continue
                    todos.append(todo)
            else:
                missing.append(folder)

        return all, q4s, missing, todos, bugs

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
        print(f"Negative Reports = {negative_reports}")

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
        print(f"Out of Balance = {out_of_balance}")



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
        this_year_dirs_split = new_dir.split("\\")
        group_name = this_year_dirs_split[- 4]
        full_group_name, group_type = OldWorkbookToDataForNew.lookup_group_full_name_type(group_name)
        new_file_name = f"{self.this_year} Q1 {full_group_name}"
        return old_file_path, new_dir, new_file_name

    def get_to_dir(self, from_dir) -> Any:
        to_dir = from_dir.partition(f"{self.previous_year_dir}")[0]
        to_dir = f"{to_dir}\\{self.this_year}\\Quarterly Reports\\"

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
        folders = self.get_this_year_folders()
        for folder in folders:
            for file_name in os.listdir(folder):
                if file_name.startswith(f"TEST {self.this_year} Q1") and file_name.endswith(".xlsx"):
                    file_path = folder + "\\" + file_name
                    os.remove(file_path)

    def copy_g_to_a(self, q4s):
        pass # TODO


    def save_status(self, all, q4s, missing, todos, bugs):
        to_convert, out_of_balance, negative_reports = self.process_Todos(todos)

        self.save_todos(todos)
        #self.save_out_of_balance(out_of_balance)
        self.save_negative_reports(negative_reports)

        file_path = Persistence.get_file_path("G:\My Drive\Group Status.csv", Persistence.FILE_PATH)
        Persistence.remove(file_path, Persistence.FILE_PATH)

        data = self.create_group_status_data(all, q4s, missing, out_of_balance, negative_reports, bugs)
        Persistence.save_list(data, file_path, Persistence.FILE_PATH)

    def create_group_status_data(self, all_last_year, q4s, missing, out_of_balance, negative_reports, bugs):
        formatted_rows = []
        formatted_row = ["Group", "Full Group Name","Hyperlink", "Hyperlink", "Hyperlink", "Status"]
        formatted_rows.append(formatted_row)

        for group in all_last_year:
            formatted_row = []
            group_last_dir, group_name, full_group_name  = self.get_group_dir_name_full(group)
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

            if group in negative_reports:
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
            hyperlink_status = Persistence.create_hyperlink(q1_data_path, f"READY")
            print(q1_path)
            if exists(q1_path):
                hyperlink_status = Persistence.create_hyperlink(q1_path, f"{q1_file_name}")
            elif q4_path is None:
                hyperlink_status = "MISSING"
            elif group in bugs or "None" in q1_data_path:
                hyperlink_status = "BUG"
            elif group in negative_reports:
                hyperlink_status = hyperlink_q4_negative
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

    def get_to_file_path(self, to_dir, group_name):
        if group_name:
            full_group_name = OldWorkbookToDataForNew.lookup_full_group_name(group_name)
            if full_group_name:
                return f"{to_dir}\\{PREFIX} {self.this_year} Q1 {group_name}.xlsx"
        return None



if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("DriveLookup")

    driveLU = DriveLookup()
    if REDO_ALL:
        driveLU.delete_all_q1_test_workbooks()

    folders = driveLU.get_last_year_folders()

    all, q4s, missing, todos, bugs = driveLU.find_all_Q4s_missing_todos_bugs(folders)

    driveLU.save_status(all, q4s, missing, todos, bugs)

    if COPY_G_TO_A:
        driveLU.copy_g_to_a(q4s)

