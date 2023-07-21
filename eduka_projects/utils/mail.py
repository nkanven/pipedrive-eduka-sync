import os
import logging
from math import floor

import ssl
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

from eduka_projects.bootstrap import Bootstrap, service
from eduka_projects.utils.rialization import deserialize, delete_serialized
from eduka_projects.utils.eduka_exceptions import EdukaMailServiceKeyError

load_dotenv()


class EnkoMail(Bootstrap):
    """
    EnkoMail is the mailing utility for email notification and error reporting
    """

    # TODO: Create a mail collector function which will handle all mails from threads and bundle them into an
    # unique summary to send

    def __init__(self, service, school):
        super().__init__()
        self.__service_name: str = service
        self.__email_message_text: str = ""
        self.__email_message_desc: str = ""
        self.__subject: str = ""
        self.__category: str = "mail"
        self.__school: str = self.parameters['enko_education']['schools'][school]['label']
        self.__email_cc_list: list = self.parameters['enko_education']['schools'][school][
            'comma_seperated_emails'].split(",")
        self.__email_to: str = self.__email_cc_list[0]
        self.__date: str = str(datetime.now())
        self.__email_from: str = os.getenv('email')
        self.__email_password: str = os.getenv('password')

        self.datas = deserialize(self.autobackup_memoize, self.__category + self.__service_name)

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

    def set_email_cc_list(self, email: list):
        self.__email_cc_list = email

    def __email_template(self):
        style = """
            <style>
                .enko_table, .enko_th, .enko_td {
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

    def construct_message_body(self, head: str, body: str, serv_name: str, errors: str):
        try:
            success = service.get[self.__service_name]["mail_template"]["success"]
            success["head"] = head
            success["body"] = body

            success["subject"] = serv_name + success["subject"] + ""
            print(success)
            self.set_email_message_desc(
                success["body"] + "<div>" + errors + "</div>"
            )
            self.set_email_message_text(success["head"])

            self.set_subject(subject=success["subject"])
        except KeyError as e:
            self.error_logger.critical(f"{str(e)} key not found in bootstrap.service.get", exc_info=True)
        except Exception:
            print("nooooooo")
            self.error_logger.error("Exception occured", exc_info=True)

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
            email_message['Subject'] = self.__service_name + " " + self.__get_subject() \
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
                delete_serialized(self.autobackup_memoize, self.__category + self.__service_name)
        except Exception as e:
            logging.error("Exception occured", exc_info=True)

    def backup_automation(self):
        """
        Mail summarized for single message using multiple threads
        """

        if self.datas is not None:
            success_message_desc = message_foot = message_title = message_desc = ""

            errors = "<p style=color:red><hr><b>Error(s)</b><hr></p>"
            for data in self.datas:
                for error in data['error']:
                    errors += "<p>" + error[0] + " " + error[1] + "</p>"

                for succ in data['success']:
                    message_title += "<p>" + succ[0] + " for " + self.__school + "</p>"
                    message_desc += succ[1]
                    message_foot += succ[2] + "</br>"

            if self.__service_name in service.get.keys():
                body = "<table class='enko_table'><tr><th class='enko_th'>Backup date</th><th " \
                       "class='enko_th'>Backup name</th></tr>" + message_desc + "</table>"
                foot = "<p><b>N.B:</b> " + message_foot + "</p>"

                if message_desc != "":
                    success_message_desc += "<p>The following backup(s) have been successfully deleted:</p>"

                body = success_message_desc + body + foot

                self.construct_message_body(message_title, body, "Database ", errors)
                self.send_mail()
            else:
                self.error_logger.info(f"{self.__service_name} key not found in bootstrap.service.get")

    def corrector(self):
        stats = sh_stats = nh_stats = families_blank_code = no_gender_students = ""
        students_blank_code = "<table class='enko_table'><tr><th class='enko_th'>Platform</th><th " \
                              "class='enko_th'>Student name</th><th class='enko_th'>Guardian " \
                              "email</th><th class='enko_th'>Error</th></tr>"

        no_clean_code_found = "<table class='enko_table'><tr><th class='enko_th'>Platform</th><th " \
                              "class='enko_th'>Academic year</th><th class='enko_th'>Category</th><th " \
                              "class='enko_th'>Error</th></tr>"

        if self.datas is not None:
            for data in self.datas:
                if self.__service_name in service.get.keys():
                    message_title = "<p>Code manager services summary</p>"
                    if data["success"]["cluster"].lower() == "nh":
                        nh_stats += "<li>" + str(data["success"]["stats"][
                                                     "nber_student_wco_rpl"]) + " wrong student codes replaced for " + \
                                    data["success"]["school"] + "</li>"
                        nh_stats += "<li>" + str(
                            data["success"]["stats"]["nber_family_wco"]) + " wrong family codes found for " + \
                                    data["success"]["school"] + "</li>"
                        nh_stats += "<li>" + str(
                            data["success"]["stats"]["nber_family_wco_rpl"]) + " wrong family codes replaced for " + \
                                    data["success"]["school"] + "</li>"
                        nh_stats += "<li>" + str(
                            data["success"]["stats"]["nber_guardian_wco"]) + " wrong guardian codes found for " + \
                                    data["success"]["school"] + "</li>"
                        nh_stats += "<li>" + str(
                            data["success"]["stats"]["nber_guardian_wco"]) + " wrong guardian codes found for " + \
                                    data["success"]["school"] + "</li>"
                        nh_stats += "<li>" + str(data["success"]["stats"][
                                                     "nber_guardian_wco_rpl"]) + " wrong guardian codes replaced for " + \
                                    data["success"]["school"] + "</li>"

                    if data["success"]["cluster"].lower() == "sh":
                        sh_stats += "<li>" + str(data["success"]["stats"][
                                                     "nber_student_wco_rpl"]) + " wrong student codes replaced for " + \
                                    data["success"]["school"] + "</li>"
                        sh_stats += "<li>" + str(
                            data["success"]["stats"]["nber_family_wco"]) + " wrong family codes found for " + \
                                    data["success"]["school"] + "</li>"
                        sh_stats += "<li>" + str(
                            data["success"]["stats"]["nber_family_wco_rpl"]) + " wrong family codes replaced for " + \
                                    data["success"]["school"] + "</li>"
                        sh_stats += "<li>" + str(
                            data["success"]["stats"]["nber_guardian_wco"]) + " wrong guardian codes found for " + \
                                    data["success"]["school"] + "</li>"
                        sh_stats += "<li>" + str(
                            data["success"]["stats"]["nber_guardian_wco"]) + " wrong guardian codes found for " + \
                                    data["success"]["school"] + "</li>"
                        sh_stats += "<li>" + str(data["success"]["stats"][
                                                     "nber_guardian_wco_rpl"]) + " wrong guardian codes replaced for " + \
                                    data["success"]["school"] + "</li>"

                    stats += "<p>Code manager statistics for NH: </p>"
                    stats += "<ul>" + nh_stats + "</ul>"
                    stats += "<p>Code manager statistics for SH: </p>"
                    stats += "<ul>" + sh_stats + "</ul>"

                    for std_bc in data["errors"]["students_blank_code"]:
                        students_blank_code += f"<tr><td>{std_bc[0]}</td><td>{std_bc[1]}</td><td>{std_bc[2]}</td><td>Student blank code</td></tr>"

                    for ng_std in data["errors"]["no_gender_students"]:
                        no_gender_students += f"<tr><td>{ng_std[0]}</td><td>{ng_std[1]}</td><td>{ng_std[2]}</td><td>No gender student</td></tr>"

                    students_blank_code += no_gender_students + "</table>"

                    for nccf in data["errors"]["no_clean_code_found"]:
                        no_clean_code_found += f"<tr><td>{nccf[0]}</td><td>{nccf[1]}</td><td>{nccf[2]}</td><td>No code found</td></tr>"
                    no_clean_code_found += "</table>"

                    for fbc in data["errors"]["families_blank_code"]:
                        families_blank_code += "<p>Family blank code found at " + fbc[0] + " line " + fbc[1] + "</p>"

                    errors = students_blank_code + "<hr>" + no_clean_code_found + "<hr>" + families_blank_code

                    self.construct_message_body(message_title, stats, "Code Manager ", errors)
                    self.send_mail()
                else:
                    self.error_logger.info(f"{self.__service_name} key not found in bootstrap.service.get")

    def login_stats(self):
        if self.datas is not None:
            message_title = "<p>Statistics login service summary</p>"
            body = ""
            errors = ""
            for data in self.datas:
                print("Yo ", data)
                f_connected_ratio = floor((data['f_connected'] * 100) / data['total_families'])
                p_connected_ratio = floor((data['p_connected'] * 100) / data['total_parents'])
                body += f"<div><p>Login statistics for {data['school']}.</p><ul><li>Number of families: {data['total_families']}</li>"
                body += f"<li>Number of parents/guardians: {data['total_parents']}</li><li>Number of unique parents login: {data['p_connected']}</li>"
                body += f"<li>Number of unique families login: {data['f_connected']}</li></ul>"
                body += f"<p>{str(f_connected_ratio)}% of families and {str(p_connected_ratio)}% of parents have logged in since platform launch</p></div>"
                errors += "<li>" + ", ".join(data['errors']) + "</li>"

            if errors != "":
                errors = "<p>No available information found for families with the following IDs: </p><ul>" + errors + "</ul>"

            self.construct_message_body(message_title, body, "Statistics ", errors)
            self.send_mail()

    def db_populate(self):
        pass

    def pipedrive_to_eduka(self):
        pass

    def mail_builder_selector(self):
        # Add service mail builder methods here
        m_select = {
            "backup_automation": self.backup_automation,
            "corrector": self.corrector,
            "login": self.login_stats,
            "db_populate": self.db_populate,
            "pipedrive_to_eduka": self.pipedrive_to_eduka
        }

        try:
            m_select[self.__service_name]()
        except KeyError as e:
            raise EdukaMailServiceKeyError(self.__service_name, self.__school, str(e))
