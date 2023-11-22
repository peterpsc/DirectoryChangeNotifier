from datetime import datetime

boxes = ["⬜", "🟨", "🟩"]


def printInBoxException(e):
    printInBox(e.args)

def printInBoxWithTime(text):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    printInBox(f"{text}: {now_str}")

def printInBox(txt="", l=80):
    if l != type(int):
        l = 80
    if txt == "":
        print(f"+{'-' * (l - 2)}+")
    else:
        lines = [txt]
        if "\n" in txt:
            lines = txt.split("\n")
        for line in lines:
            ll = l
            for box in boxes:
                if box in line:
                    ll -= 5
                    break
            before = int((ll - 2 - len(line)) / 2)
            after = ll - 2 - before - len(line)
            if before >= 0 and after >= 0:
                print(f"|{' ' * before}{line}{' ' * after}|")
            else:
                print(f"|{line}|")
            pass


if __name__ == '__main__':
    printInBox()
    printInBox("Testing printInBox")
    printInBox("Testing printInBox", "again")
    printInBoxWithTime("Last Run")
    printInBox()