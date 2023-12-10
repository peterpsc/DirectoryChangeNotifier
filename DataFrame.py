from datetime import datetime
from os.path import exists

import pandas as pd

import Persistence
import PrintHelper

KEY = "Key"
VALUE = "Value"

DEFAULT_COLUMN_NAMES = [KEY, VALUE]
DEFAULT_FILE_PATH = Persistence.private_file_path("KeyValue.csv")
FILENAME_PREVIOUS_WORD_NUMS = "Previous_Wordle_Word_Num.csv"
WORD_NUM_COLUMNS = ["Word", "Num"]


class DataFrame:

    def __init__(self, col_names=DEFAULT_COLUMN_NAMES, file_path=DEFAULT_FILE_PATH, header=True):
        self.df = None
        self.col_names = col_names
        self.file_path = file_path
        self.header = header
        self.load_dataframe(header=header)

    @classmethod
    def find_private(cls):
        possible_paths = ['../Private/', 'Private/']
        for path in possible_paths:
            if exists(path):
                return path
        return ""

    def load_dataframe(self, header=True):
        if not exists(self.file_path):
            self.df = pd.DataFrame(columns=self.col_names)
            return
        if header == None:
            self.df = pd.read_csv(self.file_path, encoding=Persistence.UTF_8, header=None)
        else:
            self.df = pd.read_csv(self.file_path, encoding=Persistence.UTF_8)
            actual_col_names = list(self.df.columns.values)
            assert self.col_names == actual_col_names

    def save_dataframe(self):
        self.df.to_csv(self.file_path, index=False, columns=self.col_names, encoding=Persistence.UTF_8)

    @classmethod
    def get_now_string(cls):
        date = datetime.now()
        return date.strftime("%Y-%m-%d %H:%M:%S")

    def print_all_data(self):
        PrintHelper.printInBox()
        for line in self.df.values:
            PrintHelper.printInBox(f'{line}')

    def get_row(self, column_name, key, default_key=None):
        if key is None:
            return None
        if not key:
            key = default_key
        results = self.df.loc[self.df[column_name] == key]
        if results.empty:
            return None
        row = results.values[0].tolist()
        return row

    def get_value(self, column_name, key, value_column_name, default_key=None):
        row = self.get_row(column_name, key, default_key=default_key)
        if not row:
            return None
        i = self.col_names.index(value_column_name)
        return row[i]

    def append_row(self, row):
        df = pd.DataFrame(columns=self.col_names)
        if type(row) == list:
            df = pd.DataFrame([row], index=[0])
        elif type(row) == str and len(self.col_names) == 1:
            df = pd.DataFrame([row], index=[0])

        df.columns = self.col_names
        concat = pd.concat([self.df, df])
        self.df = concat

    def prepend_row(self, row):
        df = pd.DataFrame(columns=self.col_names)
        if type(row) == list:
            df = pd.DataFrame([row], index=[0])

        concat = pd.concat([df, self.df])
        self.df = concat


def print_result(key, result):
    if key == None and result == None:
        PrintHelper.printInBox(f'{key} NOT FOUND', PrintHelper.LEFT)
    elif result == None:
        PrintHelper.printInBox(f'"{key}" NOT FOUND', PrintHelper.LEFT)
    else:
        PrintHelper.printInBox(f'"{key}" => "{result}"', PrintHelper.LEFT)


if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("DataFrame.py")
    # file_path = Persistence.resource_file_path(FILENAME_PREVIOUS_WORD_NUMS)
    # df = DataFrame(WORD_NUM_COLUMNS, file_path, header=None)
    # df.print_all_data()
    #
    # list1 = ["after", -1]
    # df.append_row(list1)
    # df.print_all_data()
    #
    # list2 = ["before", -2]
    # df.prepend_row(list2)
    # df.print_all_data()
    #
    # # df.save_dataframe()
    # PrintHelper.printInBox()

    file_path = Persistence.private_file_path("Signatures.csv")
    df = DataFrame(["SHORT", "LONG"], file_path)
    df.print_all_data()

    PrintHelper.printInBox()
    keys = ['upy', 'default', '', None, 'bad']
    for key in keys:
        result = df.get_value("SHORT", key, "LONG")
        print_result(key, result)
    PrintHelper.printInBox()
    for key in keys:
        result = df.get_value("SHORT", key, "LONG", "default")
        print_result(key, result)
    PrintHelper.printInBox()
