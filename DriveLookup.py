import os
from datetime import datetime
from os.path import exists
from pathlib import Path
from typing import Any

import Persistence
import PrintHelper
from DirChangeNotifier import DirChangeNotifier
from OldWorkbookToDataForNew import OldWorkbookToDataForNew


# Groups.lst, Q4s.lst, Missing.lst, Todos.csv are in G:/My Drive/

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

    def find_all_Q4s_missing_todos(self, folders):
        all = []
        q4s = []
        missing = []
        todos = []

        for folder in folders:
            paths = sorted(Path(folder).iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
            found = False
            file_name = None
            for path in paths:
                # Optional: filter out directories if you only want files
                if path.is_file():
                    file_name = path.name
                    if "Q4" in file_name or "4Q" in file_name or "EOY" in file_name or "4th" in file_name:
                        q4s.append(f"{folder}\\{file_name}")
                        found = True
                        break
            group_dir = folder.partition("Quarterly Reports")[0]
            all.append(f"{group_dir}")
            if found:
                old_file_path, new_dir, new_file_name = self.get_old_file_path_new_dir(folder, file_name)
                todo = f'"{old_file_path}","{new_dir}","{new_file_name}"'
                if not exists(new_dir):
                    os.makedirs(new_dir)
                todos.append(todo)
            else:
                missing.append(folder)

        return all, q4s, missing, todos


    def save_missing(self, missing):
        file_path = Persistence.get_file_path("G:\My Drive\Missing.lst", Persistence.FILE_PATH)
        if not q4s:
            Persistence.remove(file_path, Persistence.FILE_PATH)
            return

        Persistence.write_lines(file_path, path_type=Persistence.FILE_PATH, lines=missing)

    def save_Q4_folders(self, q4s):
        file_path = Persistence.get_file_path("G:\My Drive\Q4s.lst", Persistence.FILE_PATH)
        if not q4s:
            Persistence.remove(file_path, Persistence.FILE_PATH)
            return

        Persistence.write_lines(file_path, path_type=Persistence.FILE_PATH, lines=q4s)

    def save_Todos(self, todos):
        file_path = Persistence.get_file_path("G:\My Drive\Todos.csv", Persistence.FILE_PATH)
        if not q4s:
            Persistence.remove(file_path, Persistence.FILE_PATH)
            return

        Persistence.write_lines(file_path, path_type=Persistence.FILE_PATH, lines=todos)

    def save_all_groups(self, all):
        file_path = Persistence.get_file_path("G:\My Drive\All Groups.lst", Persistence.FILE_PATH)
        if not folders:
            Persistence.remove(file_path, Persistence.FILE_PATH)
            return

        Persistence.write_lines(file_path, path_type=Persistence.FILE_PATH, lines=all)

    def get_old_file_path_new_dir(self, folder, file_name) -> Any:
        old_file_path = Path(folder).joinpath(file_name)
        this_year_file_path = folder.replace(self.previous_year_dir, self.this_year_dir)
        new_dir = this_year_file_path.partition("Quarterly Reports")[0]+"Quarterly Reports"
        this_year_dirs = new_dir.split("\\")
        group_name = this_year_dirs[len(this_year_dirs) - 3]
        state = self.get_state(this_year_dirs)
        new_file_name = f"{self.this_year} Q1 {state} {group_name}"
        return old_file_path, new_dir, new_file_name

    @staticmethod
    def get_state(this_year_dirs) -> Any:
        for i in range(len(this_year_dirs)):
            subdir = this_year_dirs[i]
            if subdir == "East Kingdom Exchequer":
                state = this_year_dirs[i+1]
                return state
        return None

    def process_Todos(self, todos):
        for todo in todos:
            parameters = todo.replace('"', '')
            data = parameters.split(",")
            from_file_path = data[0]
            to_file_dir = data[1]
            to_q1_path = to_file_dir

            wbs = OldWorkbookToDataForNew(from_file_path,
                                          to_q1_path)
            wbs.save_new_data()


if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("DriveLookup")

    driveLU = DriveLookup()
    folders = driveLU.get_last_year_folders()

    all, q4s, missing, todos = driveLU.find_all_Q4s_missing_todos(folders)
    print(f"All Groups = {all}")

    print(f"Q4s = {q4s}")
    print(f"Missing = {missing}")
    print(f"Todos = {todos}")

    driveLU.save_all_groups(all)
    driveLU.save_Q4_folders(q4s)
    driveLU.save_missing(missing)
    driveLU.save_Todos(todos)

    driveLU.process_Todos(todos)
