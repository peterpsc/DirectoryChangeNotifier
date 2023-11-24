import csv
import datetime
import os
from time import sleep

import clipboard
from pyperclip import PyperclipWindowsException
from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import PrintHelper
import Substitutions
from WordListAnalyzer import WordListAnalyzer
from WordleEngine import WordleEngine
from WordleHelper import WordleHelper

URL = "https://www.facebook.com/?sk=h_chr"
HOME_URL = "https://www.facebook.com/"
BIRTHDAYS_URL = "https://www.facebook.com/events"
MESSAGES_URL = "https://www.facebook.com/messages/t"
GROUPS_URL = "https://www.facebook.com/groups/"
LOGIN_FILENAME = "facebook_login.html"
FILENAME = "facebook.html"
CREDENTIAL_FILENAME = "fb_login.txt"
NICKNAMES_FILENAME = "Nicknames.csv"
NICKNAMES_SORTED_FILENAME = "Nicknames.csv"
NICKNAMES_COLUMNS = ["FullName", "Nickname", "Message"]
DEADPOOL_FILENAME = "Deadpool.txt"  # for you Clock
FRIENDS_POSTED_TODAY_FILENAME = "FriendsPostedToday.csv"
FRIENDS_POSTED_TODAY_COLUMNS = ["FullName", "Date"]
BIRTHDAYS_POSTED_TODAY_FILENAME = "BirthdaysPostedToday.csv"
BIRTHDAYS_POSTED_TODAY_COLUMNS = ["FullName", "Nickname", "Message", "Date"]

EMOJI_NAMES = ["Like", "Love", "Care", "Haha", "Wow", "Sad", "Angry"]
EMOJIS_WIDTH = 580
SCALE = 1.75


def create_emoji_offsets():
    offsets = []
    start = 0

    delta = EMOJIS_WIDTH / len(EMOJI_NAMES) / SCALE
    for i in range(len(EMOJI_NAMES)):
        offsets.append(start + i * delta)
    return offsets


EMOJI_OFFSETS = create_emoji_offsets()
EMOJIS = ["👍", "❤️", "🤝", "😄", "😲", "😢", "😡"]


# TODO post a comment to Friends who have already posted today's Wordle
class Facebook:
    def post_text_message(self, text, message=""):
        """Post the clipboard to my FB page"""
        self.login(URL)

        ok = self.driver.find_element(By.XPATH, '//span[text()="OK"]')
        self.driver.execute_script('arguments[0].scrollIntoView();', ok)
        post = self.driver.find_element(By.XPATH, '//span[text()="What\'s on your mind, Peter?"]')
        # self.driver.execute_script('arguments[0].scrollIntoView();', post)
        size = post.size
        w, h = size['width'], size['height']

        action = webdriver.ActionChains(self.driver)
        action.move_to_element(post)
        # action.move_by_offset(w / 4, h / 4)  # center on the button
        action.perform()
        self.click(post)
        sleep(1)

        post_form = self.driver.find_element(By.TAG_NAME, 'form')
        entry = post_form.find_element(By.XPATH, '//div[@aria-label="What\'s on your mind, Peter?"]')
        full_text = text + "\n" + message + "\n(posted by WordleBot the Red)"

        clipboard.copy(full_text)
        entry.send_keys(Keys.CONTROL, 'v')
        sleep(2)

        post_button = post_form.find_element(By.XPATH, '//span[text()="Post"]')
        self.driver.execute_script('arguments[0].scrollIntoView();', post_button)
        self.click(post_button)
        sleep(1)

        self.driver.close()

    @classmethod
    def find_resources(cls):
        possible_paths = ['Resources', '../Resources']
        for path in possible_paths:
            if os.path.exists(path):
                return path + "/"
        return ""

    @classmethod
    def find_private(cls):
        possible_paths = ['Private', '../Private']
        for path in possible_paths:
            if os.path.exists(path):
                return path + "/"
        return ""

    @classmethod
    def open_resource(cls, filename, mode="r", encoding="utf-8"):
        resource_file_path = cls.find_resources() + filename
        f = open(resource_file_path, mode, encoding=encoding)
        return f

    @classmethod
    def open_private(cls, filename, mode="r", encoding="utf-8"):
        private_file_path = cls.find_private() + filename
        f = open(private_file_path, mode, encoding=encoding)
        return f

    def login(self, url):
        self.driver = webdriver.Firefox()
        driver = self.driver
        driver.maximize_window()
        driver.get(url)
        # sleep(5)
        # assert 'Facebook - log in or sign up' == driver.title

        username, password = self.getCredentials()

        email_element = self.driver.find_element(By.ID, "email")
        email_element.send_keys(username)
        password_element = self.driver.find_element(By.ID, "pass")
        password_element.send_keys(password)
        log_in_element = self.driver.find_element(By.NAME, "login")
        self.click(log_in_element)
        sleep(5)

    def login_birthdays(self):
        self.nick_names = self.get_nickname_messages()
        self.deadpool = self.get_deadpool()
        driver = webdriver.Firefox()
        self.driver = driver
        driver.maximize_window()
        driver.set_page_load_timeout(60)
        driver.get(BIRTHDAYS_URL)

        username, password = self.getCredentials()
        email_element = self.wait_for_element(f'//input[@aria-label="Email or phone"]', 60)
        password_element = self.wait_for_element(f'//input[@aria-label="Password"]', 60)
        email_element.send_keys(username)
        sleep(1)
        password_element.send_keys(password)
        login_button = self.wait_for_element(f'//form//span[text()="Log In"]', 60)
        # login_button.click() # doesn't work???
        password_element.send_keys(Keys.TAB, Keys.ENTER)  # this works

        birthdays_element = self.wait_for_element(f'//span[text()="Birthdays"]', 60)
        self.click(birthdays_element)

    def getCredentials(self, credential_filename=CREDENTIAL_FILENAME):
        f = self.open_private(credential_filename)
        username = f.readline()
        password = f.readline()
        f.close()
        return username, password

    def click(self, element, timeout=10 * 60):
        while True:
            try:
                element = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(element))
                element.click()
                return element
            except Exception as e:
                PrintHelper.printInBoxException(e)
                sleep(30)
        """ ALWAYS WAIT FOR SOMETHING AFTER CLICKING """

    def post_comments_to_friends_who_posted(self, wordle_text, commit=True):
        """ Search "Wordle ###" Posts/Recent Posts/Your Friends """
        num, tries, hard_mode = WordleHelper.get_wordle_num_tries_hardmode(wordle_text)

        wordle_text = WordleHelper.add_signature_to_text(wordle_text)
        file_path = self.find_private() + FRIENDS_POSTED_TODAY_FILENAME
        remote_file_path = WordListAnalyzer.get_remote_private_path() + FRIENDS_POSTED_TODAY_FILENAME
        friend_names_posted_today, today = self.get_friend_names_posted_today(file_path, remote_file_path)

        self.login_friends_who_posted(num)
        try:
            feed_element = self.wait_for_element(f'//div[@role="feed"]', 10)

            if not self.scroll_to_end_of_results():
                self.end_friends_posted_today(friend_names_posted_today, 0)
                return
        except Exception as e:
            PrintHelper.printInBox("No friends posted yet")
            self.close()
            return

        friend_elements = feed_element.find_elements(By.XPATH, f'./div')
        comment_buttons = feed_element.find_elements(By.XPATH, f'//div[@aria-label="Leave a comment"]/..')
        emoji_elements = self.get_emoji_elements(comment_buttons)
        num_comment_buttons = len(comment_buttons)
        num_comments = 0

        try:
            friend_names = self.get_friend_names(friend_elements)
            num_friends = len(friend_names)
            assert num_friends > 0, f"No friends posted Wordle {num} yet"
            assert num_friends == num_comment_buttons, f"Not the same number of friends({num_friends}) and comments({num_comment_buttons})"

            numbers, their_tries, hard_modes = self.get_friend_results(friend_elements, num)

            for i in range(num_friends):
                friend_element = friend_elements[i]
                friend_name = friend_names[i]

                self.driver.execute_script("arguments[0].scrollIntoView();", friend_element)

                their_num = numbers[i]
                theirs = their_tries[i]
                hard_mode = hard_modes[i]
                emoji_element = emoji_elements[i]

                status = WordleEngine.get_status_for_count_string(theirs, hard_mode)
                comment = f'{friend_name} {status}'
                if their_num != num or theirs == 0:
                    continue
                elif theirs <= 2:
                    self.emoji_friend(emoji_element, "Wow", comment)
                elif theirs < tries:
                    self.emoji_friend(emoji_element, "Care", comment)
                elif theirs == tries:
                    self.emoji_friend(emoji_element, "Like", comment)
                elif theirs == 7:
                    self.emoji_friend(emoji_element, "Sad", comment)
                else:
                    PrintHelper.printInBox(f'{comment}')

                if self.has_friend_been_posted_today(friend_names_posted_today, friend_name):
                    continue

                if theirs < tries < 5:
                    comment_elements = friend_element.find_elements(By.XPATH, f'//div[@aria-label="Write a comment…"]')

                    comment_button = comment_buttons[i]
                    self.click(comment_button)
                    dialog_comment_element = self.get_dialog_comment_element(friend_element, comment_elements)

                    if dialog_comment_element:  # dialog
                        dialog_elements = self.driver.find_elements(By.XPATH,
                                                                    f'//h2[contains(., "\'s Post")]/../../../../..')
                        assert len(dialog_elements) == 1, f"dialog error {len(dialog_elements)}"
                        dialog_element = dialog_elements[0]

                        num_comments += self.add_comment_from_dialog(dialog_element, dialog_comment_element,
                                                                     friend_names_posted_today, friend_name, today,
                                                                     theirs, tries,
                                                                     wordle_text, commit)
                    else:  # directly
                        num_comments += self.add_comment_directly(friend_element,
                                                                  friend_names_posted_today, friend_name, today,
                                                                  theirs, tries,
                                                                  wordle_text, commit)
                pass
        except Exception as e:
            PrintHelper.printInBoxException(e)
        finally:
            self.end_friends_posted_today(friend_names_posted_today, num_comments)

    def get_dialog_comment_element(self, friend_element, comment_elements):
        sleep(1)
        dialog_comment_element = None
        dialog_comment_elements = friend_element.find_elements(By.XPATH, f'//div[@aria-label="Write a comment…"]')
        if len(dialog_comment_elements) > len(comment_elements):
            return dialog_comment_elements[-1]
        return dialog_comment_element

    def end_friends_posted_today(self, friend_names_posted_today, num_comments):
        file_path = self.find_private() + FRIENDS_POSTED_TODAY_FILENAME
        self.write_friend_names_posted_today(friend_names_posted_today, file_path)

        remote_file_path = WordListAnalyzer.get_remote_private_path() + FRIENDS_POSTED_TODAY_FILENAME
        self.write_friend_names_posted_today(friend_names_posted_today, remote_file_path)
        PrintHelper.printInBox(self.num_comments_string(num_comments))
        self.close()

    def get_emoji_elements(self, comment_buttons):
        emoji_elements = []
        for comment_button in comment_buttons:
            emoji_element = comment_button.find_element(By.XPATH, f'preceding-sibling::div[1]')
            emoji_elements.append(emoji_element)
        return emoji_elements

    def emoji_friend(self, emoji_element, emoji_type, comment):
        a = ActionChains(self.driver)
        a.move_to_element(emoji_element).perform()
        sleep(1)
        size = emoji_element.size
        width = size["width"]
        dx = self.get_emoji_x_offset(emoji_type, width)
        dy = -30
        a.move_to_element_with_offset(emoji_element, dx, dy).perform()
        a.click().perform()
        emoji = self.get_emoji(emoji_type)
        PrintHelper.printInBox(f'{comment} {emoji}')

    def get_emoji_x_offset(self, emoji_type, width):
        EMOJI_BORDER = 7
        for i in range(len(EMOJI_NAMES)):
            if emoji_type == EMOJI_NAMES[i]:
                return EMOJI_OFFSETS[i] - width / 2 + EMOJI_BORDER

        raise Exception("Not a valid emoji_type", emoji_type)

    def get_emoji(self, emoji_type):
        for i in range(len(EMOJI_NAMES)):
            if emoji_type == EMOJI_NAMES[i]:
                return EMOJIS[i]

        raise Exception("Not a valid emoji_type", emoji_type)

    def add_comment_from_dialog(self, dialog_element, comment_element,
                                friend_names_posted_today, friend_name, today,
                                their_tries, tries, wordle_text, commit):
        self.assertIsFriendName(dialog_element, friend_name)
        if their_tries < tries:
            self.comment_you_beat_me(comment_element, wordle_text)
            if commit:
                comment_element.send_keys(Keys.ENTER)
                friend_names_posted_today[friend_name] = [today]
                PrintHelper.printInBox(f'{friend_name} {their_tries} < {tries}')
                comment_element.send_keys(Keys.ESCAPE)
                return 1
            else:
                comment_element.send_keys(Keys.ESCAPE)
                button_elements = self.driver.find_elements(By.XPATH, f'//span[text()="Leave Page"]')
                if len(button_elements) > 0:
                    self.click(button_elements[0])
                return 0

    def add_comment_directly(self, friend_element,
                             friend_names_posted_today, friend_name, today,
                             their_tries, tries,
                             wordle_text, commit):
        comment_element = friend_element.find_element(By.XPATH, f'.//div[@aria-label="Write a comment…"]')
        if their_tries < tries:
            self.assertIsFriendName(friend_element, friend_name)
            self.comment_you_beat_me(comment_element, wordle_text)
        if commit:
            comment_element.send_keys(Keys.ENTER)
            friend_names_posted_today[friend_name] = [today]
            PrintHelper.printInBox(f'{friend_name} {their_tries} < {tries}')
            return 1
        return 0

    def comment_you_beat_me(self, comment_element, wordle_text):
        comment = "You beat me [T][O][D][A][Y]!\n"
        text = comment + wordle_text
        clipboard.copy(text)
        comment_element.send_keys(Keys.CONTROL, "v")
        sleep(1)

    def get_their_wordle_from_dialog(self):
        their_message_element = self.driver.find_element(By.XPATH,
                                                         f'/html/body/div[1]/div/div[1]/div/div[4]/div/div/div[1]/div/div[2]/div/div/div/div/div/div/div[2]')
        their_message = their_message_element.text
        return their_message

    def get_their_wordle_directly(self, i):
        person_element = self.driver.find_element(By.XPATH,
                                                  f'/html/body/div[1]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div[2]/div/div/div/div/div/div[{i + 1}]')
        their_message = person_element.text
        return their_message

    def scroll_to_end_of_results(self):
        while True:
            self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            sleep(.5)
            end_of_results = self.driver.find_elements(By.XPATH, f'//span[text() = "End of results"]')
            if len(end_of_results) > 0:
                return True
            no_results = self.driver.find_elements(By.XPATH, f'//span[text() = "We didn\'t find any results"]')
            if len(no_results) > 0:
                return False

    def get_friend_names(self, friend_elements):
        friend_names = []
        for i in range(len(friend_elements) - 1):
            friend_element = friend_elements[i]
            friend_name_element = friend_element.find_element(By.XPATH, f'.//h3')
            friend_name = friend_name_element.text
            friend_names.append(friend_name)
        return friend_names

    def get_friend_results(self, feed_elements, num):
        numbers = []
        friend_results = []
        hard_modes = []
        num_friends = len(feed_elements) - 1
        for i in range(num_friends):
            message_preview_element = feed_elements[i].find_element(By.XPATH, f'./div')
            text = message_preview_element.text
            pattern = f"Wordle {num} "
            pos = text.find(pattern)
            wordle_text = text[pos:]
            number, tries, hard_mode = WordleHelper.get_wordle_num_tries_hardmode(wordle_text)
            numbers.append(number)
            friend_results.append(tries)
            hard_modes.append(hard_mode)

        return numbers, friend_results, hard_modes

    def add_signature_to_clipboard(self, comment):
        comment += "\n" + "https://wordle.tiddlyhost.com"
        clipboard.copy(comment)

    def happy_birthdays(self):
        PrintHelper.printInBox()
        PrintHelper.printInBoxWithTime("FB Happy Birthday")
        self.login_birthdays()
        try:
            birthdays_today_element = self.wait_for_element(f'//span[text()="Today\'s Birthdays"]', 30)
            sleep(5)
            todays_birthdays = birthdays_today_element.find_elements(By.XPATH, f'../../..')
            if len(todays_birthdays) == 0:
                PrintHelper.printInBox("No more Birthdays Today")
                self.done()
        except Exception as e:
            PrintHelper.printInBox("No Birthdays Today")
            self.done()
        birthdays_posted_today, today = self.get_birthdays_posted_today()
        write_on_timelines = self.driver.find_elements(By.XPATH, '//div[contains(@aria-label, "Write on ")]')
        for write_on_timeline in write_on_timelines:
            name_element = write_on_timeline.find_element(By.XPATH, f'../../../../../../..')
            section_element = name_element.find_element(By.XPATH, "../../../..")
            if section_element.text.startswith("Today's Birthdays"):
                name_age_write = name_element.text.split("\n")
                name = name_age_write[0]
                nickname, message = self.get_nick_name_message(name)
                if nickname:
                    if self.birthdays_already_posted_today(birthdays_posted_today, name):
                        continue

                    message = Substitutions.substitute("hbd\n\n" + message, name, nickname)
                    self.clipboard_copy(message)
                    PrintHelper.printInBox(message)
                    write_on_timeline.send_keys(Keys.CONTROL, "v")
                    sleep(1)
                    write_on_timeline.send_keys(Keys.ENTER)
                    birthdays_posted_today[name] = [nickname, message, today]
            else:
                break
        self.close()

        self.write_birthdays_posted_today(birthdays_posted_today)

    def clipboard_copy(self, message):
        while True:
            try:
                clipboard.copy(message)
                break
            except PyperclipWindowsException as e:
                sleep(1)

    def done(self):
        self.close()
        exit(0)

    def close(self):
        self.driver.quit()
        PrintHelper.printInBox()

    @classmethod
    def get_nickname_messages(cls):
        private_filename = cls.find_private() + NICKNAMES_FILENAME
        dictionary = {}
        with open(private_filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=NICKNAMES_COLUMNS)
            next(reader)  # This skips the first row of the CSV file.

            for row in reader:
                dictionary[row["FullName"]] = [row["Nickname"], row["Message"]]

        cls.sort_nicknames_file(dictionary)

        return dictionary

    @classmethod
    def sort_nicknames_file(cls, dictionary, file_name=NICKNAMES_SORTED_FILENAME):
        names = sorted(dictionary.keys())
        file_path = cls.find_private() + file_name
        with open(file_path, 'w', newline='', encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(NICKNAMES_COLUMNS)
            for name in names:
                nickname_message = dictionary[name]
                row = [name, nickname_message[0], nickname_message[1]]
                writer.writerow(row)

    @classmethod
    def get_birthdays_posted_today(cls):
        today = datetime.date.today().strftime('%Y:%m:%d')
        resource_filename = cls.find_private() + BIRTHDAYS_POSTED_TODAY_FILENAME
        dictionary = {}
        with open(resource_filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=BIRTHDAYS_POSTED_TODAY_COLUMNS)
            next(reader)  # This skips the first row of the CSV file.

            for row in reader:
                if row["Date"] == today:
                    dictionary[row["FullName"]] = [row["Nickname"], row["Message"], row["Date"]]

        return dictionary, today

    @classmethod
    def write_birthdays_posted_today(cls, birthdays_posted_today):
        file_path = cls.find_private() + BIRTHDAYS_POSTED_TODAY_FILENAME
        with open(file_path, 'w', newline='', encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(BIRTHDAYS_POSTED_TODAY_COLUMNS)
            for name in birthdays_posted_today.keys():
                nickname_message_today = birthdays_posted_today[name]
                row = [name, nickname_message_today[0], nickname_message_today[1], nickname_message_today[2]]
                writer.writerow(row)
                PrintHelper.printInBox(f'Already posted to {name}')
        PrintHelper.printInBox()

    @classmethod
    def get_friend_names_posted_today(cls, file_path, remote_file_path):
        today = datetime.date.today().strftime('%Y:%m:%d')
        dictionary = {}
        cls.get_friend_names_posted_today_from_filepath(dictionary, file_path, today)
        cls.get_friend_names_posted_today_from_filepath(dictionary, remote_file_path, today)

        return dictionary, today

    @classmethod
    def get_friend_names_posted_today_from_filepath(cls, dictionary, file_path, today):
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=FRIENDS_POSTED_TODAY_COLUMNS)
            next(reader)  # This skips the first row of the CSV file.

            for row in reader:
                if row["Date"] == today:
                    dictionary[row["FullName"]] = [today]

    @classmethod
    def write_friend_names_posted_today(cls, friend_names_posted_today, file_path):
        with open(file_path, 'w', newline='', encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(FRIENDS_POSTED_TODAY_COLUMNS)
            for name in friend_names_posted_today.keys():
                name_today = friend_names_posted_today[name]
                row = [name, name_today[0]]
                writer.writerow(row)

    @classmethod
    def get_lines(cls, filename):
        result = []
        try:
            f = cls.open_private(filename)
        except:
            return result
        if f:
            lines = f.readlines()
            f.close()
            for line in lines:
                line = line.replace("\n", "")
                if line:
                    result.append(line)
        return result

    @classmethod
    def append_lines(cls, filename, lines):
        f = cls.open_private(filename, mode="a")
        for line in lines:
            f.write(line + "\n")
        f.close()

    @classmethod
    def replace_lines(cls, filename, lines):
        f = cls.open_private(filename, mode="w")
        for line in lines:
            f.write(line + "\n")
        f.close()

    @classmethod
    def prepend_lines(cls, filename, lines):
        previous_lines = Facebook.get_lines(filename)
        result = lines
        if len(previous_lines) > 0:
            for line in previous_lines:
                result.append(line)
        Facebook.replace_lines(filename, lines)

    @classmethod
    def get_fullname_nickname_message(cls, line):
        fullname_nickname_message = line.split(",")
        fullname = fullname_nickname_message[0].strip()
        nickname = fullname_nickname_message[1].strip()
        message = fullname_nickname_message[2].strip()
        return fullname, nickname, message

    def get_nick_name_message(self, name):
        try:
            deceased = self.deadpool[name]
            return "", ""
        except:
            try:
                nick_name_massage = self.nick_names[name]
            except:
                names = name.split(" ")
                return names[0], ""  # first_name
            if nick_name_massage == "":
                return "", ""
            return nick_name_massage[0], nick_name_massage[1]

    def get_deadpool(self):
        deadpool = {}
        lines = self.get_lines(DEADPOOL_FILENAME)
        for deceased in lines:
            if deceased:
                deadpool[deceased] = "deceased"
        return deadpool

    def test(self):
        self.nick_names = self.get_nickname_messages()
        self.deadpool = self.get_deadpool()
        name = "Dale Miller"
        nickname, message = self.get_nick_name_message(name)
        if nickname:
            message = Substitutions.substitute("hbd\n\n" + message, name, nickname)
        PrintHelper.printInBox(message)

    def wait_for_element(self, xpath, max_wait=30):
        myElem = WebDriverWait(self.driver, max_wait).until(EC.presence_of_element_located((By.XPATH, xpath)))
        sleep(2)
        return myElem

    def birthdays_already_posted_today(self, birthdays_posted_today, name):
        if birthdays_posted_today != {}:
            try:
                posted = birthdays_posted_today[name]
                PrintHelper.printInBox(f'Already posted to {name}')
                return True
            except KeyError:
                pass
        return False

    def send_message(self, to_addr, content, signature=None, attachment_file_path=None):
        if to_addr.startswith("FB:"):
            self.post_to_fb(content, to_addr, signature, attachment_file_path)
            return
        if to_addr.startswith("FBM:"):
            self.send_direct_message(content, to_addr, signature, attachment_file_path)
            return
        if to_addr.startswith("FBG:"):
            self.send_to_fb_group(content, to_addr, signature, attachment_file_path)
            return
        else:
            raise Exception("send_message to FB:, FBM: or FBG:", to_addr)

    def send_to_fb_group(self, content, to_addr, signature=None, attachment_file_path=None):
        to_addr = to_addr[4:]
        self.driver.get(GROUPS_URL + to_addr)
        post_element = self.wait_for_element('//span[text()="Write something..."]')
        sleep(2)
        self.click(post_element)
        sleep(2)
        create_a_public_post_elements = self.driver.find_elements(By.XPATH,
                                                                  '//div[@aria-label="Create a public post…"]')
        write_something_element = None
        if len(create_a_public_post_elements) > 0:
            write_something_element = create_a_public_post_elements[0]
        else:
            write_something_element = self.driver.find_element(By.XPATH, '//div[@aria-label="Write something..."]')
        sleep(2)
        self.click(write_something_element)
        self.clipboard_copy(content)
        write_something_element.send_keys(Keys.CONTROL, "v")
        sleep(5)
        post_button_element = self.driver.find_element(By.XPATH, '//span[text()="Post"]')
        if attachment_file_path:
            attach_file_element = self.driver.find_element(By.XPATH, '//div[@aria-label="Photo/video"]')
            self.click(attach_file_element)
            form_element = self.find_the_form()
            self.upload_attachment(form_element, '//span[text()="Add Photos/Videos"]/../../../../../../..//input',
                                   attachment_file_path)

        PrintHelper.printInBox(f'{to_addr}:{content} {attachment_file_path}')
        self.click(post_button_element)
        sleep(15)

    def upload_attachment(self, form_element, add_photos_videos_xpath, attachment_file_path):
        while True:
            try:
                add_photos_videos_elements = form_element.find_elements(By.XPATH, add_photos_videos_xpath)
                add_photos_videos_element = add_photos_videos_elements[0]
                add_photos_videos_element.send_keys(attachment_file_path)
                sleep(10)
                break
            except Exception as e:
                PrintHelper.printInBoxException(e)

    def find_the_form(self, title="Create post"):
        for i in range(13, 14):
            ancestor_string = "/.." * i
            form_xpath = f'//span[text()="{title}"]{ancestor_string}//form'
            create_post_forms = self.driver.find_elements(By.XPATH, form_xpath)
            if len(create_post_forms) > 0:
                return create_post_forms[0]
        return None

    def share_to_fb_group(self, from_addr, to_addr, attachment_file_path=None):
        return  # TODO
        to_addr = to_addr[5:]
        self.driver.get(GROUPS_URL + to_addr)
        post_element = self.wait_for_element('//span[text()="Write something..."]')
        sleep(2)
        self.click(post_element)
        create_a_public_post_element = self.wait_for_element('//div[@aria-label="Create a public post…"]')
        sleep(2)
        self.click(create_a_public_post_element)
        self.clipboard_copy(content)
        PrintHelper.printInBox(f'{to_addr}:{content}')
        create_a_public_post_element.send_keys(Keys.CONTROL, "v")
        sleep(5)
        post_button_element = self.driver.find_element(By.XPATH, '//span[text()="Post"]')
        if attachment_file_path:
            attach_file_element = self.driver.find_element(By.XPATH, '//div[@aria-label="Photo/video"]')
            self.click(attach_file_element)
            add_photos_videos_element = self.wait_for_element('//span[text()="Add Photos/Videos"]')
            # self.click(add_photos_videos_element)
            # TODO
        self.click(post_button_element)
        sleep(1)

    def send_direct_message(self, content, to_addr, signature=None, attachment_file_path=None):
        to_addr = to_addr[4:]
        self.driver.get(MESSAGES_URL)
        sleep(5)
        search_element = self.driver.find_element(By.XPATH, '//input[@aria-label="Search Messenger"]')
        self.clipboard_copy(to_addr)
        PrintHelper.printInBox(to_addr)
        self.click(search_element)
        search_element.send_keys(Keys.CONTROL, "v")
        sleep(5)
        found_element = search_element.find_element(By.XPATH,
                                                    "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div/div[2]/div/div/div[1]/div[1]/div/div[1]/ul/li[1]/ul/div[2]/li/div/a/div/div[2]/div/div/div/span/span/span")
        # found_element = search_element.find_element(By.XPATH, f'//img[@alt="{to_addr}"]')
        self.click(found_element)
        sleep(2)
        message_element = self.driver.find_element(By.XPATH, '//div[@aria-label="Message"]')
        self.click(message_element)
        self.add_attachment_to_message(attachment_file_path)
        self.clipboard_copy(content)
        message_element.send_keys(Keys.CONTROL, "v")
        sleep(1)
        message_element.send_keys(Keys.ENTER)
        PrintHelper.printInBox(content)
        sleep(1)

    def add_attachment_to_message(self, attachment_file_path):
        if not attachment_file_path:
            return
        try:
            add_file_attachment_element = self.driver.find_element(By.XPATH, '//input[@type="file"]')
            file_path = self.get_full_file_path(attachment_file_path)
            add_file_attachment_element.send_keys(file_path)
        except Exception as e:
            PrintHelper.printInBoxException(e)
        pass

    def send_messages(self, fb_list, content, signature, attachment_file_path=None):
        self.login(URL)
        for fb_id in fb_list:
            self.send_message(fb_id, content, signature, attachment_file_path)
            PrintHelper.printInBox()
        self.close()

    def login_experiment(self):
        self.login(URL)
        url = f"https://www.facebook.com/photo/?fbid=10223568103941762&set=a.1791772645162"
        self.driver.get(url)

    def login_friends_who_posted(self, num):
        self.login(URL)
        url = f"https://www.facebook.com/search/posts?q=wordle%20{num}&filters=eyJycF9hdXRob3I6MCI6IntcIm5hbWVcIjpcImF1dGhvcl9mcmllbmRzX2ZlZWRcIixcImFyZ3NcIjpcIlwifSJ9"
        self.driver.get(url)
        sleep(1)

    def has_friend_been_posted_today(self, friend_names_posted_today, friend_name):
        try:
            found = friend_names_posted_today[friend_name]
            return True
        except KeyError:
            return False

    def assertIsFriendName(self, friend_element, friend_name):
        friend_name_element = friend_element.find_element(By.XPATH, f'.//h3')
        text = friend_name_element.text
        assert text == friend_name, f'{text} != {friend_name}'

    def num_comments_string(self, num_comments):
        if num_comments == 0:
            return "no Comments Posted"
        elif num_comments == 1:
            return "1 Comment Posted to a friend"
        else:
            return f'{num_comments} Comments Posted to friends'

    def emoji_friend_all(self, emoji_element, friend_name):
        dy = -30
        size = emoji_element.size
        width = size["width"]
        for emoji_type in EMOJI_NAMES:
            dx = self.get_emoji_x_offset(emoji_type, width)
            a = ActionChains(self.driver)
            a.move_to_element(emoji_element).perform()
            sleep(1)
            PrintHelper.printInBox(f'{type} : {dx}')
            a.move_to_element_with_offset(emoji_element, dx, dy).perform()
            sleep(5)
        pass

    def post_to_fb(self, content, to_addr, signature=None, attachment_file_path=None):
        self.driver.get(HOME_URL)
        post = self.driver.find_element(By.XPATH, '//span[text()="What\'s on your mind, Peter?"]')
        self.click(post)
        sleep(1)

        post_form = self.driver.find_element(By.TAG_NAME, 'form')
        entry = post_form.find_element(By.XPATH,
                                       '//div[@aria-label="Connect with anyone on Facebook about what\'s on your mind..."]')
        clipboard.copy(content)
        entry.send_keys(Keys.CONTROL, 'v')

        if signature:
            text = "\r\n-- " + signature
            for key in text:
                entry.send_keys(key)
                sleep(.05)
        sleep(2)
        post_button = post_form.find_element(By.XPATH, '//span[text()="Post"]')
        self.driver.execute_script('arguments[0].scrollIntoView();', post_button)

        if attachment_file_path:
            attach_file_element = self.driver.find_element(By.XPATH, '//div[@aria-label="Photo/video"]')
            self.click(attach_file_element)
            form_element = self.find_the_form()
            self.upload_attachment(form_element, '//span[text()="Add Photos/Videos"]/../../../../../../..//input',
                                   attachment_file_path)

        self.click(post_button)
        sleep(1)

    def get_full_file_path(self, attachment_file_path):
        exists = os.path.exists(attachment_file_path)
        if exists:
            full_file_path = os.path.abspath(attachment_file_path)
            return full_file_path


if __name__ == '__main__':
    fb = Facebook()
    # fb.login_experiment()
    # offset_x = -30
    # # type = EMOJI_NAMES[0]
    # comment_element = fb.driver.find_element(By.XPATH, f'//span[text()="Comment"]/../../../..')
    # comment_element.click()
    #
    # emoji_elements = comment_element.find_elements(By.XPATH, f'preceding-sibling::*')
    # emoji_element = emoji_elements[0]
    # emoji_element.click()
    #
    # for type in EMOJI_NAMES:
    #     try:
    #         fb.emoji_friend(emoji_element, type, "Peter", offset_x)
    #     except Exception as e:
    #         PrintHelper.printInBoxException(e)
    #
    # emoji_element = emoji_elements[0]
    # emoji_element.click()
    # sleep(2)

    # text = "Wordle 850 4/6"
    # fb.post_comments_to_friends_who_posted(text)

    # fb.login()
    # fb.send_message("FBM:Peter Carmichael", "I 💘 you")

    # fb.send_message("FBM:Yona Carmichael", "I 💘 you")
    # fb.test()
    # fb.post_text_message()
    # fb.happy_birthdays()
    fb.close()
