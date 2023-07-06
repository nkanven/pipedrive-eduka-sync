from services.code_manager import *

import bootstrap
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

    def get_wrong_ids(self):
        list_table = WebDriverWait(self.browser, 15, ignored_exceptions=bootstrap.ignored_exceptions).until(
            EC.presence_of_element_located((By.ID, 'CustomListTable0')))

        print(list_table)

        """self.browser.get(
            self.param['enko_education']['schools'][self.school]['base_url']
            + self.param['enko_education']['replacer_uri']
        )"""

    def run(self) -> None:
        self.get_wrong_ids()
