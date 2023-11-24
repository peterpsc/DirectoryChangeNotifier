import datetime
import os
import pathlib

import PrintHelper
from Gmail import Gmail

PATHS = [".", ".\\Resources", ".\\Private", "g:\\ /S"]
# PATHS = ["g: /S"]
DIR_TREE_FILENAME = "DirTreeToday.txt"
NOTIFIED = "Notifier <peter.carmichael@comcast.net>"
SIGNATURE = "Change Notifier"


def find_private():
    possible_paths = ['Private', '../Private']
    for path in possible_paths:
        if os.path.exists(path):
            return path + "/"
    return ""


def open_private(filename, mode="r", encoding="utf-8"):
    private_filename = find_private() + filename
    f = open(private_filename, mode, encoding=encoding)
    return f


def get_today_string():
    date_today = datetime.date.today()
    return date_today.strftime('%m/%d/%Y')


def save_date_previous_file_paths(save_file_name, paths):
    file_paths = get_file_paths(paths)

    f = open_private(save_file_name, mode="w")
    f.write(get_today_string() + "\n")
    for file_path in file_paths:
        f.write(file_path + "\n")
    f.close()


def private_exists(filename):
    resource_filename = find_private() + filename
    return os.path.exists(resource_filename)


def get_date_previous_file_paths(save_file_name):
    previous_file_paths = []
    previous_date_string = ""
    if private_exists(save_file_name):
        f = open_private(save_file_name)
        previous_date_string = f.readline().replace("\n", "")
        lines = f.readlines()
        f.close()
        for file_path in lines:
            previous_file_paths.append(file_path.replace("\n", ""))

    return previous_date_string, previous_file_paths


def split_path_options(path_options, default_options=[]):
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


def append_file_paths(file_paths, path):
    paths = list(pathlib.Path(path).iterdir())
    for item in paths:
        if item.is_file():
            file_paths.append(f'{path}\\{item.name}')


def get_file_paths(path_options):
    file_paths = []
    for path_options in path_options:
        path, options = split_path_options(path_options)
        if "S" in options:
            append_file_paths_include_subdirs(file_paths, path)
        else:
            append_file_paths(file_paths, path)
    return file_paths


def append_file_paths_include_subdirs(file_paths, path):
    for root, d_names, f_names in os.walk(path):
        for f in f_names:
            file_path = os.path.join(root, f)
            file_paths.append(file_path)


def get_added_removed(previous_file_paths, current_file_paths):
    file_paths_added = current_file_paths.copy()
    file_paths_removed = []

    for previous_file_path in previous_file_paths:
        if previous_file_path in file_paths_added:
            file_paths_added.remove(previous_file_path)
        else:
            file_paths_removed.append(previous_file_path)
    return file_paths_added, file_paths_removed


def notify(notifier, paths, previous_date, previous_file_paths, current_file_paths):
    file_paths_added, file_paths_removed = get_added_removed(previous_file_paths, current_file_paths)

    if not previous_file_paths:
        PrintHelper.printInBox(f'First time for {paths}')
        return False
    if not file_paths_added and not file_paths_removed:
        PrintHelper.printInBox(f'No changes since {previous_date}')
        return False

    content = ""
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

    subject = f'Changes to {paths}'
    PrintHelper.printInBox(notifier)
    PrintHelper.printInBox(subject)
    print(content)
    gmail = Gmail()
    gmail.send_emails_or_fb(notifier, subject, content, signature=SIGNATURE)
    return True


if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("Dir Change Notifier")

    previous_date_string, previous_file_paths = get_date_previous_file_paths(DIR_TREE_FILENAME)
    current_file_paths = get_file_paths(PATHS)

    changed = notify(NOTIFIED, PATHS, previous_date_string, previous_file_paths, current_file_paths)

    if changed or not previous_date_string:
        save_date_previous_file_paths(DIR_TREE_FILENAME, PATHS)

    PrintHelper.printInBox()
