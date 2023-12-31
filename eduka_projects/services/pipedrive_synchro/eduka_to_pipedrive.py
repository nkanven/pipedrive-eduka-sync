import os
import time

from eduka_projects.services.pipedrive_synchro import PipedriveService
from eduka_projects.utils.eduka_exceptions import EdukaException
from eduka_projects.bootstrap import platform
from eduka_projects.utils.rialization import serialize

from selenium.webdriver.common.by import By

import requests


class EdukaToPipedrive(PipedriveService):
    def __init__(self, school):
        super().__init__()
        self.school = school
        self.service_name = "Eduka to Pipedrive"
        self.base_url = self.get_school_parameter(self.school, "base_url")
        self.browser = None
        self.deal_created = []
        self.notifications = {"deals": [], "wrong_deals": [], "school": self.school, "error": ""}
        self.deal_not_found = ""

    def get_list_from_eduka(self, list_url):
        """
        Get a list from Eduka
        @param list_url: list url
        @return: void
        """
        url = self.base_url + self.get_school_parameter(self.school, list_url)
        if self.browser is None:
            self.browser = platform.login(url, self.logins(self.school))
        else:
            self.browser.get(url)

        breadcrumb = platform.locate_element(self.browser, By.ID, 'BreadCrumb')
        time.sleep(5)
        self.browser.get(platform.locate_element(breadcrumb, By.CSS_SELECTOR, 'span > a', 30).get_attribute('href'))

    def create_deals_from_eduka_to_pipedrive(self):
        """
        func to Create deals from Eduka to pipedrive.
        Get the list of deal from Eduka, from the school branch code, build the product code and find if exists on
        Pipedrive. If not log error and continue
        Else create deal, add the product, update deal with student ID then log for mail
        @return: void
        """
        print("Get list from")
        self.get_list_from_eduka("deals_from_eduka")
        for line in platform.get_printable(self.browser):
            print("line ", line)
            school_branch_code = line[4]
            product_code = school_branch_code + "-" + line[5][2:4]
            product_id = self.get_product_id_from_school_code(product_code)
            pipeline_id = self.get_pipeline_with_product_id(product_id, self.school)

            print(product_code, product_id, pipeline_id)

            if product_id is None:
                _error = f"Product code <b>{product_code}</b> not found in Pipedrive "
                if school_branch_code == "":
                    _error = "Empty school branch code"
                self.notifications["wrong_deals"].append((line[0], _error))
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
            # print("payload ", payload)
            # print("wrong deals ", self.notifications["wrong_deals"])

            deal_id = self.create_deal(payload)
            print(f"Deal with ID {deal_id} created")
            self.add_product_to_a_deal(deal_id, product_id)

            self.update_deal(deal_id, {
                self.get_pipedrive_param_name_for["student id"]: line[0]
            })

            self.deal_created.append([deal_id, line[0]])

        self.notifications["deals"] = self.deal_created

    def update_deals_in_pipedrive(self):
        """
        func to Update deals in Pipedrive
        Get deals to update from a list on Eduka platform. Get deal ID and find if exists on Pipedrive. If not, log reason
        Else update product code build from school branch code, update deal student ID
        update deal on Eduka to -WON on update_deal_on_eduka call
        @return: void
        """
        self.get_list_from_eduka("deals_to_update_in_pipedrive")

        for line in platform.get_printable(self.browser):
            deal_id = line[10]
            try:
                deal = self.ask_pipedrive("deals", path=deal_id)
            except KeyError:
                self.deal_not_found += f"<p>Deal ID {deal_id} for student {line[0]} not found</p>"
                continue

            academic_year = line[5]
            school_branch_code = line[4]
            product_code = school_branch_code + "-" + academic_year[2:4]
            if deal['products_count'] == 0:
                self.add_product_to_a_deal(deal_id, product_id=self.get_product_id_from_school_code(product_code))

            # Check deal product count
            self.update_deal(deal_id, {
                self.get_pipedrive_param_name_for["student id"]: line[0],
                "status": "won"
            })
            self.update_deal_on_eduka(line[0], deal_id + "-WON")
            print("End")

        if self.deal_not_found != "":
            self.deal_not_found = f"<p>Deal ID not found for update in Pipedrive:</p> {self.deal_not_found}"

    def update_deal_on_eduka(self, user_id, value):
        """
        func to update deal on Eduka by making an API call to Eduka SETDATA endpoints
        @param user_id: student id to update
        @param value: updated deal value
        @return: void
        """
        print("Deal value to update", value)
        set_data_url = f"{self.base_url}api.php?K={self.get_school_parameter(self.school, 'api_key')}"
        set_data_url += f"&A=SETDATA&PERSON={user_id}&PROPERTY=dealid&VALUE={value}"

        try:
            session = self.get_session()
            with session.get(set_data_url) as r:
                print(r.text)
                if "Error" in r.text:
                    print(f"Unable to update deal id {value} to eduka {self.school}. Error: {r.text}")
                    raise EdukaException(self.school, r.text)
        except requests.exceptions.ConnectionError as e:
            self.error_logger.critical("ConnectionError occurred", exc_info=True)
            # No need to execute the whole program and delete backups if unable to create a recent one
            raise EdukaException(self.school, e)

    def run(self, cmd: str):
        try:
            self.create_deals_from_eduka_to_pipedrive()
            self.update_deals_in_pipedrive()
            if self.browser is not None:
                self.browser.quit()
        except (Exception, EdukaException) as e:
            self.notifications["error"] = str(e)
            print(str(e))
            self.error_logger.critical("Eduka to Pipeline exception occurred", exc_info=True)
        finally:
            f_name = "mail" + cmd + "-" + self.get_school_parameter(self.school, "abbr")
            f_name_path = os.path.join(self.autobackup_memoize, f_name)
            self.notifications["error"] = self.deal_not_found + self.notifications["error"]
            print("self notif ", self.notifications)
            serialize(f_name_path, self.notifications)
            self.delete_product_memo()
