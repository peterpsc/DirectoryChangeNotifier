import datetime
import os
import random
from collections import OrderedDict
from os.path import exists

import PrintHelper

# TODO downgrade previously chosen words

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

ALPHABETICAL_SCALED_FILENAME = "5-letter-words-guesses_alphabetical_scaled.csv"
PREVIOUS_WORD_NUM_FILE = "Previous_Wordle_Word_Num.csv"
OFFICIAL_WORD_LIST = "Official Wordle Word List.txt"
ALL_WORD_LIST = "5-letter-words.txt"

FILENAME_PREVIOUS_WORD_NUMS = "Previous_Wordle_Word_Num.csv"

LOCATION = "location.txt"
REMOTE_PRIVATE_PATH = "Remote_Private.txt"

class WordListAnalyzer:
    num_word_dict = None
    word_num_dict = None
    WORDLE_START_DATE = datetime.date(2021, 6, 19)  # since 19 June 2021

    def __init__(self, dict_list, num):
        self.set_dictionary(dict_list)
        self.num = num
        self.words = {}
        self.sorted_words = {}
        self.char_counts = {
            "A": [0, 0, 0, 0, 0],
            "B": [0, 0, 0, 0, 0],
            "C": [0, 0, 0, 0, 0],
            "D": [0, 0, 0, 0, 0],
            "E": [0, 0, 0, 0, 0],
            "F": [0, 0, 0, 0, 0],
            "G": [0, 0, 0, 0, 0],
            "H": [0, 0, 0, 0, 0],
            "I": [0, 0, 0, 0, 0],
            "J": [0, 0, 0, 0, 0],
            "K": [0, 0, 0, 0, 0],
            "L": [0, 0, 0, 0, 0],
            "M": [0, 0, 0, 0, 0],
            "N": [0, 0, 0, 0, 0],
            "O": [0, 0, 0, 0, 0],
            "P": [0, 0, 0, 0, 0],
            "Q": [0, 0, 0, 0, 0],
            "R": [0, 0, 0, 0, 0],
            "S": [0, 0, 0, 0, 0],
            "T": [0, 0, 0, 0, 0],
            "U": [0, 0, 0, 0, 0],
            "V": [0, 0, 0, 0, 0],
            "W": [0, 0, 0, 0, 0],
            "X": [0, 0, 0, 0, 0],
            "Y": [0, 0, 0, 0, 0],
            "Z": [0, 0, 0, 0, 0]
        }
        self.totals = {}

    @classmethod
    def get_dictionary(cls, filename=ALPHABETICAL_SCALED_FILENAME):
        dictionary = {}
        file = WordListAnalyzer.open_resource(filename)
        lines = cls.get_lines(file)
        for word in lines:
            scale = 0
            if len(word) < 5:
                continue
            elif len(word) >= 7:
                scale = int(word[6:])
            word = word[:5].upper()
            dictionary[word] = scale

        return dictionary

    @classmethod
    def get_lines(cls, file):
        result = []
        if file:
            lines = file.readlines()
            file.close()
            for line in lines:
                line = line.replace("\n", "")
                if line:
                    result.append(line)
        return result

    @classmethod
    def get_word_list(cls, filename=ALPHABETICAL_SCALED_FILENAME):
        file = cls.open_resource(filename)
        word_list = cls.get_lines(file)
        for word in word_list:
            if len(word) < 5:
                word_list.remove(word)

        word_list = [word[:5].upper() for word in word_list]
        return word_list

    @classmethod
    def find_resources(cls):
        possible_paths = ['../Resources', 'Resources']
        for path in possible_paths:
            if os.path.exists(path):
                return path + "/"
        return ""

    @classmethod
    def open_resource(cls, filename, mode="r", encoding="utf-8"):
        if ":" not in filename:
            filename = cls.find_resources() + filename
        f = None
        try:
            f = open(filename, mode, encoding=encoding)
        finally:
            return f

    @classmethod
    def resource_exists(cls, filename):
        resource_filename = cls.find_resources() + filename
        return exists(resource_filename)

    @classmethod
    def find_private(cls):
        possible_paths = ['../Private', 'Private']
        for path in possible_paths:
            if os.path.exists(path):
                return path + "/"
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

    @classmethod
    def write_word_list(cls, word_list, filename, encoding="utf-8"):
        f = cls.open_resource(filename, "w", encoding=encoding)
        for word in word_list:
            f.write(word + "\n")
        f.close()

    def write_dictionary(self, dictionary, filename, encoding="utf-8"):
        f = self.open_resource(filename, "w", encoding=encoding)
        for word in sorted(dictionary):
            f.write(f"{word},{dictionary[word]}\n")
        f.close()

    def analyze(self):
        self.dictionary_count_chars(self.dictionary)

        for word in self.dictionary:
            self.words[word] = self.value8(word)

        self.sorted_words = sorted(self.words.items(), key=lambda item: item[1], reverse=True)

        return [word[0] for word in self.sorted_words]

    def analyze_uncommon(self, uncommon):
        self.dictionary_count_chars(self.dictionary)

        for word in self.dictionary:
            self.words[word] = self.value_uncommon(word, uncommon)

        self.sorted_words = sorted(self.words.items(), key=lambda item: item[1], reverse=True)

        return [word[0] for word in self.sorted_words]

    def dictionary_count_chars(self, dictionary):
        for word in dictionary:
            self.count_chars(word)
        self.count_totals()

    def count_chars(self, word):
        for i in range(5):
            c = word[i]
            self.count(c, i)

    def count(self, c, i):
        self.char_counts[c][i] += 1

    @classmethod
    def dictionary_keep_letters(cls, dictionary, letters):
        result = {}
        for word in dictionary:
            found = False
            for c in letters:
                if c in word:
                    found = True
                    break
            if found:
                result[word] = dictionary[word]
        return result

    @classmethod
    def word_list_keep_letters(cls, word_list, letters):
        result = []
        letters = letters.upper()
        for word in word_list:
            found = False
            word = word.upper()
            for c in letters:
                if c in word:
                    result.append(word)
                    break

        return result

    @classmethod
    def is_somewhere_else(cls, word, correct, present):
        assert len(present) == 5, f"present must be 5 characters {len(present)}"
        word = cls.space_where_correct(word, correct)
        present = cls.space_where_correct(present, correct)
        contains = ""
        for i in range(5):
            p = present[i]
            if p != " ":
                for j in range(5):
                    w = word[j]
                    if w == " ":
                        continue
                    if j == i and p == w:
                        return 0
                    if p == w:
                        contains += p
        must_contain = present.replace(" ", "")

        if len(must_contain) > len(contains):
            return 0
        for p in contains:
            must_contain = cls.remove_first_char_in(must_contain, p)
        return len(must_contain) == 0

    @classmethod
    def dictionary_remove_absent(cls, dictionary, absent):
        result = {}
        for word in dictionary:
            found = False
            for c in absent:
                if c in word:
                    found = True
                    break
            if found:
                continue
            result[word] = dictionary[word]
        return result

    @classmethod
    def remove_all_chars_in(cls, string, remove):
        result = ""
        for c in string:
            if c not in remove:
                result += c
        return result

    @classmethod
    def shuffle_word_list(cls, word_list):
        random_word_list = word_list.copy()
        random.shuffle(random_word_list)
        return random_word_list

    @classmethod
    def remove_first_char_in(cls, string, remove):
        result = ""
        for i in range(len(string)):
            c = string[i]
            if c != remove:
                result += c
            else:
                result += string[i + 1:]
                return result

        return result

    def print_data(self):
        for c in ALPHABET:
            print(f"\'{c}\': {self.char_counts[c]} {self.totals[c]}")
        self.print_sorted_words()

    def print_sorted_words(self):
        for data in self.sorted_words:
            word = data[0]
            value = data[1]
            print(
                f"{word} {value} {self.value1(word)} {self.value2(word)} {self.value3(word)} {self.value4(word)} {self.value5(word)} {self.value6(word)} {self.value7(word)}")

    def total(self, c):
        return sum(self.char_counts[c])

    def value1(self, word):
        val = 0
        for i in range(5):
            c = word[i]
            val += self.char_counts[c][i]
        return val

    def value2(self, word):
        val = 0
        for i in range(5):
            c = word[i]
            val += self.char_counts[c][i]
        val *= self.letter_count(word)
        return val

    def value3(self, word):
        val = 0
        scale = 100
        for i in range(5):
            c = word[i]
            val += self.char_counts[c][i]
            val += self.totals[c] / scale
        val *= self.letter_count(word)
        return val

    def value4(self, word):
        val = 0
        scale = 20
        for i in range(5):
            c = word[i]
            val += self.char_counts[c][i]
            val += self.totals[c] / scale
        val *= self.letter_count(word)
        return val

    def value5(self, word):
        val = 0
        scale = 20
        for i in range(5):
            c = word[i]
            val += self.char_counts[c][i]
            val += self.totals[c] / scale
        val += self.letter_count(word) * 10
        return val

    def value6(self, word):
        val = 0
        scale = 20
        for i in range(5):
            c = word[i]
            val += self.char_counts[c][i]
            val += self.totals[c] / scale
        val += self.letter_count(word) * 10

        val += self.dictionary[word]
        return val

    def value7(self, word):
        val = 0
        scale = 20
        for i in range(5):
            c = word[i]
            val += self.char_counts[c][i]
            val += self.totals[c] / scale
        val += self.letter_count(word) * 100

        val += self.dictionary[word]
        return val

    def value8(self, word):
        val = self.value7(word)
        val -= self.downgrade_if_previous_word(word, self.num)
        return val

    @classmethod
    def sort_from_dictionary(cls, dict_list, num):
        analyzer = WordListAnalyzer(dict_list, num)
        sorted_word_list = analyzer.analyze()
        return sorted_word_list

    @classmethod
    def dictionary_remove_all_char_at(cls, dictionary, c, i):
        result = {}
        for word in dictionary:
            if c != word[i]:
                result[word] = dictionary[word]
        return result

    def letter_count(self, word):
        word = self.remove_duplicate_chars(word)
        return len(word)

    @classmethod
    def remove_duplicate_chars(cls, string):
        return "".join(OrderedDict.fromkeys(string))

    def last_letter_s(self):
        result = []
        for word in self.dictionary:
            if word[4] == 's':
                result.append(word)
        return result

    def same_values6(self, dictionary):
        result = {}
        previous_value = 0
        same_value = -1
        previous_word = ""
        sorted_list = WordListAnalyzer.sort_from_dictionary(dictionary)
        for word in sorted_list:
            next_value = self.value7(word)
            if previous_value == next_value:
                result[previous_word] = previous_value
                same_value = previous_value
            elif same_value == previous_value and next_value != same_value:
                result[previous_word] = previous_value
                same_value = -1
            previous_value = next_value
            previous_word = word
        return result

    def add_word_to_dictionary(self, actual):
        official_word_list = self.get_word_list(OFFICIAL_WORD_LIST)
        official_word_list.append(actual)
        self.write_word_list(sorted(official_word_list), OFFICIAL_WORD_LIST)

        scaled_dict = self.get_dictionary()
        scaled_dict[actual] = 3
        self.write_dictionary(scaled_dict, ALPHABETICAL_SCALED_FILENAME)

    @classmethod
    def print_dictionary(cls, dictionary):
        print(len(dictionary), " ", dictionary)

    @classmethod
    def print_list(cls, word_list):
        print(f"{len(word_list)}) {word_list}")

    def count_totals(self):
        for c in ALPHABET:
            self.totals[c] = self.total(c)

    @classmethod
    def uncommon_letters(cls, choices):
        uncommon = ""
        analyzer = WordListAnalyzer(choices)
        analyzer.dictionary_count_chars(analyzer.dictionary)
        for c in ALPHABET:
            if analyzer.totals[c] == 1:
                uncommon += c
        return uncommon

    def value_uncommon(self, word, uncommon):
        val = self.dictionary[word]
        val = self.unique_chars_in(word, uncommon)
        return val

    @classmethod
    def unique_chars_in(cls, word, uncommon):
        val = 0
        for c in uncommon:
            if c in word:
                val += 1
        return val

    def set_dictionary(self, dict_list):
        if type(dict_list) == list:
            result = {}
            for word in dict_list:
                result[word] = 0
            self.dictionary = result
        else:
            self.dictionary = dict_list

    @classmethod
    def sort_alphabetically(cls, word_list):
        return sorted(word_list)

    @classmethod
    def get_previous_word(cls, number):
        num_word_dict, word_num_dict = cls.get_num_word_dicts()
        return num_word_dict[number]

    @classmethod
    def get_random_word_in_file(cls, file):
        word_list = cls.get_word_list(file)
        return cls.get_random_word(word_list)

    @classmethod
    def get_random_word(cls, word_list):
        i = random.randrange(len(word_list))
        return word_list[i]

    @classmethod
    def get_latest_number(cls):
        word_num_dict, num_word_dict = cls.get_num_word_dicts()
        for num in word_num_dict:
            break

        num_today = cls.number_today()
        if num != num_today:
            PrintHelper.printInBox(f"Today's number {num_today} not found")
        return num

    @classmethod
    def number_today(cls):
        today = datetime.date.today()
        number = today - cls.WORDLE_START_DATE
        return number.days

    @classmethod
    def get_date_string(cls, num):
        date = cls.WORDLE_START_DATE + datetime.timedelta(days=num)
        return date.strftime("%a %d, %b %Y")

    @classmethod
    def combine(cls, all_word_list, official_word_list):

        for word in official_word_list:
            if word not in all_word_list:
                print(word)
                all_word_list.append(word)

        return all_word_list

    @classmethod
    def apply(cls, wordlist, command):
        result = []
        for word in wordlist:
            result.append(command(word))
        return result

    @classmethod
    def word_today(cls):
        today = cls.number_today()
        word = cls.get_num_word_dicts()[today]
        return word

    @classmethod
    def random_word(cls):
        official_word_list = WordListAnalyzer.get_word_list(OFFICIAL_WORD_LIST)
        word = cls.get_random_word(official_word_list)
        return word

    @classmethod
    def space_where_correct(cls, word, correct):
        result = ""
        for i in range(5):
            if correct[i] == " ":
                result += word[i]
            else:
                result += " "
        return result

    @classmethod
    def has_updated_today(cls, filename, remote_filename):
        file = cls.open_private(filename)
        date_last_updated = WordListAnalyzer.get_lines(file)

        remote_file = open(remote_filename, encoding="utf-8")
        remote_date_last_updated = WordListAnalyzer.get_lines(remote_file)
        today = datetime.date.today().strftime('%Y:%m:%d')

        if len(date_last_updated) > 0 and today == date_last_updated[0][:10]:
            PrintHelper.printInBox(f"already done today {date_last_updated[0]}")
            return True
        if len(remote_date_last_updated) > 0 and today == remote_date_last_updated[0][:10]:
            PrintHelper.printInBox(f"already done today {remote_date_last_updated[0]}")
            return True
        return False

    @classmethod
    def updated(cls, filename):
        today = datetime.date.today().strftime('%Y:%m:%d')
        file = WordListAnalyzer.open_private(filename, mode='w')
        location = WordListAnalyzer.get_location()
        file.write(f"{today} {location}")
        file.close()

    @classmethod
    def get_location(cls):
        file = WordListAnalyzer.open_private(LOCATION)
        lines = WordListAnalyzer.get_lines(file)
        return lines[0].strip()

    @classmethod
    def get_remote_private_path(cls):
        file = WordListAnalyzer.open_private(REMOTE_PRIVATE_PATH)
        lines = WordListAnalyzer.get_lines(file)
        return lines[0].strip()

    @classmethod
    def get_day_of_week(cls):
        return datetime.date.today().strftime('%A')

    @classmethod
    def get_num_word_dicts(cls):
        if cls.word_num_dict:
            return cls.num_word_dict, cls.word_num_dict
        num_word_dict = {}
        word_num_dict = {}
        file = cls.open_resource(PREVIOUS_WORD_NUM_FILE)
        previous_word_list = cls.get_lines(file)
        for wn in previous_word_list:
            word_num = wn.split(",")
            num_word_dict[int(word_num[1])] = word_num[0]
            word_num_dict[word_num[0]] = int(word_num[1])
        cls.num_word_dict = num_word_dict
        cls.word_num_dict = word_num_dict
        return num_word_dict, word_num_dict

    @classmethod
    def get_most_recent_num(cls):
        for num in cls.get_num_word_dicts():
            return num

    def downgrade_if_previous_word(self, word, num):
        try:
            word_num = self.word_num_dict[word]
            if word_num and word_num < num:
                return 0  # TODO 1 it seemed to make things worse
            else:
                return 0
        except:
            return 0

    @classmethod
    def get_number_for_word(cls, actual):
        try:
            return cls.word_num_dict[actual]
        except KeyError:
            return None

    @classmethod
    def save_num_word_dicts(cls, num, word):
        try:
            w = WordListAnalyzer.num_word_dict[num]
            return
        except KeyError:
            WordListAnalyzer.num_word_dict[num] = word
            WordListAnalyzer.word_num_dict[word] = num

        f = WordListAnalyzer.open_resource(FILENAME_PREVIOUS_WORD_NUMS, "w")
        for i in range(num, -1, -1):
            f.write(f'{WordListAnalyzer.num_word_dict[i]},{i}\n')
        f.close()


if __name__ == '__main__':
    print(WordListAnalyzer.get_day_of_week())
    # print(f"Upper case {OFFICIAL_WORD_LIST}")
    # command = lambda x: x.upper()
    # official_word_list = WordListAnalyzer.get_word_list(OFFICIAL_WORD_LIST)
    # official_word_list = WordListAnalyzer.apply(official_word_list, command)
    # WordListAnalyzer.write_word_list(official_word_list, OFFICIAL_WORD_LIST)
    #
    # print(f"Upper case {ALL_WORD_LIST}")
    # all_word_list = WordListAnalyzer.get_word_list(ALL_WORD_LIST)
    # count_before = len(all_word_list)
    # combined = WordListAnalyzer.combine(all_word_list, official_word_list)
    # count_after = len(combined)
    # combined = WordListAnalyzer.apply(combined, command)
    # WordListAnalyzer.write_word_list(sorted(combined), ALL_WORD_LIST)

    latest_number = WordListAnalyzer.get_latest_number()
    print(f"Latest number = {latest_number}")
    word = WordListAnalyzer.word_today()
    print(f"word_today = {word}")
    print(f"Date today = {WordListAnalyzer.get_date_string(latest_number)}")
    print(f"First Wordle = {WordListAnalyzer.get_date_string(0)}")
