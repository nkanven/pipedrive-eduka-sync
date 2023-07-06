from services.code_manager import *

import bootstrap
from bootstrap import *
from bootstrap import platform
from utils.mail import EnkoMail

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Correct:
    def __init__(self, school: str, mail: EnkoMail):
        """
        The correct class browse Enko Dashboard in other to correct wrong student and family IDs
        """
        self.school = school
        self.param = bootstrap.parameters
        self.mailer = EnkoMail(service_name, school, self.param)
        self.logins = {
            'email': self.param['enko_education']['schools'][self.school]['login']['email'],
            'password': self.param['enko_education']['schools'][self.school]['login']['password']
        }

        self.browser: webdriver = platform.login(
            url=self.param['enko_education']['schools'][self.school]['wrong_id_list_url'],
            logins=self.logins
        )
        self.columns_data = []

    def get_wrong_ids(self):
        list_table = WebDriverWait(self.browser, 15, ignored_exceptions=bootstrap.ignored_exceptions).until(
            EC.presence_of_element_located((By.ID, 'CustomListTable0')))
        table_rows = list_table.find_elements(By.TAG_NAME, 'tr')

        # Loop through table ignoring thead row
        for table_row in table_rows[1:]:
            columns = table_row.find_elements(By.TAG_NAME, 'td')
            user_data = ()

            for column in columns:
                user_data += (column.get_attribute('textContent'),)

            self.columns_data.append(user_data)

        print(self.columns_data)

        self.browser.get(
            self.param['enko_education']['schools'][self.school]['base_url']
            + self.param['enko_education']['replacer_uri']
        )

    def code_replacer(self):
        self.browser.get(
            self.param['enko_education']['schools'][self.school]['base_url']
            + self.param['enko_education']['replacer_uri']
        )
        platform.get_tabs("tabs", self.browser).find_elements(By.TAG_NAME, 'li')[4].click()

    def run(self) -> None:
        try:
            self.get_wrong_ids()
            self.code_replacer()
        except Exception:
            logging.critical("ConnectionError occurred", exc_info=True)
