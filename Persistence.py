import datetime
import os
import random
from os.path import exists

import PrintHelper

REMOTE_FILE_PATH_TXT = "RemoteFilepath.txt"
LOCATION_FILENAME = "location.txt"
UTF_8 = "utf-8"

FILE_PATH = 0
PRIVATE_PATH = 1
RESOURCE_PATH = 2
REMOTE_PATH = 3
REMOTE_PRIVATE_PATH = 4
REMOTE_RESOURCES_PATH = 5

global the_remote_file_path


def find_private():
    possible_paths = ['../Private/', 'Private/']
    for path in possible_paths:
        if exists(path):
            return path
    return ""


def find_resource():
    possible_paths = ['../Resources/', 'Resources/']
    for path in possible_paths:
        if exists(path):
            return path
    return ""


def private_file_path(filename):
    return find_private() + filename


def resource_file_path(filename):
    return find_resource() + filename


def remote_file_path(filename):
    global the_remote_file_path
    try:
        return the_remote_file_path + filename
    except NameError as e:
        the_remote_file_path = get_string(private_file_path(REMOTE_FILE_PATH_TXT))
        return the_remote_file_path + filename


def remote_private_file_path(filename):
    return remote_file_path("Private\\" + filename)


def remote_resources_file_path(filename):
    return remote_file_path("Resources\\" + filename)


def remote_found():
    file_path = remote_private_file_path(REMOTE_FILE_PATH_TXT)
    return exists(file_path)


def readlines(file_path, strip=True):
    assert exists(file_path), f'Missing File: {file_path}'

    f = open(file_path, mode="r", encoding=UTF_8)
    lines = f.readlines()
    f.close()

    if strip:
        result = []
        for line in lines:
            result.append(line.strip())
        return result
    return lines


def get_file_path(filename, path_type=PRIVATE_PATH):
    if path_type == FILE_PATH:
        return filename
    elif path_type == PRIVATE_PATH:
        return private_file_path(filename)
    elif path_type == RESOURCE_PATH:
        return resource_file_path(filename)
    elif path_type == REMOTE_PATH:
        return remote_file_path(filename)
    elif path_type == REMOTE_PRIVATE_PATH:
        return remote_private_file_path(filename)
    elif path_type == REMOTE_RESOURCES_PATH:
        return remote_resources_file_path(filename)
    else:
        raise Exception("Invalid path")


def full_file_path(file_path):
    if exists(file_path):
        full_file_path = os.path.abspath(file_path)
        return single_back_slash(full_file_path)
    return None


def get_lines(filename, path_type=PRIVATE_PATH, strip=True, only_single_back_slash=True, remove_blank_lines=True):
    file_path = get_file_path(filename, path_type=path_type)
    lines = readlines(file_path, strip=strip)
    i = 0
    for line in lines:
        if line == "\n":
            lines[i] = line[:-1]
        if only_single_back_slash:
            lines[i] = single_back_slash(lines[i])
        i += 1

    if remove_blank_lines:
        while True:
            if "" in lines:
                lines.remove("")
            else:
                break
    return lines


def single_back_slash(line):
    return line.replace("\\\\", "\\")


def write_lines(filename, lines, path_type=PRIVATE_PATH):
    file_path = get_file_path(filename, path_type)
    f = open(file_path, mode="w", encoding=UTF_8)
    for line in lines:
        f.write(line + "\n")
    f.close()


def append_lines(filename, lines, path=PRIVATE_PATH):
    file_path = get_file_path(filename, path)
    f = open(file_path, mode="a", encoding=UTF_8)
    for line in lines:
        f.write(line + "\n")
    f.close()


def replace_lines(filename, lines, path=PRIVATE_PATH):
    file_path = get_file_path(filename, path)
    f = open(file_path, mode="w")
    for line in lines:
        f.write(line + "\n")
    f.close()


def prepend_lines(filename, lines, path=PRIVATE_PATH):
    previous_lines = get_lines(filename, path)
    result = lines
    if len(previous_lines) > 0:
        for line in previous_lines:
            result.append(line)
    replace_lines(filename, lines, path)


def get_credentials(credential_filename):
    file_path = get_file_path(credential_filename, PRIVATE_PATH)
    f = open(file_path)
    username = f.readline()
    password = f.readline()

    f.close()
    return username, password

def has_updated_today(file_path, remote_file_path):
    date_last_updated = get_string(file_path)
    today = datetime.date.today().strftime('%Y:%m:%d')

    if not exists(remote_file_path):
        PrintHelper.printInBoxException(Exception("remote not found"))
    else:
        remote_date_last_updated = get_string(remote_file_path)
        if len(remote_date_last_updated) > 0 and today == remote_date_last_updated[:10]:
            PrintHelper.printInBox(f" already done today {remote_date_last_updated} ")
            return True
    if len(date_last_updated) > 0 and today == date_last_updated[:10]:
        PrintHelper.printInBox(f" already done today {date_last_updated} ")
        return True

    return False


def updated_today(file_path):
    today = datetime.date.today().strftime('%Y:%m:%d')
    location_file_path = private_file_path(LOCATION_FILENAME)
    location = get_string(location_file_path)
    write_string(file_path, f'{today} {location}')


def get_string(file_path):
    return readlines(file_path)[0]


def write_string(file_path, string):
    f = open(file_path, mode="w", encoding=UTF_8)
    f.write(string)
    f.close()


def find_in_dict(substitutions, key):
    try:
        return substitutions[key]
    except Exception as e:
        return None

class PersistentSet:

    def __init__(self, file_path):
        self.set = []
        self.file_path = file_path
        self.load_data()

    def load_data(self):
        self.set = []
        if not exists(self.file_path):
            PrintHelper.printInBox("NO DATA YET")
        else:
            self.readlines(self.file_path)

    def save(self):
        with open(self.file_path, mode="w", encoding=UTF_8) as file:
            for line in self.set:
                file.write(line + "\n")

    def add(self, line):
        line = line.strip()
        if line not in self.set:
            self.set.append(line)

    def remove(self, line):
        self.set.remove(line)

    def readlines(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, encoding=UTF_8) as file:
                while True:
                    line = file.readline()
                    if not line:
                        break
                    self.add(line)

    def print(self):
        PrintHelper.printInBox()
        for line in self.set:
            PrintHelper.printInBox(f'{line}')

    def random(self):
        length = self.len()
        value = ""
        if length > 0:
            rnd = random.randrange(0, length)
            value = self.set[rnd]
        return value

    def len(self):
        return len(self.set)


if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("Persistence.py")

    s = PersistentSet(private_file_path("NotificationList.txt"))
    s.print()

    s.add("FBM:Peter Carmichael")
    s.add("Notified <peter.carmichael@comcast.net>")
    s.print()
    s.save()

    s = PersistentSet(private_file_path("NotificationList.txt"))
    s.print()

    s.remove("FBM:Peter Carmichael")
    s.print()

    for i in range(10):
        s.add(f'{i}')
    for i in range(10):
        s.add(f'{i}')

    s.save()
    s.print()

    PrintHelper.printInBox()
    count = 30
    PrintHelper.printInBox(f'Random {count}')
    for i in range(count):
        PrintHelper.printInBox(s.random())

    for i in range(10):
        s.remove(f'{i}')

    s.save()
    s.print()

    file_path = 'C:\\\\Users\\peter\\PycharmProjects\\webdriver\\AudioCreate.py'
    PrintHelper.printInBox(file_path)
    PrintHelper.printInBox(single_back_slash(file_path))

    PrintHelper.printInBox()
