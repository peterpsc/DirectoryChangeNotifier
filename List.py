from datetime import datetime

import PrintHelper
from os.path import exists

from KeyValue import KeyValue


class List:

    def __init__(self, filename):
        self.filename = filename
        self.list = self.load_data()


    def load_data(self):
        list = []
        file = KeyValue.open_private(self.filename)
        if not file:
            PrintHelper.printInBox("NO DATA YET")
        else:
            lines = file.readlines()
            for line in lines:
                list.append(line.strip())
        return list

    def save(self):
        file = KeyValue.open_private(self.filename, mode="w")
        for line in self.list:
            file.write(f'{line}\n')
        file.close()

    def add(self, line):
        if line not in data.list:
            data.list.append(line)

    def remove(self, line):
        self.list.remove(line)


def print_data():
    PrintHelper.printInBox()
    for line in data.list:
        PrintHelper.printInBox(f'{line}')


if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("List.py")

    data = List("NotificationList.txt")
    print_data()

    data.add("FBM:Peter Carmichael")
    data.add("Notified <peter.carmichael@comcast.net>")
    print_data()

    data.remove("FBM:Peter Carmichael")
    print_data()

    data.save()
    PrintHelper.printInBox()
