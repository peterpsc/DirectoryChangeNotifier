import datetime
from os.path import exists

import Persistence
import PrintHelper

M_D_Y = "%m/%d/%Y"
DATE_READABLE_FORMAT = "%A %b {S}"

LEFT_CURLY_BRACE = '{'
RIGHT_CURLY_BRACE = '}'

DEFAULT_KEY = "default"
KEY = "KEY"
VALUE = "VALUE"

DEFAULT_COLUMN_NAMES = [KEY, VALUE]


def suffix(n):
    suffixes = ['th', 'st', 'nd', 'rd']

    if n % 100 in range(11, 14):
        return 'th'
    if n % 10 > 3:
        return 'th'
    return suffixes[n % 10]


def custom_strftime(formatter, t):
    return t.strftime(formatter).replace('{S}', str(t.day) + suffix(t.day))


class Substitutions:
    def __init__(self):
        self.substitutions = None
        self.signatures = None
        self.date_today = datetime.date.today()
        self.date_string_today = self.date_today.strftime('%m/%d/%Y')
        self.year_string = self.date_today.strftime('%Y')
        self.month_string = self.date_today.strftime('%m')

    def substitute(self, text, substitutions: dict[str, str] = {}):
        if not text:
            return ""
        if not self.substitutions:
            self.init_substitutions()

        result = text
        for key in self.substitutions:
            while key in result:
                replacement = self.substitutions[key]
                result = result.replace(f"{key}", replacement)

        if substitutions is not None:
            while "{" in result:
                key = result[result.find("{") + 1:result.find("}")]
                substitution = ""
                if key in substitutions:
                    substitution = substitutions[key]
                if key == "date(Scheduled)":
                    substitution, days = self.get_date_scheduled(substitutions)

                result = result.replace(f"{LEFT_CURLY_BRACE}{key}{RIGHT_CURLY_BRACE}", substitution)

        return result

    def init_substitutions(self):
        self.substitutions = Persistence.get_dict("Substitutions.csv")

    def get_signature(self, signature, default_key=DEFAULT_KEY):
        if signature is None:
            return None

        if not self.signatures:
            self.init_signatures()

        if signature == "":
            signature = default_key
        if signature in self.signatures:
            signature = self.signatures[signature]

        return self.substitute(signature)

    def init_signatures(self):
        file_path = Persistence.get_file_path("Signatures.csv")
        if not exists(file_path):
            lines = ["KEY,VALUE", "default,Notifier"]
            Persistence.write_lines(file_path, lines, path_type=Persistence.FILE_PATH)
        self.signatures = Persistence.get_dict(file_path, path_type=Persistence.FILE_PATH)

    def print_all_substitutions(self):
        PrintHelper.printInBox()
        PrintHelper.printInBox("Substitutions.csv")
        if not self.substitutions:
            self.init_substitutions()
        Persistence.print_all_dict(self.substitutions)

    def print_all_signatures(self):
        PrintHelper.printInBox("Signatures.csv")
        if not self.signatures:
            self.init_signatures()
        Persistence.print_all_dict(self.signatures)

    def get_date_scheduled(self, substitutions):
        if "Scheduled" in substitutions:
            scheduled = substitutions["Scheduled"]
            reminder_days_before = substitutions["ReminderDaysBefore"]
            date_scheduled_M_D_Y, reminder_date_M_D_Y = self.get_start_date_reminder_date(scheduled)
            date_scheduled = datetime.datetime.strptime(date_scheduled_M_D_Y, M_D_Y)
            reminder_date = datetime.datetime.strptime(reminder_date_M_D_Y, M_D_Y)
            timedelta = reminder_date - date_scheduled
            date_scheduled_pretty = custom_strftime(DATE_READABLE_FORMAT, date_scheduled)
            return date_scheduled_pretty, timedelta.days

    def get_start_date_reminder_date(self, scheduled, reminder_days_before=None):
        scheduled_date = scheduled.split("/")
        if len(scheduled_date) < 3:
            scheduled_date.append(self.year_string)
        if len(scheduled_date[1]) == 1:
            scheduled_date[1] = "0" + scheduled_date[1]
        if len(scheduled_date[0]) == 0:
            scheduled_date[0] = self.month_string
        elif len(scheduled_date[0]) < 2:
            scheduled_date[0] = "0" + scheduled_date[0]

        date_string = "/".join(scheduled_date)
        reminder_date_string = date_string
        date = None
        try:
            date = datetime.datetime.strptime(date_string, "%m/%d/%Y")
        except:
            if date_string.startswith("02/29"):
                date_string = f"03/01/{self.year_string}"
            else:
                date_string = None
        if date and reminder_days_before:
            date -= datetime.timedelta(days=int(reminder_days_before))
            reminder_date_string = date.strftime("%m/%d/%Y")

        return date_string, reminder_date_string


if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("Substitutions.py")

    for d in range(1, 31 + 1):
        print(f"{d}{suffix(d)}")

    s = Substitutions()

    s.print_all_substitutions()

    PrintHelper.printInBox()
    text = "I <3 you"
    substituted = s.substitute(text)
    PrintHelper.printInBox(text)
    PrintHelper.printInBox(substituted)

    PrintHelper.printInBox()
    text = "I hope you have a hbd"
    substitutions: dict[str, str] = {"Nickname": "Peter the Red"}
    substituted = s.substitute(text, substitutions)
    PrintHelper.printInBox(text)
    PrintHelper.printInBox(substituted)

    PrintHelper.printInBox()
    s.print_all_signatures()
    PrintHelper.printInBox()
    signature = s.get_signature("ptr")
    PrintHelper.printInBox(f'  "ptr" : {signature}')

    PrintHelper.printInBox()
