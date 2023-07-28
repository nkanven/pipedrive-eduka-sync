import time

from eduka_projects.services.pipedrive_synchro import PipedriveService

from eduka_projects.bootstrap import platform

from selenium.webdriver.common.by import By

import requests
import json


class EdukaToPipedrive(PipedriveService):
    def __init__(self, school):
        super().__init__()
        self.school = school
        self.service_name = "Eduka to Pipedrive"
        self.base_url = self.get_school_parameter(self.school, "base_url")

    def get_list_from_eduka(self):
        print("Get list from")
        browser = platform.login(self.base_url + self.get_school_parameter(self.school, "eduka_to_pipedrive"), self.logins(self.school))
        breadcrumb = platform.locate_element(browser, By.ID, 'BreadCrumb')
        # platform.locate_element(breadcrumb, By.CSS_SELECTOR, 'span > a')
        time.sleep(5)
        browser.get(platform.locate_element(breadcrumb, By.CSS_SELECTOR, 'span > a').get_attribute('href'))

        for line in platform.get_printable(browser):
            school_branch_code = line[4]
            product_code = school_branch_code + "-" + line[5][2:4]
            product_id = self.get_product_id_from_school_code(product_code)
            print(product_code, product_id)
            exit()
            payload = {
                self.get_pipedrive_param_name_for["student id"]: line[0],
                "title": line[1] + " " + line[2],
                self.get_pipedrive_param_name_for["student first name"]: line[1],
                self.get_pipedrive_param_name_for["student last name"]: line[2],
                self.get_pipedrive_param_name_for["gender"]: 103 if line[3].lower() == "female" else 102,
                self.get_pipedrive_param_name_for["parent first name"]: line[6],
                self.get_pipedrive_param_name_for["parent last name"]: line[7],
                self.get_pipedrive_param_name_for["email"]: line[8],
                self.get_pipedrive_param_name_for["phone"]: line[9]
            }
            self.create_deal(payload)

    def run(self, cmd: str):
        self.get_list_from_eduka()
