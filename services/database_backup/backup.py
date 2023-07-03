import os
import re
import sys
import time
from datetime import datetime

import bootstrap
from bootstrap import platform
from utils.mail import EnkoMail
from services.database_backup import *

import requests

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup


def run(school: str, switch: str) -> None:
    """
    Run the database base backup automation on Enko dashboard
    :param school: (str) school name
    :param switch: (str) it's not needed in this function as this is a uni-tack service
    :return: (None) function does not return a value
    """
    print("Start " + school + " " + service_name)

    # DB backup parameters initialization
    param = bootstrap.parameters
    api_key = bootstrap.parameters['enko_education']['schools'][school]['api_key']
    backup_endpoint_uri = param['enko_education']['db_backup_api'].replace('INSERT_API_KEY_HERE', api_key)
    backup_endpoint = param['enko_education']['schools'][school]['base_url'] + backup_endpoint_uri
    backup_url = param['enko_education']['schools'][school]['base_url'] + \
                 param['enko_education']['database_uri']
    email = param['enko_education']['schools'][school]['login']['email']
    password = param['enko_education']['schools'][school]['login']['password']
    abbr = param['enko_education']['schools'][school]['abbr']
    logins = {
        'email': email,
        'password': password
    }

    mailer = EnkoMail(service_name, school, param)

    # Create a backup through API if not already done for this task
    recent_memoize_file = datetime.now().strftime("%Y%m%d") + abbr + ".ep"

    # Check if today's task hadn't already backup the database
    if recent_memoize_file not in os.listdir(bootstrap.autobackup_memoize):
        try:
            session = bootstrap.get_session()
            with session.get(backup_endpoint) as r:
                response_text = r.text
        except requests.exceptions.ConnectionError:
            bootstrap.logging.critical("ConnectionError occurred", exc_info=True)
            # No need to execute the whole program and delete backups if unable to create a recent one
            sys.exit("Program exit due to Connection Error")

        # Check if API call return any error
        if response_text.find('ErrorBox') != -1:
            soup = BeautifulSoup(r.text, features="html.parser")
            mailer.set_subject("error ")
            mailer.set_email_message_text("<b>Unexpected failure occurred</b>")
            mailer.set_email_message_desc("API call throw: " + soup.text + "<br>IP: " + bootstrap.my_public_ip)

            # Exceptional call for private EnkoMail method __get_email_message_desc()
            bootstrap.logging.error(f"Execution error occurred {mailer._EnkoMail__get_email_message_desc()}")
            mailer.send_mail()
            sys.exit("System exit due to API unexpected failure")
        else:
            # Delete unnecessary memos
            for stored_memo_file in os.listdir(bootstrap.autobackup_memoize):
                # Prevent from threading lock, remove old memo of this school only
                if abbr in stored_memo_file:
                    os.remove(bootstrap.autobackup_memoize + os.sep + stored_memo_file)

            # Create recent memo
            with open(bootstrap.autobackup_memoize + os.sep + re.search("\d{8}", response_text).group(0) + abbr + ".ep",
                      "w") as m:
                pass
    else:
        bootstrap.logging.info("Database already store for today")
        print("Database already store for today")

    # Login to ENKO and redirection to back up management page successful
    browser = platform.login(backup_url, logins)
    if browser is None:
        # stop script execution
        sys.exit()

    # List available backups and delete old ones if any
    try:
        db_tabs = WebDriverWait(browser, 15, ignored_exceptions=bootstrap.ignored_exceptions).until(
            EC.presence_of_element_located((By.ID, 'DBTabs')))
        li = db_tabs.find_elements(By.TAG_NAME, 'li')
        li[2].click()

        backup_list = WebDriverWait(browser, 5, ignored_exceptions=bootstrap.ignored_exceptions).until(
            EC.presence_of_element_located((By.ID, 'BackupListbody')))
        backups = backup_list.find_elements(By.TAG_NAME, 'tr')
        deleted_backups = []
        for bckup in backups:
            bckup_date = bckup.find_element(By.CLASS_NAME, 'column_date').get_attribute('textContent')
            parse_date = re.search("\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}$", bckup_date)
            bckup_parsed_date = datetime.strptime(parse_date.group(0), "%d/%m/%Y %H:%M")

            date_diff = datetime.now() - bckup_parsed_date

            # Check if backups are old enough to be deleted
            if param['enko_education']['db_backup_max_days'] <= date_diff.days:
                # TODO: Get backup time and name
                bckup_filename = bckup.find_element(By.CLASS_NAME, 'column_filename').get_attribute('textContent')

                # TODO: Delete backup
                bckup.find_element(By.CLASS_NAME, 'column_delete').click()
                deleted_backups.append((bckup_parsed_date, bckup_filename))
                print("Delete ", bckup_parsed_date, bckup_filename)
                time.sleep(2)

        # Send notification mail
        # TODO: Remove this dummy data
        # deleted_backups.append(("2023-06-28 16:18","backup-enko-mali-com-20230628-1618-ab5d.sql.ctl.eeb"))
        mailer.set_subject("notification ")
        message_desc = ""
        if len(deleted_backups) > 0:
            mailer.set_email_message_text("<b>Removal of old database backup(s)</b>")
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
            mailer.set_email_message_text("No database backup eligible for removal was found")

        message_desc += "<p><b>N.B:</b> A new database backup has been created already</p>"
        mailer.set_email_message_desc(message_desc)
        mailer.send_mail()
        browser.quit()
    except Exception as e:
        # Send error message and quit
        bootstrap.logging.error("Exception occured", exc_info=True)
        browser.quit()
