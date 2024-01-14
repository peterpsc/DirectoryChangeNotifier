import csv
import datetime
import os
import random
from os.path import exists
from time import sleep

import clipboard
from selenium.webdriver import Keys

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

the_remote_file_path = ""  # get it from a file


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
    if the_remote_file_path == "":
        file_path = private_file_path(REMOTE_FILE_PATH_TXT)
        remote_file_path = get_string(file_path)
        # if remote_file_path[0] == "A":
        #     remote_file_path = 'G:\My Drive\SourceCode\PycharmProjects\webdriver\\'
        #     write_string(file_path, remote_file_path)
        use_remote = exists(remote_file_path)

        if use_remote:
            the_remote_file_path = remote_file_path
            return remote_file_path + filename

        the_remote_file_path = None
        return None
    return the_remote_file_path + filename


def remote_private_file_path(filename):
    return remote_file_path("Private\\" + filename)


def remote_resources_file_path(filename):
    return remote_file_path("Resources\\" + filename)


def remote_found():
    global the_remote_file_path
    if the_remote_file_path is None:
        return False
    if the_remote_file_path != "":
        return True
    the_remote_file_path = remote_file_path("")
    if the_remote_file_path:
        return True
    return False


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


def get_line(filename, path_type=PRIVATE_PATH, strip=True, only_single_back_slash=True, remove_blank_lines=True):
    return get_lines(filename, path_type=path_type, strip=strip, only_single_back_slash=only_single_back_slash,
                     remove_blank_lines=remove_blank_lines)[0]


def get_list(filename, path_type=PRIVATE_PATH, header=True):
    results = []
    file_path = get_file_path(filename, path_type)
    if exists(file_path):
        with open(file_path, newline='', encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            if header:
                next(reader)  # This skips the first row of the CSV file.

            for row in reader:
                results.append(row)

    return results


def get_dict(filename, path_type=PRIVATE_PATH, header=True):
    file_path = get_file_path(filename, path_type)
    if not exists(file_path):
        line = "KEY,VALUE"
        write_string(file_path, line)

    dict = {}
    if file_path:
        with open(file_path, newline='', encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            if header:
                next(reader)  # This skips the first row of the CSV file.

            for row in reader:
                if len(row) == 2:
                    key = row[0]
                    value = row[1]
                    dict[key] = value

    return dict


def get_dict_rows(filename, path_type=PRIVATE_PATH, col_names=None, header=True):
    file_path = get_file_path(filename, path_type)
    rows = []
    with open(file_path, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=col_names)
        if header:
            next(reader)  # This skips the first row of the CSV file.

        for row_dict in reader:
            rows.append(row_dict)

    return rows


def single_back_slash(line):
    return line.replace("\\\\", "\\")


def write_lines(filename, lines, path_type=PRIVATE_PATH):
    file_path = get_file_path(filename, path_type)
    if file_path[0].upper() == "G":
        raise Exception("Can't write to a Google Drive this way")
    else:
        with open(file_path, mode="w", encoding=UTF_8) as f:
            for line in lines:
                f.write(line + "\n")


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

    if remote_file_path is None:
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


def copy_to_clipboard(text):
    prior_text = None
    while True:
        try:
            prior_text = clipboard.paste()
            clipboard.copy(text)
            return prior_text
        except Exception as e:
            print(".", end="")
            sleep(5)


def get_clipboard_text():
    return clipboard.paste()


def paste_text(element, text, enter=False):
    previous_text = copy_to_clipboard(text)
    element.send_keys(Keys.CONTROL, 'v')
    if enter:
        element.send_keys(Keys.ENTER)
        sleep(1)

    copy_to_clipboard(previous_text)


def updated_today(file_path):
    today = datetime.date.today().strftime('%Y:%m:%d')
    location_file_path = private_file_path(LOCATION_FILENAME)
    location = get_string(location_file_path)
    write_string(file_path, f'{today} {location}')


def get_string(file_path):
    lines = readlines(file_path)
    if len(lines) == 0:
        return ""
    return lines[0]


def write_string(file_path, string):
    if file_path[0].upper() == "G":
        raise Exception("Can't write to a Google Drive this way")
    else:
        with open(file_path, mode="w", encoding="utf-8") as f:
            f.write(string)


def find_in_dict(substitutions, key):
    try:
        return substitutions[key]
    except Exception as e:
        return None


def get_random(cls, list):
    i = random.randrange(len(list))
    return list[i]


def get_stardate():
    return datetime.datetime.now().strftime("%Y%m%d.%H%M")


def print_all_dict(lookup):
    t = type(lookup)
    assert t == dict, "lookup must be a dict"
    for key in lookup:
        PrintHelper.printInBox(f'{key}: {lookup[key]}')


def random_value(from_list):
    assert type(from_list) == list, "from_list must be a list"
    i = random.randrange(len(from_list))
    return from_list[i]


def eliminate_duplicates(list_of_lists):
    hash_list = []
    result = []
    for list in list_of_lists:
        h = 0
        for val in list:
            h += hash(val)
        if h not in hash_list:
            hash_list.append(h)
            result.append(list)
    return result


def dict_to_list(dict_row, col_names):
    result = []
    for col_name in col_names:
        result.append(dict_row[col_name])
    return result


def split(text, sep=","):
    results = []
    while True:
        start = 0
        if len(text) > 0:
            if text[0] == "'":
                end = text.find("'", 1)
                result = text[1:end]
                results.append(result)
                text = text[end + 2:]
                continue
            elif text[0] == '"':
                end = text.find('"', 1)
                result = text[1:end]
                results.append(result)
                text = text[end + 2:]
                continue
            pos = text.find(sep, start)
            if pos < 0:
                results.append(text)
                return results
            else:
                results.append(text[0:pos])
                text = text[pos + 1:]
        else:
            return results


if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("Persistence.py")

    parameters = split("123")
    assert parameters[0] == "123"

    parameters = split("0,1")
    assert parameters[0] == "0", parameters[0]
    assert parameters[1] == "1", parameters[1]

    parameters = split("0,'1,2',3")
    assert parameters[0] == "0", parameters[0]
    assert parameters[1] == "1,2", parameters[1]
    assert parameters[2] == "3", parameters[2]

    parameters = split('0,"1,2",3')
    assert parameters[0] == "0", parameters[0]
    assert parameters[1] == "1,2", parameters[1]
    assert parameters[2] == "3", parameters[2]

    parameters = split('"0,1","2,3",4')
    assert parameters[0] == "0,1", parameters[0]
    assert parameters[1] == "2,3", parameters[1]
    assert parameters[2] == "4", parameters[2]

    file_path = 'C:\\\\Users\\peter\\PycharmProjects\\webdriver\\AudioCreate.py'
    PrintHelper.printInBox(file_path)
    PrintHelper.printInBox(single_back_slash(file_path))

    PrintHelper.printInBox()
    lookup = get_dict("Signatures.csv")
    print_all_dict(lookup)

    PrintHelper.printInBox()
    winning_list = get_lines("Winning.txt", RESOURCE_PATH)
    PrintHelper.printInBox(random_value(winning_list))

    PrintHelper.printInBox()
