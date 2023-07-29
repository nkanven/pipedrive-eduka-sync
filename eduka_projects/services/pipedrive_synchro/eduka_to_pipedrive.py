import time

from eduka_projects.services.pipedrive_synchro import PipedriveService
from eduka_projects.utils.eduka_exceptions import EdukaException
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
        self.browser = None

    def get_list_from_eduka(self):
        print("Get list from")
        self.browser = platform.login(self.base_url + self.get_school_parameter(self.school, "deals_from_eduka"), self.logins(self.school))
        breadcrumb = platform.locate_element(self.browser, By.ID, 'BreadCrumb')
        # platform.locate_element(breadcrumb, By.CSS_SELECTOR, 'span > a')
        time.sleep(5)
        self.browser.get(platform.locate_element(breadcrumb, By.CSS_SELECTOR, 'span > a').get_attribute('href'))

        for line in platform.get_printable(self.browser):
            school_branch_code = line[4]
            product_code = school_branch_code + "-" + line[5][2:4]
            product_id = self.get_product_id_from_school_code(product_code)
            pipeline_id = self.get_pipeline_with_product_id(product_id, self.school)

            print(product_code, product_id, pipeline_id)

            if pipeline_id is None:
                #TODO: Handle bad or not found pipeline id
                continue

            payload = {
                "pipeline_id": pipeline_id,
                # "pipeline_id": 50,

                "user_id": self.get_school_parameter(self.school, "pipedrive_pipelines")[pipeline_id]["OwnerID"],
                self.get_pipedrive_param_name_for["student id"]: line[0],
                "title": line[1] + " " + line[2],
                "stage_id": self.get_school_parameter(self.school, "pipedrive_pipelines")[pipeline_id]["eduka_stageID"],
                # "stage_id": 984,
                self.get_pipedrive_param_name_for["student first name"]: line[1],
                self.get_pipedrive_param_name_for["student last name"]: line[2],
                self.get_pipedrive_param_name_for["gender"]: self.genders[line[3].lower()],
                self.get_pipedrive_param_name_for["parent first name"]: line[6],
                self.get_pipedrive_param_name_for["parent last name"]: line[7],
                self.get_pipedrive_param_name_for["email"]: line[8],
                self.get_pipedrive_param_name_for["phone"]: line[9]
            }
            deal_id = self.create_deal(payload)
            self.add_product_to_a_deal(deal_id, product_id)
            set_data_url = f"{self.base_url}api.php?K={self.get_school_parameter(self.school, 'api_key')}"
            set_data_url += f"&A=SETDATA&PERSON={line[0]}&PROPERTY=dealid&VALUE={deal_id}"

            print(set_data_url)

            try:
                session = self.get_session()
                with session.get(set_data_url) as r:
                    print(r.text)
            except requests.exceptions.ConnectionError as e:
                self.error_logger.critical("ConnectionError occurred", exc_info=True)
                # No need to execute the whole program and delete backups if unable to create a recent one
                raise EdukaException(self.school, e)

    def run(self, cmd: str):
        self.get_list_from_eduka()
        if self.browser is not None:
            self.browser.close()
