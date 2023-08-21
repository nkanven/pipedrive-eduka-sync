import logging
import os
import re
import time
from datetime import datetime

from eduka_projects.bootstrap import platform
from eduka_projects.utils.eduka_exceptions import EdukaException
from eduka_projects.utils.rialization import serialize, delete_serialized
from eduka_projects.services.database_backup import DatabaseBackup

import requests

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup


class Backup(DatabaseBackup):
    """
    Backup service class
    """
    def __init__(self, school):
        super().__init__()
        self.school = school

        # DB backup parameters initialization
        self.api_error = -1
        self.api_key = self.get_school_parameter(self.school, 'api_key')
        self.abbr = self.get_school_parameter(self.school, 'abbr')
        self.backup_endpoint_uri = self.parameters['enko_education']['db_backup_api'].replace('INSERT_API_KEY_HERE',
                                                                                              self.api_key)
        self.backup_endpoint = self.get_school_parameter(self.school, 'base_url') + self.backup_endpoint_uri
        self.backup_url = self.get_school_parameter(self.school, 'base_url') + \
                          self.parameters['enko_education']['database_uri']
        self.bck_max_days = self.parameters['enko_education']['db_backup_max_days']

        self.tabs_id = 'DBTabs'
        self.errors = []
        self.success = []
        self.notifications = {}

    def create_backup(self):
        """
        func to create backup of Eduka database. Database will be backed up through API by default. If failured, browser
        backup will initiate.
        @return: void
        """
        # Create a backup through API if not already done for this task
        recent_memoize_file = datetime.now().strftime("%Y%m%d") + self.abbr + ".ep"
        create_memo = False

        # Check if today's task hadn't already backup the database
        print(recent_memoize_file, os.listdir(self.autobackup_memoize))

        if recent_memoize_file not in os.listdir(self.autobackup_memoize):
            try:
                session = self.get_session()
                with session.get(self.backup_endpoint) as r:
                    response_text = r.text
                create_memo = True
            except requests.exceptions.ConnectionError as e:
                self.errors.append(
                    ("ConnectionError occurred on " + self.school, "Error summary " + str(e))
                )
                self.error_logger.critical("ConnectionError occurred", exc_info=True)
                # No need to execute the whole program and delete backups if unable to create a recent one
                raise EdukaException(self.school, e)

            # Check if API call return any error
            self.api_error = response_text.find('ErrorBox')

            if self.api_error != -1:
                soup = BeautifulSoup(r.text, features="html.parser")
                message_desc = "API call throw: " + soup.text + "<br>IP: " + self.my_public_ip
                self.errors.append(
                    ("<b>Unexpected failure occurred</b> " + self.school, message_desc, None)
                )
                # Exceptional call for private EnkoMail method __get_email_message_desc()
                self.error_logger.error(f"Execution error occurred {message_desc}")

                browser = platform.login(self.backup_url, self.logins(self.school))

                li = platform.get_tabs(self.tabs_id, browser).find_elements(By.TAG_NAME, 'li')

                # Create backup with browser if there was an API error
                li[1].click()
                backup_button = platform.get_tabs(self.tabs_id, browser).find_element(By.ID, 'StartBackup')
                backup_button.click()
                jqibuttons = WebDriverWait(browser, 30, ignored_exceptions=self.ignored_exceptions).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'jqibuttons')))
                jqibuttons.click()
                browser.quit()
                create_memo = True

            if create_memo:
                # Delete unnecessary memos
                delete_serialized(self.autobackup_memoize, self.abbr)

                # Create recent memo
                with open(self.autobackup_memoize + os.sep + recent_memoize_file, "w") as m:
                    pass
        else:
            self.nb = f"Database already store for today for {self.school}"
            self.error_logger.info(self.nb)
            print(self.nb)

    def delete_backups(self):
        """
        func to delete Old backups
        @return: void
        """
        # List available backups and delete old ones if any
        try:
            browser = platform.login(self.backup_url, self.logins(self.school))
            tabs = platform.get_tabs(self.tabs_id, browser)
            tabs.find_elements(By.TAG_NAME, 'li')[2].click()

            backup_list = WebDriverWait(browser, 5, ignored_exceptions=self.ignored_exceptions).until(
                EC.presence_of_element_located((By.ID, 'BackupListbody')))
            backups = backup_list.find_elements(By.TAG_NAME, 'tr')
            tr_len = len(backups)
            deleted_backups = []

            if tr_len > 1:
                while tr_len > 0:
                    # Never delete all backup
                    if len(backups) == 1:
                        break

                    backups.reverse()
                    for bckup in backups:
                        bckup_date = bckup.find_element(By.CLASS_NAME, 'column_date').get_attribute('textContent')

                        parse_date = re.search("\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}$", bckup_date)
                        bckup_parsed_date = datetime.strptime(parse_date.group(0), "%d/%m/%Y %H:%M")

                        date_diff = datetime.now() - bckup_parsed_date

                        # Check if backups are old enough to be deleted
                        if self.parameters['enko_education']['db_backup_max_days'] <= date_diff.days:
                            # TODO: Get backup time and name
                            bckup_filename = bckup.find_element(By.CLASS_NAME, 'column_filename').get_attribute(
                                'textContent')

                            print(self.abbr, " Delete ", bckup_filename, " Diff ", date_diff.days)

                            # TODO: Delete backup
                            time.sleep(5)
                            column_del = WebDriverWait(bckup, 15,
                                                       ignored_exceptions=self.ignored_exceptions).until(
                                EC.presence_of_element_located((By.CLASS_NAME, 'column_delete')))
                            column_del.click()
                            deleted_backups.append((bckup_parsed_date, bckup_filename))
                            time.sleep(10)
                            break
                    browser.refresh()
                    tabs = platform.get_tabs(self.tabs_id, browser)
                    tabs.find_elements(By.TAG_NAME, 'li')[2].click()
                    backup_list = WebDriverWait(browser, 5, ignored_exceptions=self.ignored_exceptions).until(
                        EC.presence_of_element_located((By.ID, 'BackupListbody')))
                    backups = backup_list.find_elements(By.TAG_NAME, 'tr')
                    tr_len -= 1

            # Send notification mail
            # TODO: Remove this dummy data
            # deleted_backups.append(("2023-06-28 16:18","backup-enko-mali-com-20230628-1618-ab5d.sql.ctl.eeb"))
            message_desc = ""
            message_text = "<b>No database backup eligible for removal was found on " + self.school + "</b>"
            if len(deleted_backups) > 0:
                message_text = "<b>Removal of " + str(self.bck_max_days) + " days(s) old database backup(s) on " + self.school +"</b>"

                for deleted_backup in deleted_backups:
                    message_desc += "<tr><td class='enko_td'>" + str(deleted_backup[0]) + "</td><td class='enko_td'>" \
                                    + str(deleted_backup[1]) + "</td>"

            self.nb = f"A new database backup has been created already for {self.school}" if self.nb == "" else self.nb
            self.success.append((message_text, message_desc, self.nb))

            browser.quit()
        except Exception as e:
            # Send error message and quit
            self.error_logger.error("Exception occured", exc_info=True)
            self.errors.append(
                ("ConnectionError occurred on " + self.school, "Error summary " + str(e), None)
            )

    def run(self, cmd: str) -> None:
        """
        Run the database base backup automation on Enko dashboard
        :param school: (str) school name
        :param cmd: (str) it's the running service / microservice name
        :return: (None) function does not return a value
        """
        print("Start " + self.school + " " + self.service_name)
        try:
            self.create_backup()
            self.delete_backups()
        except EdukaException as e:
            self.errors.append(("EdukaException error occured ", str(e), None))
            logging.critical("Exception occured", exc_info=True)
        except TimeoutException as e:
            self.errors.append(("Selenium Time out occured ", str(e), None))
            logging.critical("Selenium time out exception occured", exc_info=True)
            self.errors.append(
                ("Web browser error occured on " + self.school, "Error summary " + str(e), None)
            )
        finally:

            self.notifications["error"] = self.errors
            self.notifications["success"] = self.success

            file_name = self.autobackup_memoize + os.sep + "mail" + cmd + "-" + self.abbr
            if serialize(file_name, self.notifications):
                print("Succcessful serialization")
            else:
                print("Fail to serialize")
