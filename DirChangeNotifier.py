import os
import pathlib
from os.path import exists

import Persistence
import PrintHelper
from Gmail import Gmail

DIR_TREE_FILENAME = "DirTreeToday.txt"
SIGNATURE = "Change Notifier"

NOTIFICATION_LIST_FILENAME = "NotificationList.txt"


class DirChangeNotifier:

    @classmethod
    def save_date_previous_and_file_paths(cls, save_file_name, file_paths):

        save_file_path = Persistence.private_file_path(save_file_name)
        f = open(save_file_path, mode="w", encoding=Persistence.UTF_8)
        f.write(PrintHelper.get_now_string() + "\n")

        for file_path in file_paths:
            f.write(file_path + "\n")
        f.close()

    @classmethod
    def get_date_previous_file_paths(cls, save_file_name):
        previous_file_paths = []

        previous_date_string = ""
        save_file_path = Persistence.private_file_path(save_file_name)
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
    def get_file_paths(cls, path_options, ignore_paths):
        file_paths = []
        for path_option in path_options:
            if path_option:
                path, option = cls.split_path_options(path_option)
                if "S" in option:
                    cls.append_file_paths_include_subdirs(file_paths, path, ignore_paths)
                else:
                    cls.append_file_paths(file_paths, path, ignore_paths)
        return file_paths

    @classmethod
    def append_file_paths(cls, file_paths, path, ignore_paths):
        if path in ignore_paths:
            return
        paths = list(pathlib.Path(path).iterdir())
        for item in paths:
            file_path = str(item.absolute())
            file_path = Persistence.single_back_slash(file_path)
            if file_path not in ignore_paths:
                if item.is_file():
                    file_paths.append(file_path)

    @classmethod
    def append_file_paths_include_subdirs(cls, file_paths, path, ignore_paths):
        paths = list(pathlib.Path(path).iterdir())
        for item in paths:
            file_path = str(item.absolute())
            if file_path not in ignore_paths:
                if item.is_file():
                    file_paths.append(file_path)
                elif item.is_dir():
                    cls.append_file_paths_include_subdirs(file_paths, file_path, ignore_paths)

    @classmethod
    def get_added_removed(cls, previous_file_paths, current_file_paths):
        file_paths_added = current_file_paths.copy()
        file_paths_removed = []

        for previous_file_path in previous_file_paths:
            if previous_file_path in file_paths_added:
                file_paths_added.remove(previous_file_path)
            else:
                file_paths_removed.append(previous_file_path)
        return file_paths_added, file_paths_removed

    @classmethod
    def notify(cls, title_filename, notify_list_filename, paths, previous_date, previous_file_paths,
               current_file_paths):
        title_file_path = Persistence.get_file_path(title_filename)
        title = Persistence.get_string(title_file_path)
        notification_list = cls.load_list(notify_list_filename)
        file_paths_added, file_paths_removed = cls.get_added_removed(previous_file_paths, current_file_paths)

        now_string = PrintHelper.get_now_string()
        subject = f'{title}: {now_string}'
        previous = "Previous"
        previous = f'{" " * (len(title) - len(previous))}{previous}: {previous_date}'
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
            PrintHelper.printInBox(f' No changes since {previous_date}')
            return False

        content = f'{subject}\n{previous}\n{title}\n{ignoring}\n\n'
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

        PrintHelper.printInBox(content)
        PrintHelper.printInBox()
        PrintHelper.printInBox(notification_list)
        gmail = Gmail()
        gmail.send_emails_or_fb(notification_list, subject, content, signature=SIGNATURE)
        return True

    @classmethod
    def load_list(cls, notify_list_filename):
        notification_list = Persistence.get_lines(notify_list_filename)
        return notification_list


if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("Dir Change Notifier")

    dcn = DirChangeNotifier()
    previous_date_string, previous_file_paths = dcn.get_date_previous_file_paths(DIR_TREE_FILENAME)
    paths = Persistence.get_lines("DirChangePaths.txt")
    ignore_paths = Persistence.get_lines("DirChangeIgnorePaths.txt")
    current_file_paths = dcn.get_file_paths(paths, ignore_paths)

    changed = dcn.notify("Title.txt", NOTIFICATION_LIST_FILENAME, paths, previous_date_string, previous_file_paths,
                         current_file_paths)

    if changed or not previous_date_string:
        dcn.save_date_previous_and_file_paths(DIR_TREE_FILENAME, current_file_paths)

    PrintHelper.printInBox()
