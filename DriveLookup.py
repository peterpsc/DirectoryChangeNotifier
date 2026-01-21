import os
import pathlib
from datetime import datetime
from typing import Any

import Persistence
import PrintHelper
from DirChangeNotifier import DirChangeNotifier


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
                filtered_directories.remove(lower_directory)
        return filtered_directories

    def find_Q4s_missing(self, folders):
        q4s = []
        missing = []

        for folder in folders:
            entries = os.listdir(folder)
            found = False
            for entry in entries:
                if "Q4" in entry or "4Q" in entry or "EOY" in entry:
                    q4s.append(f"{folder}\\{entry}")
                    found = True
                    break
            if not found:
                missing.append(folder)
        return q4s, missing

    def save_missing(self, missing):
        filename = "Missing.csv"
        if not missing:
            Persistence.remove(filename)
            return

        Persistence.write_lines(filename, path_type=Persistence.PRIVATE_PATH, lines=missing)


    def save_Q4s(self, q4s):
        filename = "Q4s.csv"
        if not q4s:
            Persistence.remove(filename)
            return

        Persistence.write_lines(filename, path_type=Persistence.PRIVATE_PATH, lines=q4s)

    def save_Todos(self, q4s):
        todos = self.find_todos(q4s)

        filename = "Todos.csv"
        if not todos:
            Persistence.remove(filename)
            return

        Persistence.write_lines(filename, path_type=Persistence.PRIVATE_PATH, lines=todos)

    def find_todos(self, q4s):
        todos = []
        for file_path in q4s:
            new_file_path = self.this_year_file_path(file_path)
            todos.append(new_file_path)
        return todos

    def this_year_file_path(self, file_path) -> Any:
        this_year_file_path = file_path.replace(self.previous_year_dir, self.this_year_dir)
        this_year_file_path = this_year_file_path.replace(self.previous_year, self.this_year)
        this_year_file_path = this_year_file_path.replace("Q4", "Q1")
        this_year_file_path = this_year_file_path.replace("4Q", "Q1")
        this_year_file_path = this_year_file_path.replace("EOY", "Q1")

        return this_year_file_path

if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("DriveLookup")

    driveLU = DriveLookup()
    folders = driveLU.get_last_year_folders()
    q4s, missing = driveLU.find_Q4s_missing(folders)
    print(f"Q4s = {q4s}")
    print(f"missing = {missing}")

    driveLU.save_missing(missing)
    driveLU.save_Q4s(q4s)
    driveLU.save_Todos(q4s)

