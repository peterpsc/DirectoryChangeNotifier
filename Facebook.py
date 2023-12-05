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

import Persistence
import PrintHelper
import Substitutions

NOT_READY = True

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
BIRTHDAYS_POSTED_TODAY_FILENAME = "BirthdaysPostedToday.csv"
BIRTHDAYS_POSTED_TODAY_COLUMNS = ["FullName", "Nickname", "Message", "Date"]


EMOJI_NAMES = ["Like", "Love", "Care", "Haha", "Wow", "Sad", "Angry"]
EMOJIS_WIDTH = 580
EMOJI_BORDER = 7
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


    def login(self, url):
        self.driver = webdriver.Firefox()
        driver = self.driver
        driver.set_page_load_timeout(120)
        driver.maximize_window()
        driver.get(url)
        # sleep(5)
        # assert 'Facebook - log in or sign up' == driver.title

        username, password = Persistence.get_credentials(CREDENTIAL_FILENAME)

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

        username, password = Persistence.get_credentials(CREDENTIAL_FILENAME)
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

    def click(self, element, timeout=10 * 60):
        while True:
            try:
                element = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(element))
                element.click()
                return element
            except Exception as e:
                PrintHelper.printInBoxException(e)
                sleep(5)

    def add_signature_to_clipboard(self, comment):
        comment += "\n" + "https://wordle.tiddlyhost.com"
        clipboard.copy(comment)

    def happy_birthdays(self):
        PrintHelper.printInBox()
        PrintHelper.printInBoxWithTime("FB Happy Birthday")
        self.login_birthdays()
        birthdays_title = "Today's birthdays"

        try:
            birthdays_today_element = self.wait_for_element(f'//span[text()="{birthdays_title}"]', 30)
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
            if section_element.text.startswith(birthdays_title):
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
        with open(private_filename, newline='', encoding=Persistence.UTF_8) as csvfile:
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
        with open(resource_filename, newline='', encoding=Persistence.UTF_8) as csvfile:
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
        lines = Persistence.get_lines(DEADPOOL_FILENAME)
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
        if signature:
            content += "\n\n" + signature
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
        sleep(2)
        search_element = self.driver.find_element(By.XPATH, '//input[@aria-label="Search Messenger"]')
        self.clipboard_copy(to_addr)
        PrintHelper.printInBox(to_addr)
        self.click(search_element)
        search_element.send_keys(Keys.CONTROL, "v")
        sleep(2)
        found_root_element = self.driver.find_element(By.XPATH, f'//li[@id="{to_addr}"]')
        found_element = found_root_element.find_element(By.XPATH, f'//span[text()="{to_addr}"]/span')
        self.click(found_element)
        sleep(2)
        message_element = self.driver.find_element(By.XPATH, '//div[@aria-label="Message"]')
        self.click(message_element)
        self.add_attachment_to_message(attachment_file_path)
        if signature:
            content += "\n\n" + signature
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
            file_path = Persistence.full_file_path(attachment_file_path)
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


    def assertIsFriendName(self, friend_element, friend_name):
        friend_name_element = friend_element.find_element(By.XPATH, f'.//h3')
        text = friend_name_element.text
        assert text == friend_name, f'{text} != {friend_name}'


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

    def get_emoji_x_offset(self, emoji_type, width):
        for i in range(len(EMOJI_NAMES)):
            if emoji_type == EMOJI_NAMES[i]:
                return EMOJI_OFFSETS[i] - width / 2 + EMOJI_BORDER

        raise Exception("Not a valid emoji_type", emoji_type)

    def get_emoji(self, emoji_type):
        for i in range(len(EMOJI_NAMES)):
            if emoji_type == EMOJI_NAMES[i]:
                return EMOJIS[i]

        raise Exception("Not a valid emoji_type", emoji_type)


if __name__ == '__main__':
    PrintHelper.printInBox()
    PrintHelper.printInBoxWithTime("Facebook.py")
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

    fb.login(MESSAGES_URL)
    fb.send_message("FBM:Peter Carmichael", "I 💘 you")

    # fb.send_message("FBM:Yona Carmichael", "I 💘 you")
    # fb.test()
    # fb.post_text_message()
    # fb.happy_birthdays()
    fb.close()
