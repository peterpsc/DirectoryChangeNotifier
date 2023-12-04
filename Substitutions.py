def substitute(text, full_name, nick_name):
    result = text
    if nick_name == "":
        nick_name = full_name.split(" ")[0]
    if "hbd" in text:
        substitution = "♫♪ Happy Birthday, {Nickname} ♫♪"
        result = result.replace("hbd", substitution)
    if "{Nickname}" in result:
        substitution = f"{nick_name}"
        result = result.replace("{Nickname}", substitution)
    if "{FullName}" in result:
        substitution = f"{full_name}"
        result = result.replace("{FullName}", substitution)
    if "<3" in result:
        result = result.replace("<3", "💘")
    if "aheart" in result:
        result = result.replace("aheart", "💘")
    if "<br>" in result:
        result = result.replace("<br>", "\n")
    if "\\n" in result:
        result = result.replace("\\n", "\n")
    if "m4bwy" in result:
        result = result.replace("m4bwy", "May the 4th Be With You")
    return result


if __name__ == '__main__':
    print(substitute("hbd\n\nLet's get together and celebrate <3", "Dale Miller", "Dale"))
