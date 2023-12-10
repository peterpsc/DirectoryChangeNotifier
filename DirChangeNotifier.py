import os
import pathlib
from os.path import exists

import Persistence
import PrintHelper
from Gmail import Gmail


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
    def get_file_paths(cls, path_options, ignore_paths):
        file_paths = []
        for path_option in path_options:
            if path_option:
                path, option = cls.split_path_options(path_option)
                recursive = False
                if "S" in option:
                    recursive = True
                cls.append_file_paths(file_paths, path, ignore_paths, recursive=recursive)
        return file_paths

    @classmethod
    def append_file_paths(cls, file_paths, root_path, ignore_paths, recursive=False):
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
                    file_paths.append(file_path)
                if item.is_dir():
                    PrintHelper.printInBox(file_path, force_style=PrintHelper.INDENT_1)
                    if recursive:
                        cls.append_file_paths(file_paths, file_path, ignore_paths, recursive)

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
    def notify(cls, title, notification_list, paths, ignore_paths, previous_date, previous_file_paths,
               current_file_paths, signature):
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
        title = self.get_title(notification_name)
        notification_list = self.get_notification_list(notification_name)
        signature = self.get_signature(notification_name)
        try:
            current_file_paths = self.get_file_paths(path_options, ignore_paths)
            changed = self.notify(title, notification_list, path_options, ignore_paths, previous_date_string,
                                  previous_file_paths, current_file_paths, signature)

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
        file_path = self.copy_first_if_missing(notification_name, "_Notification_List.txt")
        return Persistence.get_lines(file_path, Persistence.FILE_PATH)

    def get_signature(self, notification_name):
        file_path = self.copy_first_if_missing(notification_name, "_Signature.txt")
        return "\n".join(Persistence.get_lines(file_path, Persistence.FILE_PATH))

    def copy_first(self, notification_name, end_of_name):
        first_file_path = Persistence.private_file_path(self.notification_names[0] + end_of_name)
        file_path = Persistence.private_file_path(notification_name + end_of_name)
        self.copy_and_edit(first_file_path, file_path)

    def copy_and_edit(self, first_file_path, file_path):
        lines = Persistence.get_lines(first_file_path, Persistence.FILE_PATH)
        Persistence.write_lines(file_path, lines, Persistence.FILE_PATH)
        os.system(f'notepad {file_path}')


if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("Dir Change Notifier")

    notification_names = Persistence.get_lines("NotificationNames.txt")
    dcn = DirChangeNotifier(notification_names)
    dcn.notify_all_names()

    PrintHelper.printInBox()
