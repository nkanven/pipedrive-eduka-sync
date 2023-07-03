import logging
import ssl
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bootstrap import *


class EnkoMail:
    """
    EnkoMail is the mailing utility for email notification and error reporting
    """
    def __init__(self, service, school, params):
        self.__service_name: str = service
        self.__params = params
        self.__email_message_text: str = ""
        self.__email_message_desc: str = ""
        self.__subject: str = ""
        self.__school: str = params['enko_education']['schools'][school]['label']
        self.__email_cc_list: list = params['enko_education']['schools'][school]['comma_seperated_emails'].split(",")
        self.__email_to: str = params['enko_education']['schools'][school]['comma_seperated_emails'].split(",")[0]
        self.__date: str = str(datetime.now())
        self.__email_from: str = params['environment']['email']
        self.__email_password: str = params['environment']['password']

    def set_email_message_text(self, email_message_text):
        self.__email_message_text = email_message_text

    def __get_email_message_text(self):
        return self.__email_message_text

    def set_email_message_desc(self, email_message_desc):
        self.__email_message_desc = email_message_desc

    def __get_email_message_desc(self):
        return self.__email_message_desc

    def set_subject(self, subject):
        self.__subject = subject

    def __get_subject(self):
        return self.__subject

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

    def send_mail(self) -> None:
        """
        Build email components and send message
        :return: (None)
        """
        try:
            # Create a MIMEMultipart class, and set up the From, To, Subject fields

            receivers = self.__email_cc_list

            email_message = MIMEMultipart()
            email_message['From'] = self.__service_name + ' <' + self.__email_from + '>'
            email_message['To'] = self.__email_to
            email_message['Subject'] = self.__school + " - " + self.__service_name + " " + self.__get_subject()\
                + " - " + self.__date

            email_message.attach(MIMEText(self.__email_template(), "html"))

            try:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                    server.login(self.__email_from, self.__email_password)
                    server.sendmail(self.__email_from, receivers, email_message.as_string())
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
