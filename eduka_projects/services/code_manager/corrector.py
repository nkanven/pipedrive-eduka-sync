import os
import datetime
import random
import time
import webbrowser

import mysql.connector

from eduka_projects.services.code_manager import *

from eduka_projects.bootstrap import platform
from eduka_projects.utils.mail import EnkoMail
from eduka_projects.utils.rialization import serialize
from eduka_projects.utils.eduka_exceptions import EdukaNoJobExecution
from eduka_projects.services.code_manager import CodeManager
from eduka_projects.services.code_manager.db_populate import Populate

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException

from mysql.connector import errors
from dotenv import load_dotenv

load_dotenv()


class Correct(CodeManager):
    def __init__(self, school: str):
        """
        The correct class browse Enko Dashboard in other to correct wrong student and family IDs
        """
        super().__init__()
        self.browser = None
        self.school = school
        self.param = self.parameters
        self.cluster = ""
        self.mailer = EnkoMail(self.service_name, school)
        self.db_init()

        self.wrong_student_list_uri = self.param['enko_education']['schools'][self.school]['base_url'] + \
                                      self.param['enko_education']['schools'][self.school]['wrong_student_list_uri']
        self.wrong_family_list_uri = self.param['enko_education']['schools'][self.school]['base_url'] + \
                                     self.param['enko_education']['schools'][self.school]['wrong_family_list_uri']

        self.columns_data: list = []
        self.families = {}
        self.clean_datas = {}

        self.stats = {
            "nber_student_wco": 0,
            "nber_student_wco_rpl": 0,
            "nber_family_wco": 0,
            "nber_family_wco_rpl": 0,
            "nber_guardian_wco": 0,
            "nber_guardian_wco_rpl": 0
        }
        self.notifications = {
            "errors": {
                "students_blank_code": [],
                "no_gender_students": [],
                "no_clean_code_found": [],
                "families_blank_code": []
            }
        }

        self.code_blocks = {"person": None, "user": None}

        self.no_code_available = []

        # Check Database components
        try:
            Populate(self.school).pre_check()
        except Exception:
            pass

    def code_is_empty(self, data: list, c_line, group="st") -> bool:
        """
        Check if code is empty
        @param data: list of student or family data
        @param c_line: family line number
        @param group: default is st for student.
        @return: a boolean value
        """
        result = False
        strip_data = str(data[0]).strip(" ")

        if strip_data == "":
            if group == "st":
                # Student's code is blank
                self.notifications["errors"]["students_blank_code"].append(
                    (self.param['enko_education']['schools'][self.school]['base_url'], data[2], data[-1], self.cluster)
                )
            else:
                if strip_data == "":
                    self.notifications["errors"]["families_blank_code"].append(
                        (self.wrong_family_list_uri, c_line, self.cluster)
                    )
            result = True

        return result

    def get_wrong_ids(self):

        urls = [
            self.wrong_student_list_uri,
            self.wrong_family_list_uri
        ]

        for url in urls:
            if url == "":
                continue

            # Close the browser after the first id collection in other to avoid an isolated browser left running
            try:
                self.browser.quit()
            except AttributeError:
                pass

            self.browser = platform.login(
                url=url,
                logins=self.logins(self.school)
            )

            # Get printable link list as it content full data
            platform.goto_printable(self.browser)

            self.columns_data = platform.get_printable(self.browser)

        if self.columns_data.__len__() == 0:
            raise EdukaNoJobExecution(self.service_name, self.school, "No Id to correct found")

        random.shuffle(self.columns_data)

        self.browser.get(
            self.param['enko_education']['schools'][self.school]['base_url']
            + self.param['enko_education']['replacer_uri']
        )

    def db_manipulations(self, old_code, c_platform, category, acad_year):
        # Get the oldest student id
        query = f"select code_id, code from bank_code where platform='{c_platform}' and cluster='{self.cluster}' and acad_year='{acad_year}' and category='{category}' and is_used=0 order by code_id asc"

        with mysql.connector.connect(**self.db_config) as conn:
            global res
            cursor = conn.cursor(buffered=True)
            cursor.execute('use enko_db')
            cursor.execute(query)
            res = cursor.fetchone()

        if res is not None:
            clean_code_id = res[0]
            clean_code = res[1]
            clean_datas = None

            # Update bank_code and replacement_logs tables
            # To insecure consistency, query is wrapped inside a transaction

            query2 = f"INSERT INTO replacement_logs (old_code, new_code) VALUES (%s, %s);"
            query3 = f"UPDATE bank_code SET is_used=1,update_date=NOW() WHERE code=%s;"

            with mysql.connector.connect(**self.db_config) as conn:
                try:
                    conn.autocommit = False
                    cursor = conn.cursor()
                    cursor.execute('use enko_db')
                    cursor.execute(query2, (old_code, clean_code_id))
                    cursor.execute(query3, (clean_code,))

                    try:
                        clean_datas = self.families[old_code]
                    except Exception:
                        clean_datas = old_code

                    # Handle replacement here
                    self.code_replacer(clean_datas, clean_code)

                    conn.commit()

                    # print(f"{clean_code_id} for {clean_code} Update")
                except (errors.InternalError, errors.ProgrammingError, errors.IntegrityError,
                        errors.InterfaceError):
                    self.error_logger.critical("DB error occurred", exc_info=True)
                    conn.rollback()
                except Exception as e:
                    conn.rollback()
                    self.error_logger.critical("Exception occurred", exc_info=True)
                    print("Exception", str(e))
        else:
            self.notifications["errors"]["no_clean_code_found"].append(
                (c_platform, acad_year, category, self.cluster)
            )

    def code_categorizer(self):
        school_caracteristics = ""
        category_map = {"male": "mst", "female": "fst", "family": "fam"}
        data_inputs = self.get_good_codes_from_excel(self.parameters["global"]["eduka_code_manager_data_inputs"])

        for data_input in data_inputs:
            if self.param['enko_education']['schools'][self.school]['base_url'] == data_input[0] + "/":
                school_caracteristics = data_input
                break

        if school_caracteristics == "":
            # TODO: Handle this failure
            print("Couldn't find the school. Exit the program")

        self.browser.get(

            self.param['enko_education']['schools'][self.school]['base_url']
            + self.param['enko_education']['replacer_uri']

        )
        platform.get_tabs("tabs", self.browser).find_elements(By.TAG_NAME, 'li')[4].click()

        random.shuffle(self.columns_data)
        db_datas = []
        data_line_count = 0

        user_code_box = WebDriverWait(self.browser, 15, ignored_exceptions=self.ignored_exceptions).until(
            EC.presence_of_element_located((By.ID, 'UserCodeBox')))

        person_code_box = WebDriverWait(self.browser, 15, ignored_exceptions=self.ignored_exceptions).until(
            EC.presence_of_element_located((By.ID, 'PersonCodeBox')))

        self.code_blocks["person"] = person_code_box
        self.code_blocks["user"] = user_code_box

        for data in self.columns_data:
            data_line_count += 1
            if len(data) > 4:
                # Handle family data
                self.stats["nber_family_wco"] += 1
                if self.code_is_empty(data, data_line_count, "fam"):
                    continue

                guardians = []

                # Get all family data except the names
                for guardian in data[:-1]:
                    # Avoid empty list
                    if guardian != "":
                        self.stats["nber_guardian_wco"] += 1
                        guardians.append(guardian)
                self.families[data[0]] = guardians
                category = "fam"
            else:
                # Handle students
                self.stats["nber_student_wco"] += 1

                if self.code_is_empty(data, data_line_count):
                    continue

                if data[1] == "":
                    # Skip if student gender is blank
                    self.notifications["errors"]["no_gender_students"].append(
                        (self.param['enko_education']['schools'][self.school]['base_url'], data[2], data[-1],
                         self.cluster)
                    )
                    continue

                # Correct student code
                # Select a clean code from bank_code table with the appropriate values
                category = category_map[data[1].lower()]

            c_platform = school_caracteristics[0]
            self.cluster = school_caracteristics[6].lower()

            __year = str(datetime.date.today().year)[2:]
            acad_year = self.build_academic_year(self.cluster, category, __year)
            clean_code = ""

            self.db_manipulations(data[0], c_platform, category, acad_year)

    def code_replacer(self, datas, clean_id):
        # UserCodeBox
        print("replace bad code on dashboard")
        final_code = ""

        selector = 'button[data-type = "person"]'
        code_block = self.code_blocks["person"]

        if type(datas) is str:
            final_code = datas + ";" + clean_id
            self.stats["nber_student_wco_rpl"] += 1
            self.fill_code_for_replacement(final_code, code_block, selector)
        if type(datas) is list:
            i = 0
            for up_code in datas:
                if i == 0:
                    final_code = up_code + ";" + clean_id
                    self.stats["nber_family_wco_rpl"] += 1
                    self.fill_code_for_replacement(final_code, self.code_blocks["user"], 'button[data-type = "user"]')
                else:
                    final_code = up_code + ";" + clean_id + "-" + str(i)
                    self.stats["nber_guardian_wco_rpl"] += 1
                    selector = 'button[data-type = "person"]'
                    self.fill_code_for_replacement(final_code, code_block, selector)

                i += 1

        # print("Stats:", self.stats, "errors:", self.notifications["errors"])

    def fill_code_for_replacement(self, data: str, block: webbrowser, selector: str):
        block.click()
        block.send_keys(data)
        block.send_keys(Keys.ENTER)

        # 'button[data-type = "person"]'  'button[data-type = "user"]'
        _code_btn = WebDriverWait(self.browser, 15, ignored_exceptions=self.ignored_exceptions).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        time.sleep(15)
        _code_btn.click()

        self.submit_updates()

    def submit_updates(self):
        while True:
            try:
                ui_dialog_buttonset = WebDriverWait(self.browser, 15, ignored_exceptions=self.ignored_exceptions).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'ui-dialog-buttonset')))

                button = WebDriverWait(ui_dialog_buttonset, 15, ignored_exceptions=self.ignored_exceptions).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'button')))

                button.click()
                break
            except ElementNotInteractableException:
                print("Waiting for element to be interectable...")

    def run(self, cmd: str) -> None:
        # TODO: Handle mail notification for errors and statistics
        try:
            self.get_wrong_ids()
            self.code_categorizer()
            self.code_replacer()
            self.notifications["success"] = {"stats": self.stats, "cluster": self.cluster, "school": self.school}

            # Serialize notification for mailing
            f_name = "mail" + cmd + "-" + self.param['enko_education']['schools'][self.school]["abbr"]
            f_name_path = os.path.join(self.autobackup_memoize, f_name)
            print("self notif ", self.notifications)
            serialize(f_name_path, self.notifications)

        except Exception:
            self.error_logger.critical("ConnectionError occurred", exc_info=True)
        except EdukaNoJobExecution:
            self.error_logger.info("EdukaNoJobExecution occurred", exc_info=True)
