import re
import sys
import requests
from datetime import datetime

from utils import mail
from bootstrap import *
from bootstrap import platform
from services.database_backup import *

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup


def run(school):
    print("Start " + service_name)

    # DB backup parameters initialization
    param = parameters
    api_key = parameters['enko_education']['schools'][school]['api_key']
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
    address = {
        "email_from": param['environment']['email'],
        "email_password": param['environment']['password'],
        "email_to": param['enko_education']['schools'][school]['comma_seperated_emails'].split(",")[0],
        "email_cc_list": param['enko_education']['schools'][school]['comma_seperated_emails'].split(","),
        "date": str(datetime.now()),
    }

    # Create a backup through API if not already done for this task
    recent_memoize_file = datetime.now().strftime("%Y%m%d")+abbr+".ep"

    # Check if today's task hadn't already backup the database
    if recent_memoize_file not in os.listdir(autobackup_memoize):
        try:
            session = get_session()
            with session.get(backup_endpoint) as r:
                response_text = r.text
        except requests.exceptions.ConnectionError:
            logging.critical("ConnectionError occurred", exc_info=True)
            sys.exit("Program exit due to Connection Error")

        # Check if API call return any error
        if response_text.find('ErrorBox') != -1:
            soup = BeautifulSoup(r.text, features="html.parser")
            address['subject'] = service_name + " error "
            address['email_message_text'] = "Unexpected failure occurred"
            address['email_message_desc'] = "API call throw: " + soup.text + "<br>IP: " + my_public_ip

            logging.error(f"Execution error occurred {address['email_message_desc']}")
            mail.send_mail(address, service_name)
        else:
            # Delete unnecessary memos
            for stored_memo_file in os.listdir(autobackup_memoize):
                # Prevent from threading lock, remove old memo of this school only
                if abbr in stored_memo_file:
                    os.remove(autobackup_memoize + os.sep + stored_memo_file)

            # Create recent memo
            with open(autobackup_memoize + os.sep + re.search("\d{8}", response_text).group(0)+abbr+".ep", "w") as m:
                pass
    else:
        logging.info("Database already store for today")
        print("Database already store for today")

    # Login to ENKO and redirection to back up management page successful
    browser = platform.login(backup_url, logins)
    if browser is None:
        # stop script execution
        sys.exit()

    # List available backups and delete old ones if any
    try:
        db_tabs = WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.ID, 'DBTabs')))
        li = db_tabs.find_elements(By.TAG_NAME, 'li')
        li[2].click()

        backup_list = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, 'BackupListbody')))
        backups = backup_list.find_elements(By.TAG_NAME, 'tr')
        for bckup in backups:
            bckup_date = bckup.find_element(By.CLASS_NAME, 'column_date ').get_attribute('textContent')
            parse_date = re.search("\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}$", bckup_date)
            bckup_parsed_date = datetime.strptime(parse_date.group(0), "%d/%m/%Y %H:%M")

            date_diff = datetime.now() - bckup_parsed_date

            # Check if backups are old enough to be deleted
            if param['enko_education']['db_backup_max_days'] <= date_diff.days:
                #TODO: Get backup time and name

                #TODO: Delete backup
                print("Delete backup")

                #TODO: Send notification mail

    except Exception as e:
        # Send error message and quit
        logging.error("Exception occured", exc_info=True)
        browser.quit()
