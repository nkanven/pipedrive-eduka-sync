import os
import re
import sys
import time
from datetime import datetime

import selenium.common.exceptions

import bootstrap
from bootstrap import platform
from utils.mail import EnkoMail
from services.database_backup import *

import requests

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup


class Backup:

    def __init__(self, school):
        self.school = school
        self.param = bootstrap.parameters
        self.mailer = EnkoMail(service_name, school, self.param)

        # DB backup parameters initialization
        self.api_error = -1
        self.api_key = bootstrap.parameters['enko_education']['schools'][school]['api_key']
        self.abbr = self.param['enko_education']['schools'][school]['abbr']
        self.backup_endpoint_uri = self.param['enko_education']['db_backup_api'].replace('INSERT_API_KEY_HERE',
                                                                                         self.api_key)
        self.backup_endpoint = self.param['enko_education']['schools'][school]['base_url'] + self.backup_endpoint_uri
        self.backup_url = self.param['enko_education']['schools'][school]['base_url'] + \
                          self.param['enko_education']['database_uri']
        self.bck_max_days = self.param['enko_education']['db_backup_max_days']

        self.email = self.param['enko_education']['schools'][school]['login']['email']
        self.password = self.param['enko_education']['schools'][school]['login']['password']
        self.logins = {
            'email': self.email,
            'password': self.password
        }

    def reload_tabs(self, bws):
        """
        Reload the browser to get a new driver object with the correct node names because of weird
        naming after immediate backup through browser
        :return a driver object
        """

        db_tabs = WebDriverWait(bws, 15, ignored_exceptions=bootstrap.ignored_exceptions).until(
            EC.presence_of_element_located((By.ID, 'DBTabs')))
        return db_tabs

    def create_backup(self):

        # Create a backup through API if not already done for this task
        recent_memoize_file = datetime.now().strftime("%Y%m%d") + self.abbr + ".ep"

        # Check if today's task hadn't already backup the database
        print(self.backup_endpoint)
        if recent_memoize_file not in os.listdir(bootstrap.autobackup_memoize):
            try:
                session = bootstrap.get_session()
                with session.get(self.backup_endpoint) as r:
                    response_text = r.text
            except requests.exceptions.ConnectionError:
                bootstrap.logging.critical("ConnectionError occurred", exc_info=True)
                # No need to execute the whole program and delete backups if unable to create a recent one
                sys.exit("Program exit due to Connection Error")

            # Check if API call return any error
            self.api_error = response_text.find('ErrorBox')
            print(self.api_error)
            if self.api_error != -1:
                soup = BeautifulSoup(r.text, features="html.parser")
                self.mailer.set_subject("error ")
                self.mailer.set_email_message_text("<b>Unexpected failure occurred</b>")
                self.mailer.set_email_message_desc("API call throw: " + soup.text + "<br>IP: " + bootstrap.my_public_ip)

                # Exceptional call for private EnkoMail method __get_email_message_desc()
                bootstrap.logging.error(f"Execution error occurred {self.mailer._EnkoMail__get_email_message_desc()}")
                # mailer.send_mail()
                # sys.exit("System exit due to API unexpected failure")
            else:
                # Delete unnecessary memos
                for stored_memo_file in os.listdir(bootstrap.autobackup_memoize):
                    # Prevent from threading lock, remove old memo of this school only
                    if self.abbr in stored_memo_file:
                        os.remove(bootstrap.autobackup_memoize + os.sep + stored_memo_file)

                # Create recent memo
                with open(bootstrap.autobackup_memoize + os.sep + re.search("\d{8}", response_text).group(
                        0) + self.abbr + ".ep",
                          "w") as m:
                    pass
        else:
            bootstrap.logging.info("Database already store for today")
            print("Database already store for today")

        browser = platform.login(self.backup_url, self.logins)

        li = self.reload_tabs(browser).find_elements(By.TAG_NAME, 'li')

        # Create backup with browser
        print(self.api_error)
        if self.api_error != -1:
            li[1].click()
            backup_button = self.reload_tabs(browser).find_element(By.ID, 'StartBackup')
            backup_button.click()
            jqibuttons = WebDriverWait(browser, 30, ignored_exceptions=bootstrap.ignored_exceptions).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'jqibuttons')))
            jqibuttons.click()
            browser.quit()

    def delete_backups(self):
        # List available backups and delete old ones if any
        try:
            browser = platform.login(self.backup_url, self.logins)
            tabs = self.reload_tabs(browser)
            tabs.find_elements(By.TAG_NAME, 'li')[2].click()

            backup_list = WebDriverWait(browser, 5, ignored_exceptions=bootstrap.ignored_exceptions).until(
                EC.presence_of_element_located((By.ID, 'BackupListbody')))
            backups = backup_list.find_elements(By.TAG_NAME, 'tr')
            tr_len = len(backups)
            deleted_backups = []

            if tr_len > 1:
                while tr_len > 0:
                    # Never delete all backup
                    if len(backups) == 1:
                        break
                    bckup = backups[-1]
                    bckup_date = bckup.find_element(By.CLASS_NAME, 'column_date').get_attribute('textContent')

                    parse_date = re.search("\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}$", bckup_date)
                    bckup_parsed_date = datetime.strptime(parse_date.group(0), "%d/%m/%Y %H:%M")

                    date_diff = datetime.now() - bckup_parsed_date

                    # Check if backups are old enough to be deleted
                    if self.param['enko_education']['db_backup_max_days'] <= date_diff.days:
                        # TODO: Get backup time and name
                        bckup_filename = bckup.find_element(By.CLASS_NAME, 'column_filename').get_attribute('textContent')

                        # TODO: Delete backup
                        column_del = WebDriverWait(browser, 10, ignored_exceptions=bootstrap.ignored_exceptions).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'column_delete')))
                        column_del.click()
                        deleted_backups.append((bckup_parsed_date, bckup_filename))
                        time.sleep(10)
                    browser.refresh()
                    tabs = self.reload_tabs(browser)
                    tabs.find_elements(By.TAG_NAME, 'li')[2].click()
                    backup_list = WebDriverWait(browser, 5, ignored_exceptions=bootstrap.ignored_exceptions).until(
                        EC.presence_of_element_located((By.ID, 'BackupListbody')))
                    backups = backup_list.find_elements(By.TAG_NAME, 'tr')
                    tr_len -= 1

            # Send notification mail
            # TODO: Remove this dummy data
            # deleted_backups.append(("2023-06-28 16:18","backup-enko-mali-com-20230628-1618-ab5d.sql.ctl.eeb"))
            self.mailer.set_subject("notification ")
            message_desc = ""
            if len(deleted_backups) > 0:
                self.mailer.set_email_message_text(
                    "<b>Removal of " + str(self.bck_max_days) + " old database backup(s)</b>")
                message_desc += """
                        <p>The following backup(s) have been successfully deleted:</p>
                        <table id='enko_table'>
                            <tr>
                                <th class='enko_th'>Backup date</th>
                                <th class='enko_th'>Backup name</th>
                            </tr>
                        """
                for deleted_backup in deleted_backups:
                    message_desc += "<tr><td class='enko_td'>" + str(deleted_backup[0]) + "</td><td class='enko_td'>" \
                                    + str(deleted_backup[1]) + "</td>"
                message_desc += "</table>"
            else:
                self.mailer.set_email_message_text("No database backup eligible for removal was found on "
                                                   + self.school)

            message_desc += "<p><b>N.B:</b> A new database backup has been created already</p>"
            self.mailer.set_email_message_desc(message_desc)
            self.mailer.send_mail()
            browser.quit()
        except Exception as e:
            # Send error message and quit
            bootstrap.logging.error("Exception occured", exc_info=True)
            browser.quit()


def run(school: str, switch: str) -> None:
    """
    Run the database base backup automation on Enko dashboard
    :param school: (str) school name
    :param switch: (str) it's not needed in this function as this is a uni-tack service
    :return: (None) function does not return a value
    """
    print("Start " + school + " " + service_name)

    bck = Backup(school)
    bck.create_backup()
    bck.delete_backups()
