import datetime
import random
import time

import mysql.connector

from eduka_projects.services.code_manager import *

from eduka_projects.bootstrap import platform
from eduka_projects.utils.mail import EnkoMail
from eduka_projects.utils.eduka_exceptions import EdukaNoJobExecution
from eduka_projects.services.code_manager import CodeManager
from eduka_projects.services.code_manager.db_populate import Populate

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException

from mysql.connector import errors


class Correct(CodeManager):
    def __init__(self, school: str):
        """
        The correct class browse Enko Dashboard in other to correct wrong student and family IDs
        """
        super().__init__()
        self.blank_students_code = self.columns_data = []
        self.browser = None
        self.school = school
        self.param = self.parameters
        self.mailer = EnkoMail(self.service_name, school)
        self.db_init()

        self.logins = {
            'email': self.param['enko_education']['schools'][self.school]['login']['email'],
            'password': self.param['enko_education']['schools'][self.school]['login']['password']
        }

        self.columns_data: list
        self.families = {}
        self.clean_datas = {}
        self.blank_students_code: list

        self.stats = {
            "nber_student_wco": 0,
            "nber_student_wco_rpl": 0,
            "nber_family_wco": 0,
            "nber_family_wco_rpl": 0,
            "nber_guardian_wco": 0,
            "nber_guardian_wco_rpl": 0
        }

        # Check Database components
        try:
            Populate(self.school).pre_check()
        except Exception:
            pass

    def get_wrong_ids(self):

        urls = [
            self.param['enko_education']['schools'][self.school]['base_url'] +
            self.param['enko_education']['schools'][self.school]['wrong_student_list_uri'],
            self.param['enko_education']['schools'][self.school]['base_url'] +
            self.param['enko_education']['schools'][self.school]['wrong_family_list_uri']
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
                logins=self.logins
            )

            # Get printable link list as it content full data
            breadcrumb = WebDriverWait(self.browser, 15, ignored_exceptions=self.ignored_exceptions).until(
                EC.presence_of_element_located((By.ID, 'BreadCrumb')))
            printable_link = WebDriverWait(breadcrumb, 5, ignored_exceptions=self.ignored_exceptions).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'span > a')))
            self.browser.get(printable_link.get_attribute('href'))

            list_table = WebDriverWait(self.browser, 15, ignored_exceptions=self.ignored_exceptions).until(
                EC.presence_of_element_located((By.ID, 'CustomListTable0')))
            table_rows = list_table.find_elements(By.TAG_NAME, 'tr')

            # Loop through table ignoring thead row
            for table_row in table_rows[1:]:
                columns = table_row.find_elements(By.TAG_NAME, 'td')
                user_data = ()

                for column in columns:
                    user_data += (column.get_attribute('textContent'),)

                self.columns_data.append(user_data)

        if self.columns_data.__len__() == 0:
            raise EdukaNoJobExecution(self.service_name, self.school, "No Id to correct found")

        random.shuffle(self.columns_data)

        self.browser.get(
            self.param['enko_education']['schools'][self.school]['base_url']
            + self.param['enko_education']['replacer_uri']
        )

    def db_manipulations(self, old_code, c_platform, cluster, category, acad_year):
        # Get the oldest student id
        query = f"select code_id, code from bank_code where platform='{c_platform}' and cluster='{cluster}' and acad_year='{acad_year}' and category='{category}' and is_used=0 order by code_id asc"

        with mysql.connector.connect(**self.db_config) as conn:
            global res
            cursor = conn.cursor(buffered=True)
            cursor.execute('use enko_db')
            cursor.execute(query)
            res = cursor.fetchone()

        if res is not None:
            clean_code_id = res[0]
            clean_code = res[1]

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
                    conn.commit()
                    try:
                        self.clean_datas[clean_code] = self.families[old_code]
                    except Exception as e:
                        self.error_logger.error("Error occurred", exc_info=True)
                        self.clean_datas[clean_code] = old_code

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
            self.message_text = "No result found for these queries"
            self.message_desc = ""

    def code_categorizer(self):
        school_caracteristics = ""
        category_map = {"male": "mst", "female": "fst", "family": "fam"}
        data_inputs = self.get_good_codes_from_excel(self.parameters["environment"]["eduka_code_manager_data_inputs"])

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

        for data in self.columns_data:
            if len(data) > 4:
                # Handle family data
                self.stats["nber_family_wco"] += 1
                guardians = []

                # Get all family data except the names
                for guardian in data[:-1]:
                    if guardian != "":
                        self.stats["nber_guardian_wco"] += 1
                        guardians.append(guardian)
                self.families[data[0]] = guardians
                category = "fam"
            else:
                # Handle students
                self.stats["nber_student_wco"] += 1

                if str(data[0]).strip(" ") == "":
                    # Student's code is blank
                    self.blank_students_code.append(
                        (
                            self.param['enko_education']['schools'][self.school]['base_url'],
                            data[2],
                            data[-1]
                        )
                    )
                    continue
                if data[1] == "":
                    # TODO: Report this error
                    # Skip if student gender is blank
                    continue

                # Correct student code
                # Select a clean code from bank_code table with the appropriate values
                category = category_map[data[1].lower()]
                # print(f"Wrong code {data[0]}, gender {data[1]}, full name {data[2]}, email {data[3]}")

            c_platform = school_caracteristics[0]
            cluster = school_caracteristics[6].lower()

            __year = str(datetime.date.today().year)[2:]
            acad_year = self.build_academic_year(cluster, category, __year)
            clean_code = ""

            self.db_manipulations(data[0], c_platform, cluster, category, acad_year)

    def code_replacer(self):
        # UserCodeBox
        print("replace bad code on dashboard")
        user_code = []
        person_code = []
        user_code_box = WebDriverWait(self.browser, 15, ignored_exceptions=self.ignored_exceptions).until(
            EC.presence_of_element_located((By.ID, 'UserCodeBox')))

        # PersonCodeBox
        person_code_box = WebDriverWait(self.browser, 15, ignored_exceptions=self.ignored_exceptions).until(
            EC.presence_of_element_located((By.ID, 'PersonCodeBox')))

        self.stats = {
            "nber_student_wco": 0,
            "nber_student_wco_rpl": 0,
            "nber_family_wco": 0,
            "nber_family_wco_rpl": 0,
            "nber_guardian_wco": 0,
            "nber_guardian_wco_rpl": 0
        }

        for clean_data in self.clean_datas.keys():
            if type(self.clean_datas[clean_data]) is str:
                print("Is student data")
                # person_code_box.click()
                # person_code_box.send_keys(self.clean_datas[clean_data]+";"+clean_data)
                # person_code_box.send_keys(Keys.ENTER)
                person_code.append(self.clean_datas[clean_data] + ";" + clean_data)
                self.stats["nber_student_wco_rpl"] += 1
            if type(self.clean_datas[clean_data]) is list:
                i = 0
                for up_code in self.clean_datas[clean_data]:
                    if i == 0:
                        print("is Family")
                        # user_code_box.send_keys(up_code+";"+clean_data)
                        # user_code_box.send_keys(Keys.ENTER)
                        user_code.append(up_code + ";" + clean_data)
                        self.stats["nber_family_wco_rpl"] += 1
                    else:
                        # person_code_box.click()
                        # person_code_box.send_keys(self.clean_datas[clean_data] + ";" + clean_data+"-"+str(i))
                        # person_code_box.send_keys(Keys.ENTER)
                        print("Is guardian")
                        person_code.append(up_code + ";" + clean_data + "-" + str(i))
                        self.stats["nber_guardian_wco_rpl"] += 1

                    i += 1
        print("Person ", person_code)
        person_code_box.click()
        for pc in person_code[:2]:
            person_code_box.send_keys(pc)
            person_code_box.send_keys(Keys.ENTER)

        person_code_btn = WebDriverWait(self.browser, 15, ignored_exceptions=self.ignored_exceptions).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-type = "person"]')))
        person_code_btn.click()

        self.submit_updates()

        print("Family", user_code)
        user_code_box.click()
        for uc in user_code[:2]:
            user_code_box.send_keys(uc)
            user_code_box.send_keys(Keys.ENTER)
        user_code_btn = WebDriverWait(self.browser, 15, ignored_exceptions=self.ignored_exceptions).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-type = "user"]')))
        user_code_btn.click()
        time.sleep(5)

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

    def run(self) -> None:
        try:
            self.get_wrong_ids()
            self.code_categorizer()
            self.code_replacer()
            print(self.clean_datas, self.stats)
            self.notifications["errors"] = self.errors
            self.notifications["success"] = self.success
            self.notifications["stats"] = self.stats
        except Exception:
            self.error_logger.critical("ConnectionError occurred", exc_info=True)
        except EdukaNoJobExecution:
            self.error_logger.info("EdukaNoJobExecution occurred", exc_info=True)
