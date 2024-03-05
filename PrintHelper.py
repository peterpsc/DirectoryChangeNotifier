from datetime import datetime

from colorama import Fore

import Persistence
from Substitutions import Substitutions

EMOJIS = ["⬛", "⬜", "🟨", "🟩", "👍", "❤️", "🤝", "😄", "😲", "😢", "😡"]

NONE = 0
LEFT = 1
CENTER = 2
RIGHT = 3
INDENT_1 = 4
INDENT_2 = 5
INDENT_3 = 6
INDENT_4 = 7

IGNORE_COLOR = False

substitutions = Substitutions()

def printInBoxException(e):
    printInBox("Exception:", color=Fore.RED)
    for arg in e.args:
        printInBox(str(arg), force_style=RIGHT, color=Fore.RED)


def printInBoxWithTime(text, dt=datetime.now(), style=LEFT):
    dt_str = get_datetime_string(dt)
    printInBox(f"{text}: {dt_str}", force_style=style)


def get_datetime_string(dt=datetime.now()):
    dt_string = dt.strftime("%A %Y-%m-%d %H:%M:%S")
    return dt_string


def printInBox(txt=None, force_style=None, length=80, color=""):
    if type(length) != int:
        length = 80
    color_end = ""
    if IGNORE_COLOR:
        color = ""
    if color:
        color_end = Fore.RESET
    if txt == None:
        print(f"{color}+{'-' * (length - 2)}+{color_end}")
    else:
        if type(txt) == list:
            txt = "\n".join(txt)
        lines = [txt]
        txt = substitutions.substitute(txt)
        if "\r" in txt:
            txt = txt.replace("\r", "")
        if "\\n" in txt:
            txt = txt.replace("\\n", "\n")
        if "\n" in txt:
            lines = txt.split("\n")
        for line in lines:
            derived_style, text = indent_style(line, length)
            if force_style:
                derived_style = force_style
            before = get_indent(text, derived_style, length)
            after = get_remaining_spaces(before, text, length)
            text = f"|{before}{text}{after}|"
            if color:
                text = f"{color}|{before}{text}{after}|{color_end}"
            print(text)


def indent_style(line, length):
    style = NONE  # blank
    if not line:
        text = ""
    elif line == "---":
        style = NONE  # line
        text = "-" * (length - 2)
    else:
        style = LEFT
        text = line
        last_char = line[-1]
        leading_spaces = 0
        for char in line:
            if char != " ":
                break
            leading_spaces += 1
        if leading_spaces == 0:
            if line[0] == "|" and last_char == "|":
                style = CENTER
                text = line[1:-1]
            elif last_char == "|":
                style = RIGHT
                text = text[:-1]
            else:
                style = LEFT
        elif leading_spaces == 1:
            if last_char == " " or last_char == "|":
                style = CENTER
                text = line[1:-1]
            else:
                style = RIGHT
                text = line[1:]
        else:
            style = leading_spaces - 2 + INDENT_1  # level of indent
            text = line[leading_spaces:]

    return style, text


def get_indent(text, style, length):
    n = 0  # NONE
    if style == LEFT:
        n = 1
    if style == CENTER:  # center
        n = int((length - 2 - len(text)) / 2)
    elif style == RIGHT:  # right
        n = (length - 2 - len(text)) - 1
    elif style >= INDENT_1:  # indent
        n = 3 * (style - INDENT_1 + 1)
    return " " * n


def get_remaining_spaces(before, text, length):
    n = length - 2 - len(before) - len(text)
    emoji_count = 0
    for char in text:
        if char in EMOJIS:
            emoji_count += 1
    # return " " * (n - emoji_count - emoji_count // 4)
    return " " * (n - emoji_count)


def colored(color: str, message: str) -> str:
    return color + message + Fore.RESET


def bright(message: str) -> str:
    return colored(Fore.LIGHTWHITE_EX, message)


def get_now_string():
    date = datetime.now()
    return date.strftime("%Y/%m/%d %H:%M:%S")


if __name__ == '__main__':
    printInBox()
    printInBoxWithTime("PrintHelper.py ")
    lines = Persistence.get_lines("TestPrintHelper.txt", strip=False, path_type=Persistence.RESOURCE_PATH)
    text = "\n".join(lines)
    printInBox(text)
    printInBox()
