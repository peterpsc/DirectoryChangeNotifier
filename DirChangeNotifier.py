import os
import pathlib
import time
from datetime import datetime
from os.path import exists

import Persistence
import PrintHelper
from Gmail import Gmail
from Substitutions import Substitutions

REPORT_MODIFIED = True
ONLY_TO_ME = True
ME = "me.lst"


class DirChangeNotifier:

    def __init__(self, notification_names):
        self.notification_names = notification_names

    def save_date_previous_and_file_paths(self, notification_name, file_paths):
        save_file_path = self.get_save_file_path(notification_name)
        f = open(save_file_path, mode="w", encoding=Persistence.UTF_8)
        f.write(PrintHelper.get_now_string() + "\n")

        for file_path in file_paths:
            f.write(file_path + "\n")
        f.close()

    def get_save_file_path(self, notification_name):
        end_of_name = "_DirTreeToday.txt"
        save_file_name = f'{notification_name}{end_of_name}'
        file_path = Persistence.get_file_path(save_file_name)
        return file_path

    def get_date_previous_file_paths(self, notification_name):
        previous_file_paths = []

        previous_date_string = ""
        save_file_path = self.get_save_file_path(notification_name)
        if exists(save_file_path):
            f = open(save_file_path, mode="r", encoding=Persistence.UTF_8)
            previous_date_string = f.readline().strip()
            lines = f.readlines()
            f.close()
            for file_path in lines:
                previous_file_paths.append(file_path.replace("\n", ""))

        return previous_date_string, previous_file_paths

    @classmethod
    def split_path_options(cls, path_options, default_options=[]):
        options = []
        if "/" in path_options:
            split = path_options.split("/")
            path = split[0].strip()
            options = split[1:]
        else:
            path = path_options.strip()

        if not options:
            options = default_options
        return path, options

    @classmethod
    def get_file_paths(cls, path_options, ignore_paths, filter_paths=[]):
        file_paths = []
        for path_option in path_options:
            if path_option:
                path, option = cls.split_path_options(path_option)
                recursive = False
                if "S" in option:
                    recursive = True
                cls.append_file_paths(file_paths, path, ignore_paths, filter_paths, recursive=recursive)
        return file_paths

    @classmethod
    def append_file_paths(cls, file_paths, root_path, ignore_paths, filter_paths=[], recursive=False):
        if root_path in ignore_paths:
            return

        paths = list(pathlib.Path(root_path).iterdir())
        for item in paths:
            name = item.name
            if name[0] == ".":
                continue
            if name in ignore_paths:
                continue

            file_path = str(item.absolute())
            file_path = Persistence.single_back_slash(file_path)
            if file_path not in ignore_paths:
                if item.is_file():
                    if cls.is_in_filter_path(filter_paths, file_path):
                        file_paths.append(file_path)
                if item.is_dir():
                    PrintHelper.printInBox(file_path, force_style=PrintHelper.INDENT_1)
                    if recursive:
                        cls.append_file_paths(file_paths, file_path, ignore_paths, filter_paths, recursive)

    @classmethod
    def get_dir_paths(cls, path_options, ignore_paths):
        dir_paths = []
        for path_option in path_options:
            if path_option:
                path, option = cls.split_path_options(path_option)
                recursive = False
                if "S" in option:
                    recursive = True
                cls.append_dir_paths(dir_paths, path, ignore_paths, recursive=recursive)
        return dir_paths

    @classmethod
    def append_dir_paths(cls, file_paths, root_path, ignore_paths, recursive=False):
        if root_path in ignore_paths:
            return
        paths = list(pathlib.Path(root_path).iterdir())
        for item in paths:
            name = item.name
            if name[0] == ".":
                continue
            if name in ignore_paths:
                continue
            file_path = str(item.absolute())
            file_path = Persistence.single_back_slash(file_path)
            if file_path not in ignore_paths:
                if item.is_dir():
                    file_paths.append(file_path)
                    if recursive:
                        cls.append_dir_paths(file_paths, file_path, ignore_paths, recursive)

    @classmethod
    def get_added_removed_modified(cls, previous_file_paths, current_file_paths, previous_date_string, filter_paths):
        file_paths_added = current_file_paths.copy()
        file_paths_removed = []
        file_paths_modified = []

        for previous_file_path in previous_file_paths:
            if not exists(previous_file_path):
                file_paths_removed.append(previous_file_path)
            elif cls.is_modified_since(previous_file_path, previous_date_string):
                file_paths_modified.append(previous_file_path)
            elif previous_file_path in file_paths_added:
                file_paths_added.remove(previous_file_path)

        return file_paths_added, file_paths_removed, file_paths_modified

    @classmethod
    def notify(cls, title, notification_list, paths, ignore_paths, filter_paths, previous_date_string,
               previous_file_paths,
               current_file_paths, signature):
        file_paths_added, file_paths_removed, file_paths_modified = cls.get_added_removed_modified(previous_file_paths,
                                                                                                   current_file_paths,
                                                                                                   previous_date_string,
                                                                                                   filter_paths)

        now_string = PrintHelper.get_now_string()
        subject = f'{title}: {now_string}'
        previous = "Previous"
        previous = f'{" " * (len(title) - len(previous))}{previous}: {previous_date_string}'
        title = f'Changes to {paths}'
        ignoring = f'Ignoring: {ignore_paths}'

        PrintHelper.printInBox(subject, force_style=PrintHelper.RIGHT)
        PrintHelper.printInBox(previous, force_style=PrintHelper.RIGHT)
        PrintHelper.printInBox(title, force_style=PrintHelper.LEFT)
        PrintHelper.printInBox(ignoring, force_style=PrintHelper.LEFT)

        if not previous_file_paths:
            PrintHelper.printInBox(f' First time')
            return True
        if not file_paths_added and not file_paths_removed:
            if not REPORT_MODIFIED or not file_paths_modified:
                PrintHelper.printInBox(f' No changes since {previous_date_string}')
                return False

        content = f'{subject}\n{previous}\n{title}\n\n'
        if file_paths_added:
            content += "Added:\n"
            for added in file_paths_added:
                content += "   " + added + "\n"

        if file_paths_removed:
            if not content:
                content += "\n"

            content += "Removed:\n"
            for removed in file_paths_removed:
                content += "   " + removed + "\n"

        if REPORT_MODIFIED and file_paths_modified:
            if not content:
                content += "\n"

            content += "Modified:\n"
            for modified in file_paths_modified:
                content += "   " + modified + "\n"

        PrintHelper.printInBox(content)
        PrintHelper.printInBox()
        PrintHelper.printInBox(notification_list)
        gmail = Gmail()
        gmail.send_emails_or_fb(notification_list, subject, content, signature=signature)
        return True

    @classmethod
    def load_list(cls, notify_list_filename):
        notification_list = Persistence.get_lines(notify_list_filename)
        return notification_list

    def notify_all_names(self):
        for notification_name in self.notification_names:
            self.notify_name(notification_name)

    def notify_name(self, notification_name):
        previous_date_string, previous_file_paths = self.get_date_previous_file_paths(notification_name)
        path_options = self.get_dir_change_path_options(notification_name)
        ignore_paths = self.get_ignore_paths(notification_name)
        filter_paths = self.get_filter_paths(notification_name)
        title = self.get_title(notification_name)
        notification_list = self.get_notification_list(notification_name)
        signature = Substitutions().get_signature("")
        try:
            current_file_paths = self.get_file_paths(path_options, ignore_paths, filter_paths)
            changed = self.notify(title, notification_list, path_options, ignore_paths, filter_paths,
                                  previous_date_string, previous_file_paths, current_file_paths, signature)

            if changed or not previous_date_string:
                self.save_date_previous_and_file_paths(notification_name, current_file_paths)

        except Exception as e:
            PrintHelper.printInBoxException(e)

    def get_dir_change_path_options(self, notification_name):
        file_path = self.copy_first_if_missing(notification_name, "_Path_Options.txt")
        return Persistence.get_lines(file_path, Persistence.FILE_PATH)

    def get_ignore_paths(self, notification_name):
        file_path = self.copy_first_if_missing(notification_name, "_Ignore_Paths.txt")
        return Persistence.get_lines(file_path, Persistence.FILE_PATH)

    def get_filter_paths(self, notification_name):
        file_path = self.copy_first_if_missing(notification_name, "_Filter_Paths.txt")
        filter_paths = []
        if exists( file_path):
            filter_paths = Persistence.get_lines(file_path, Persistence.FILE_PATH)
        return filter_paths


    def copy_first_if_missing(self, notification_name, end_of_name):
        filename = f'{notification_name}{end_of_name}'
        file_path = Persistence.private_file_path(filename)
        if not exists(file_path):
            self.copy_first(notification_name, end_of_name)
        return file_path

    def get_title(self, notification_name):
        file_path = self.copy_first_if_missing(notification_name, "_Title.txt")
        return Persistence.get_lines(file_path, Persistence.FILE_PATH)[0]

    def get_notification_list(self, notification_name):
        if ONLY_TO_ME:
            file_path = Persistence.private_file_path(ME)
        else:
            file_path = self.copy_first_if_missing(notification_name, "_Notification_List.txt")
        return Persistence.get_lines(file_path, Persistence.FILE_PATH)

    def copy_first(self, notification_name, end_of_name):
        first_file_path = Persistence.private_file_path(self.notification_names[0] + end_of_name)
        file_path = Persistence.private_file_path(notification_name + end_of_name)
        self.copy_and_edit(first_file_path, file_path)

    def copy_and_edit(self, first_file_path, file_path):
        if exists(first_file_path):
            lines = Persistence.get_lines(first_file_path, Persistence.FILE_PATH)
            Persistence.write_lines(file_path, lines, Persistence.FILE_PATH)
        os.system(f'notepad {file_path}')

    def check_for_this_year_directories(self):
        for notification_name in self.notification_names:
            year_directories_filename = "NewYearDirectories.txt"
            year_directories_file_path = Persistence.get_file_path(year_directories_filename)
            if exists(year_directories_file_path):
                year_directory_names = Persistence.get_lines(year_directories_filename)
                path_options = self.get_dir_change_path_options(notification_name)
                ignore_paths = self.get_ignore_paths(notification_name)
                all_directories = self.get_dir_paths(path_options, ignore_paths)
                self.make_this_year_directories(year_directory_names, all_directories)

    def make_this_year_directories(self, year_directory_names, all_directories):
        current_year = datetime.now().strftime("%Y")
        previous_year = str(int(current_year) - 1)
        dir_previous_year = "\\" + previous_year
        for directory in all_directories:
            if directory.endswith(dir_previous_year):
                self.ensure_current_year(year_directory_names, directory, current_year)

    def ensure_current_year(self, year_directory_names, previous_year_directory, current_year):
        current_year_directory = previous_year_directory[0:-4] + current_year
        if not exists(current_year_directory):
            os.mkdir(current_year_directory)
            for directory_name in year_directory_names:
                subdir = f'{current_year_directory}\\{directory_name}'
                os.mkdir(subdir)

    @classmethod
    def is_modified_since(cls, file_path, previous_date_string):
        last_modified_timestamp = get_last_modified_timestamp(file_path)
        if last_modified_timestamp > previous_date_string:
            return True
        return False

    @classmethod
    def is_in_filter_path(cls, filter_paths, file_path):
        if len(filter_paths) == 0:
            return True
        for filter_path in filter_paths:
            if filter_path in file_path:
                return True
        return False


def get_last_modified_timestamp(file_path):
    m_t_obj = get_last_modified_time_obj(file_path)
    m_t_stamp = time.strftime("%Y/%m/%d %H:%M:%S", m_t_obj)
    return m_t_stamp


def get_last_modified_time_obj(file_path):
    ti_m = os.path.getmtime(file_path)
    m_ti = time.ctime(ti_m)
    m_t_obj = time.strptime(m_ti)
    return m_t_obj


if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("Dir Change Notifier")

    notification_names = Persistence.get_lines("NotificationNames.txt")
    dcn = DirChangeNotifier(notification_names)
    dcn.check_for_this_year_directories()
    dcn.notify_all_names()

    PrintHelper.printInBox()
