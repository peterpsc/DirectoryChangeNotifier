from datetime import datetime

import PrintHelper
from os.path import exists

class KeyValue:

    def __init__(self, filename = "KeyValue.txt"):
        self.filename = filename
        self.dict = self.load_data()

    @classmethod
    def find_private(cls):
        possible_paths = ['../Private/', 'Private/']
        for path in possible_paths:
            if exists(path):
                return path
        return ""

    @classmethod
    def open_private(cls, filename, mode="r", encoding="utf-8"):
        if ":" not in filename:
            filename = cls.find_private() + filename
        f = None
        try:
            f = open(filename, mode, encoding=encoding)
        finally:
            return f

    @classmethod
    def private_exists(cls, filename):
        private_filename = cls.find_private() + filename
        return exists(private_filename)

    def load_data(self):
        dict = {}
        file = self.open_private(self.filename)
        if not file:
            PrintHelper.printInBox("NO DATA YET")
        else:
            lines = file.readlines()
            for line in lines:
                pos = line.find("=")
                key = line[:pos].strip()
                value = line[pos+1:].strip()
                dict[key]=value
        return dict

    @classmethod
    def get_now_string(cls):
        date = datetime.now()
        return date.strftime("%Y-%m-%d %H:%M:%S")

    def save(self):
        file = self.open_private(self.filename, mode="w")
        for key in self.dict:
            file.write(f'{key}={self.dict[key]}\n')
        file.close()


def print_data():
    for key in data.dict:
        PrintHelper.printInBox(f'{key}={data.dict[key]}')


if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("KeyValue.py")
    PrintHelper.printInBox()

    data = KeyValue()
    print_data()

    PrintHelper.printInBox()

    data.dict["Notify"] = "FBM:Peter Carmichael,Notified <peter.carmichael@comcast.net>"
    data.dict["last_notified"] = data.get_now_string()
    print_data()

    data.save()
    PrintHelper.printInBox()
