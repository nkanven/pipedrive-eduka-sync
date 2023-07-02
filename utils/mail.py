import logging
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bootstrap import *


class EnkoMail:
    def __init__(self, service, school):
        self.service_name: str = service
        self.school: str = school
        self.email_message_text: str = ""
        self.email_message_desc: str = ""
        self.email_cc_list: list = []
        self.email_from: str = ""
        self.email_to: str = ""
        self.date: str = ""
        self.subject: str = ""
        self.email_password: str = ""

    def set_email_message_text(self, email_message_text):
        self.email_message_text = email_message_text

    def __get_email_message_text(self):
        return self.email_message_text

    def set_email_message_desc(self, email_message_desc):
        self.email_message_desc = email_message_desc

    def __get_email_message_desc(self):
        return self.email_message_desc

    def set_email_cc_list(self, email_cc_list):
        self.email_cc_list = email_cc_list

    def __get_email_cc_list(self):
        return self.email_cc_list

    def set_email_from(self, email_from):
        self.email_from = email_from

    def __get_email_from(self):
        return self.email_from

    def set_email_to(self, email_to):
        self.email_to = email_to

    def __get_email_to(self):
        return self.email_to

    def set_date(self, date):
        self.date = date

    def __get_date(self):
        return self.date

    def set_subject(self, subject):
        self.subject = subject

    def __get_subject(self):
        return self.subject

    def set_email_password(self, email_password):
        self.email_password = email_password

    def __get_email_password(self):
        return self.email_password

    def __email_template(self):
        style = """
            <style>
                #enko_table, .enko_th, .enko_td {
                    border: 1px solid black;
                    border-collapse: collapse;
                    padding: 10px;
                }
                .enko_th{
                    background-color: #edf5ea;
                    font-weight: bold;
                }
            </style>
        """
        html = """
        <html>
            <head>
                {style}
            </head>
            <body>
                <div>{message_text} <br> {message_desc} </div>
            </body>
        </html>
        """
        return html.format(
            style=style,
            message_text=self.__get_email_message_text(),
            message_desc=self.__get_email_message_desc()
        )

    def send_mail(self):
        try:
            # Create a MIMEMultipart class, and set up the From, To, Subject fields

            receivers = self.__get_email_cc_list()

            email_message = MIMEMultipart()
            email_message['From'] = self.service_name + ' <' + self.__get_email_from() + '>'
            email_message['To'] = self.__get_email_to()
            email_message['Subject'] = self.school + " - " + self.service_name + " " + self.__get_subject()\
                + " - " + self.__get_date()

            email_message.attach(MIMEText(self.__email_template(), "html"))

            try:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                    server.login(self.__get_email_from(), self.__get_email_password())
                    server.sendmail(self.__get_email_from(), receivers, email_message.as_string())
            except smtplib.SMTPAuthenticationError as e:
                error_msg = """
                    In a nutshell, google is not allowing you to log in via smtplib because it has flagged this sort of login as "less secure", so what you have to do is go to this link while you're logged in to your google account, and allow the access:
                    https://www.google.com/settings/security/lesssecureapps
                    Once that is set (see my screenshot below), it should work.
                """
                logging.critical("SMTPAuthenticationError occured " + error_msg, exc_info=True)
                print("SMTP Error occured: " + str(e) + " " + error_msg)
            except Exception as e:
                logging.error("Exception occured", exc_info=True)
            else:
                print("Mail sent successfully")
        except Exception as e:
            logging.error("Exception occured", exc_info=True)
