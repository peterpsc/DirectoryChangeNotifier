import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep

import PrintHelper
import WordleHelper
from Facebook import Facebook
from WordListAnalyzer import WordListAnalyzer

DATE_LAST_SENT = "Gmail_Friends_updated.txt"
CREDENTIAL_FILENAME_PETER_PSC = "PeterPSC.txt"
GMAIL_FRIENDS = "GmailFriends.txt"


class Gmail:
    def __init__(self, credential_filename=WordleHelper.CREDENTIAL_FILENAME_WORDLEBOT_THE_RED):
        self.credential_filename = credential_filename

    @classmethod
    def find_private(cls):
        possible_paths = ['../Private', 'Private']
        for path in possible_paths:
            if os.path.exists(path):
                return path + "/"
        return ""

    @classmethod
    def open_private(cls, filename, mode="r", encoding="utf-8"):
        resource_filename = cls.find_private() + filename
        f = open(resource_filename, mode, encoding=encoding)
        return f

    def getCredentials(self):
        """ instructions for App Password can be found at https://www.getmailbird.com/gmail-app-password/"""
        f = self.open_private(self.credential_filename)
        username = f.readline().replace("\n", "")
        password = f.readline().replace("\n", "")
        signature = f.readlines()
        signature = "".join(signature)
        f.close()
        return username, password, signature

    @classmethod
    def get_list(cls, filename=GMAIL_FRIENDS):
        f = cls.open_private(filename)
        friends = f.readlines()
        f.close()
        result = []

        for friend in friends:
            friend = friend.replace("\n", "")
            if friend:
                result.append(friend)
            else:
                break
        return result

    def send_to_friends(self, wordle):
        message = wordle.get_message()

        to_email_list = self.get_list()
        remote_last_sent_file_path = WordListAnalyzer.get_remote_private_path() + DATE_LAST_SENT
        if self.not_sent_today(DATE_LAST_SENT, remote_last_sent_file_path) and to_email_list:
            lines = wordle.result_boxes.split("\n")
            subject = lines[0]
            if subject.startswith("Wordle "):
                subject = f"WordleBot the Red {subject[7:]} {WordListAnalyzer.get_day_of_week()}"

            content = '\r\n'.join(lines[2:])
            if message:
                content += "\r\n\r\n" + message

            self.send_emails_or_fb(to_email_list, subject, content)
        WordListAnalyzer.updated(DATE_LAST_SENT)
        WordListAnalyzer.updated(remote_last_sent_file_path)

    def send_emails_or_fb(self, email_or_fb_list, subject, content, cc_emails="", bcc_emails="", signature=None,
                          attachment_file_path=None):
        to_email_list, fb_list = self.split_emails_fb(email_or_fb_list)
        if fb_list != []:
            Facebook().send_messages(fb_list, subject + "\n" + content, signature, attachment_file_path)
            PrintHelper.printInBox('FB Sent')

        if to_email_list != []:
            self.send_email(to_email_list, subject, content, cc_emails=cc_emails, signature=signature,
                            bcc_emails=bcc_emails, attachment_file_path=attachment_file_path)

    def send_email(self, to_emails, subject, content, cc_emails="", signature=None, bcc_emails="",
                   attachment_file_path=None):
        from_email, password, signature_default = self.getCredentials()
        if signature == None:
            signature = signature_default
        message = MIMEMultipart()
        message['From'] = from_email
        to_email_list = self.convert_to_list(to_emails)
        cc_email_list = self.convert_to_list(cc_emails)
        bcc_email_list = self.convert_to_list(bcc_emails)
        message['To'] = ', '.join(to_email_list)
        if cc_emails:
            message['Cc'] = ', '.join(cc_email_list)
        message['Subject'] = subject
        # The body and the attachments for the mail
        content += "\r\n\r\n-- " + signature
        message.attach(MIMEText(content, 'plain'))
        if attachment_file_path:
            self.attach(message, attachment_file_path)
        # Create SMTP session for sending the mail
        session = self.waitfor_session('smtp.gmail.com', 587)  # use gmail with port
        session.starttls()  # enable security
        session.login(from_email, password)  # login with mail_id and password
        text = message.as_string()
        session.sendmail(from_email, (to_email_list + cc_email_list + bcc_email_list), text)
        session.quit()
        PrintHelper.printInBox(f'Mail Sent to {to_email_list}')
        PrintHelper.printInBox(f'  CC:{cc_email_list}')
        PrintHelper.printInBox(f'  BCC:{bcc_email_list}')
        PrintHelper.printInBox()

    def convert_to_list(self, string_or_list):
        if not string_or_list:
            return []
        if type(string_or_list) == list:
            return string_or_list
        assert type(string_or_list) == str
        text = string_or_list
        if ", " in text:
            text = text.replace(", ", ",")
        if "," in text:
            to_list = text.split(",")
        else:
            to_list = [text]

        for text in to_list:
            if "@" not in text and text[:2] != "FB":
                to_list.append(self.load_list(text))

        return to_list

    def waitfor_session(self, host, port):
        while True:
            try:
                return smtplib.SMTP(host, port)
            except:
                sleep(30)
                pass

    def attach(self, message, attachment_file_path):
        attachment = open(attachment_file_path, "rb")

        # instance of MIMEBase and named as p
        p = MIMEBase('application', 'octet-stream')

        # To change the payload into encoded form
        p.set_payload((attachment).read())

        # encode into base64
        encoders.encode_base64(p)

        p.add_header('Content-Disposition', "attachment; filename= %s" % attachment_file_path)

        # attach the instance 'p' to instance 'msg'
        message.attach(p)

    @classmethod
    def load_list(cls, list_name):
        try:
            f = cls.open_private(list_name)
            entries = f.readlines()
            f.close()
            result = []

            for entry in entries:
                entry = entry.replace("\n", "")
                if entry:
                    result.append(entry)
                else:
                    break
            return result
        except FileNotFoundError:
            PrintHelper.printInBox(f'{list_name} not found')
            return None

    def split_emails_fb(self, email_or_fb_list):
        if type(email_or_fb_list) == str:
            email_or_fb_list = email_or_fb_list.split(",")
        to_email_list = []
        fb_list = []
        for to_addr in email_or_fb_list:
            to_addr = to_addr.strip()
            if "@" not in to_addr:
                if to_addr.startswith("FB:"):
                    fb_list.append(to_addr)
                elif to_addr.startswith("FBM:"):
                    fb_list.append(to_addr)
                elif to_addr.startswith("FBG:"):
                    fb_list.append(to_addr)
                else:
                    loaded_list = self.load_list(to_addr)
                    if loaded_list:
                        for entry in loaded_list:
                            email_or_fb_list.append(entry)
            else:
                to_email_list.append(to_addr)
        return to_email_list, fb_list

    def not_sent_today(self, last_sent_filename, remote_last_sent_filepath):
        sent = WordListAnalyzer.has_updated_today(last_sent_filename, remote_last_sent_filepath)
        return not sent


if __name__ == '__main__':
    PrintHelper.printInBox()
    # Gmail().sent()
    # if Gmail().sent_today():
    #     exit(0)
    to_email_list = ["FBM:Peter Carmichael", "peter.carmichael@comcast.net"]
    cc_email_list = []
    bcc_email_list = []
    subject = "test"
    content = 'I hope it works 💘'
    content = content.replace("\\n", "\n")

    Gmail(CREDENTIAL_FILENAME_PETER_PSC).send_emails_or_fb(to_email_list, subject, content)
    # Gmail().send_email(to_email_list, subject, content, cc_email_list, bcc_email_list)
    # Gmail().send_to_friends()
    PrintHelper.printInBox()
