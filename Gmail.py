import datetime
import shutil
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep

import DataFrame
import Persistence
import PrintHelper
from Facebook import Facebook
from Substitutions import Substitutions

DEFAULT_SIGNATURE = 'default'

DATE_LAST_SENT = "Wordle_Contacts_updated.txt"
CREDENTIALS_NOTIFIER = "CredentialsNotifier.txt"


class Gmail:
    def __init__(self, credential_filename=CREDENTIALS_NOTIFIER):
        self.credential_filename = credential_filename
        self.substitutions = Substitutions()

    def getCredentials(self):
        """ instructions for App Password can be found at https://www.getmailbird.com/gmail-app-password/"""
        file_path = Persistence.remote_private_file_path(self.credential_filename)
        list = Persistence.readlines(file_path)
        username = list[0]
        password = list[1]
        return username, password

    def send_to_friends(self, wordle, friends_list):
        to_email_file_path = Persistence.private_file_path("me.txt")
        to_email_list = Persistence.readlines(to_email_file_path)
        bcc_email_file_path = Persistence.private_file_path(friends_list)
        bcc_email_list = Persistence.readlines(bcc_email_file_path)
        last_sent_file_path = Persistence.private_file_path(DATE_LAST_SENT)
        remote_last_sent_file_path = Persistence.remote_private_file_path(DATE_LAST_SENT)

        has_updated_today = Persistence.has_updated_today(last_sent_file_path, remote_last_sent_file_path)
        if not has_updated_today and bcc_email_list:
            # Prevent the automation from sending twice
            Persistence.updated_today(last_sent_file_path)
            shutil.copyfile(last_sent_file_path, remote_last_sent_file_path)

            message = wordle.get_message()
            lines = wordle.result_boxes.split("\n")
            subject = lines[0]
            if subject.startswith("Wordle "):
                subject = f"WordleBot the Red {subject[7:]} {self.get_day_of_week()}"

            content = '\r\n'.join(lines[2:])
            if message:
                content += "\r\n\r\n" + message

            self.send_emails_or_fb(to_email_list, subject, content, bcc_emails=bcc_email_list, fb_signature="wbtr",
                                   signature="wbtru")

    @staticmethod
    def get_day_of_week():
        return datetime.date.today().strftime('%A')

    def send_emails_or_fb(self, email_or_fb_list, subject, content, cc_emails="", bcc_emails="", fb_signature=None,
                          signature=None, attachment_file_path=None):
        if subject:
            to_email_list, fb_list = self.split_emails_fb(email_or_fb_list)
            if fb_list != []:
                Facebook().send_messages(fb_list, subject + "\n" + content, fb_signature, attachment_file_path)
                PrintHelper.printInBox('FB Sent')

            if to_email_list != []:
                self.send_email(to_email_list, subject, content, cc_emails=cc_emails, signature=signature,
                                bcc_emails=bcc_emails, attachment_file_path=attachment_file_path)

    def send_email(self, to_emails, subject, content, cc_emails="", signature=None, bcc_emails="",
                   attachment_file_path=None):
        from_email, password = Persistence.get_credentials(self.credential_filename)
        signature = self.substitutions.get_signature(signature)
        message = MIMEMultipart()
        message['From'] = from_email
        to_email_list, fb_list = self.split_emails_fb(to_emails)
        cc_email_list, fb_list = self.split_emails_fb(cc_emails)
        bcc_email_list, fb_list = self.split_emails_fb(bcc_emails)
        message['To'] = ', '.join(to_email_list)
        if cc_emails:
            message['Cc'] = ', '.join(cc_email_list)
        if bcc_emails:
            message['Bcc'] = ', '.join(bcc_email_list)

        message['Subject'] = subject
        # The body and the attachments for the mail
        if signature:
            content += "\n\n" + signature
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
        PrintHelper.printInBox()
        PrintHelper.printInBox(f'Mail Sent to {to_email_list}')
        PrintHelper.printInBox(f'  CC:{cc_email_list}')
        PrintHelper.printInBox(f'  BCC:{bcc_email_list}')
        PrintHelper.printInBox(f'  Subject:{subject} ')
        PrintHelper.printInBox(f'  {content}')

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
                to_list.append(Persistence.get_lines(text))

        return to_list

    @staticmethod
    def waitfor_session(host, port):
        while True:
            try:
                return smtplib.SMTP(host, port)
            except:
                sleep(30)
                pass

    @staticmethod
    def attach(message, attachment_file_path):
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

    @staticmethod
    def split_emails_fb(email_or_fb_list):
        if type(email_or_fb_list) == str:
            email_or_fb_list = email_or_fb_list.split(",")
        to_email_list = []
        fb_list = []
        for to_addr in email_or_fb_list:
            to_addr = to_addr.strip()
            if to_addr:
                if "@" not in to_addr:
                    if to_addr.startswith("FB:"):
                        fb_list.append(to_addr)
                    elif to_addr.startswith("FBM:"):
                        fb_list.append(to_addr)
                    elif to_addr.startswith("FBG:"):
                        fb_list.append(to_addr)
                    else:
                        to_addr_file_path = Persistence.private_file_path(to_addr)
                        loaded_list = Persistence.readlines(to_addr_file_path)
                        if loaded_list:
                            for entry in loaded_list:
                                email_or_fb_list.append(entry)
                else:
                    to_email_list.append(to_addr)
        return to_email_list, fb_list


if __name__ == '__main__':
    PrintHelper.printInBox()
    # to_email_list = ["peter.carmichael@comcast.net"]
    to_email_list = ["FBM:Peter Carmichael", "peter.carmichael@comcast.net"]
    cc_email_list = []
    bcc_email_list = []
    subject = "test"
    content = 'I hope it works 💘'
    content = content.replace("\\n", "\n")

    gmail = Gmail()

    for key in ["", "not found", "default", "pc", None]:
        signature = Substitutions.get_signature(key)
        DataFrame.print_result(key, signature)

    PrintHelper.printInBox()
    gmail.send_emails_or_fb(to_email_list, subject, content, fb_signature="fbtest", signature="test")
    # Gmail(CREDENTIAL_NOTIFIER).send_email(to_email_list, subject, content, cc_email_list, bcc_email_list)
    # Gmail(CREDENTIAL_NOTIFIER).send_to_friends()

    PrintHelper.printInBox()
