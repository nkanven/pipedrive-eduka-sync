import os
import datetime
import random
import time
import webbrowser

import mysql.connector

from eduka_projects.services.code_manager import *

from eduka_projects.bootstrap import platform
from eduka_projects.utils.mail import EnkoMail
from eduka_projects.utils.rialization import serialize, deserialize
from eduka_projects.utils.eduka_exceptions import EdukaNoJobExecution, EdukaException
from eduka_projects.services.code_manager import CodeManager
from eduka_projects.services.code_manager.db_populate import Populate

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException, ElementClickInterceptedException

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
        self.mailer = EnkoMail(self.service_name, school)
        self.db_init()
        self.abbr = self.get_school_parameter(self.school, "abbr")
        self.base_url = self.get_school_parameter(self.school, 'base_url')
        self.wrong_student_list_uri = self.base_url + self.get_school_parameter(self.school, 'wrong_student_list_uri')
        self.wrong_family_list_uri = self.base_url + self.get_school_parameter(self.school, 'wrong_family_list_uri')
        self.id_fname = "idreplaced" + self.abbr + ".ep"
        self.id_fname_path = os.path.join(self.autobackup_memoize, self.id_fname)
        self.lock = os.path.join(self.autobackup_memoize, self.get_school_parameter(self.school, "country_code") + ".lock")

        # For exceptional countries
        self.same_country_codes = {
            "enko_waca": "https://enko-dakar-senegal.com",
            "enko_dakar": "https://enko-dakar-senegal.com",
        }
        self.columns_data: list = []
        self._old_code: list = []
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

        data_inputs = self.get_good_codes_from_excel(self.parameters["global"]["eduka_code_manager_data_inputs"])
        self.school_caracteristics = []
        for data_input in data_inputs:
            if self.base_url == data_input[0] + "/":
                self.school_caracteristics = data_input
                break
        self.cluster = self.school_caracteristics[6].lower()

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
                    (self.base_url, data[2], data[-2], self.cluster)
                )
            else:
                if strip_data == "":
                    self.notifications["errors"]["families_blank_code"].append(
                        (self.wrong_family_list_uri, c_line, self.cluster)
                    )
            result = True

        return result

    def get_wrong_ids(self):
        """
        Get all the wrong IDs to correct
        @return: void
        """
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

            print("Getting ", url)
            self.browser = platform.login(
                url=url,
                logins=self.logins(self.school)
            )

            # Get printable link list as it content full data
            print("Go to printable")
            platform.goto_printable(self.browser)

            print("Getting printable")
            self.columns_data += platform.get_printable(self.browser)

        print("Launching ", self.base_url + self.param['enko_education']['replacer_uri'])
        self.browser.get(
            self.base_url
            + self.param['enko_education']['replacer_uri']
        )

        if self.columns_data.__len__() == 0:
            raise EdukaNoJobExecution(self.service_name, self.school, "No Id to correct found")

        print(self.columns_data, self.columns_data.__len__())

    def db_manipulations(self, old_code, c_platform, category, acad_year):
        """
        func to get good code and match with corresponding bad code for update in Eduka platform. This func calls
        the code_replacer func.
        @param old_code: bad code to replace
        @param c_platform: school url
        @param category: user cateory (family, male or female)
        @param acad_year: academic year
        @return: void
        """
        # Get the oldest student id
        print("DB Manipulations......")
        try:
            c_platform = self.same_country_codes[self.school]
        except KeyError:
            pass

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

                    # Handle replacement here. Make sure all went well before storing
                    if self.code_replacer(clean_datas, clean_code):
                        conn.commit()
                    else:
                        conn.rollback()
                        exit("Stop execution")

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

        corrector_memoize = {
            "code": self._old_code,
            "stats": self.stats,
            "notif": self.notifications
        }
        serialize(self.id_fname_path, corrector_memoize)

    def code_categorizer(self):
        """
        func to categorize each code for it to be associated with the corresponding good code. A lock is placed to no
        allow a school access to the same code more than once on runtime. This func calls the db_manipulations func
        @return: void
        """
        category_map = {"male": "mst", "garçon": "mst", "female": "fst", "fille": "fst", "family": "fam"}

        if self.school_caracteristics.__len__() == 0:
            print("Couldn't find the school. Exit the program")
            raise EdukaException(self.school, "Couldn't find the school. Exit the program")

        self.browser.get(

            self.base_url
            + self.param['enko_education']['replacer_uri']

        )
        platform.get_tabs("tabs", self.browser).find_elements(By.TAG_NAME, 'li')[4].click()

        data_line_count = 0

        user_code_box = WebDriverWait(self.browser, 15, ignored_exceptions=self.ignored_exceptions).until(
            EC.presence_of_element_located((By.ID, 'UserCodeBox')))

        person_code_box = WebDriverWait(self.browser, 15, ignored_exceptions=self.ignored_exceptions).until(
            EC.presence_of_element_located((By.ID, 'PersonCodeBox')))

        self.code_blocks["person"] = person_code_box
        self.code_blocks["user"] = user_code_box

        if os.path.exists(self.id_fname_path):
            deserial = deserialize(self.autobackup_memoize, self.id_fname)[0]
            print(deserial)
            self._old_code = [] if deserial["code"] is None else deserial["code"]
            self.stats["nber_family_wco"] = deserial["stats"]["nber_family_wco"]
            self.stats["nber_guardian_wco"] = deserial["stats"]["nber_guardian_wco"]
            self.stats["nber_student_wco"] = deserial["stats"]["nber_student_wco"]
            self.stats["nber_student_wco_rpl"] = deserial["stats"]["nber_student_wco_rpl"]
            self.stats["nber_family_wco_rpl"] = deserial["stats"]["nber_family_wco_rpl"]
            self.stats["nber_guardian_wco_rpl"] = deserial["stats"]["nber_guardian_wco_rpl"]
            try:
                self.notifications = deserial["notif"]
            except KeyError:
                pass

        for data in self.columns_data:
            print(f"Correct {data}...")
            if data.__len__() == 0:
                continue

            data_line_count += 1
            if data[-1] == "fam":
                # Handle family data
                if self.code_is_empty(data, data_line_count, "fam"):
                    continue

                guardians = []

                # Get all family data except the names
                for guardian in data[:-2]:
                    # Avoid empty list
                    if guardian != "":
                        self.stats["nber_guardian_wco"] += 1
                        guardians.append(guardian)
                self.families[data[0]] = guardians
                category = "fam"
            else:
                # Handle students
                if data[1].lower() not in category_map:
                    # Skip if student gender is blank
                    print("gender", data[1].lower())
                    self.notifications["errors"]["no_gender_students"].append(
                        (self.base_url, data[2], data[-3],
                         self.cluster)
                    )
                    continue

                category = category_map[data[1].lower()]
                self.stats["nber_student_wco"] += 1

                if self.code_is_empty(data, data_line_count):
                    continue

            c_platform = self.school_caracteristics[0]

            __year = str(datetime.date.today().year)[2:]
            acad_year = self.build_academic_year(self.cluster, category, __year)
            clean_code = ""

            # Avoid same code to be selected form DB where school has same country code
            # If a file with country code as name exists, same school of the country should wait before fetching a code

            while True:
                if not os.path.exists(self.lock):
                    with open(self.lock, "w") as f:
                        f.write(self.school)
                    self.db_manipulations(data[0], c_platform, category, acad_year)
                    os.remove(self.lock)
                    time.sleep(1)
                    break

    def code_replacer(self, datas, clean_id) -> bool:
        """
        func to replace bad code with good one on Eduka platform. This func calls fill_code_for_replacement func
        @param datas: student data is a string and family data is a list
        @param clean_id: good id
        @return: bool if update went well True is return else False
        """
        result = False
        print("replace bad code on dashboard")
        try:
            selector = 'button[data-type = "personlist"]'
            code_block = self.code_blocks["person"]

            if type(datas) is str and not self.code_is_stored(datas, self._old_code):
                final_code = datas + ";" + clean_id
                self.stats["nber_student_wco_rpl"] += 1
                if self.fill_code_for_replacement(final_code, code_block, selector):
                    self._old_code.append(datas)
            if type(datas) is list:
                i = 0
                is_filled = False
                for up_code in datas:
                    if not self.code_is_stored(up_code, self._old_code):
                        if i == 0:
                            final_code = up_code + ";" + clean_id
                            self.stats["nber_family_wco_rpl"] += 1
                            if self.fill_code_for_replacement(final_code, self.code_blocks["user"],
                                                              'button[data-type = "user"]'):
                                is_filled = True
                        else:
                            is_filled = False
                            final_code = up_code + ";" + clean_id + "-" + str(i)
                            self.stats["nber_guardian_wco_rpl"] += 1
                            selector = 'button[data-type = "person"]'
                            if self.fill_code_for_replacement(final_code, code_block, selector):
                                is_filled = True

                        if is_filled:
                            self._old_code.append(up_code)

                    i += 1
            result = True
            # print("Stats:", self.stats, "errors:", self.notifications["errors"])
        except Exception:
            self.error_logger.critical("ConnectionError occurred", exc_info=True)
        finally:
            return result

    def code_is_stored(self, code, o_codes) -> bool:
        """
        func to check if code is already stored on runtime. It's a second security layer to prevent multiple usage o same code.
        @param code: good code
        @param o_codes: old code
        @return: bool True is code found and False if not
        """
        # Skip if code has been already replaced
        result = False
        if code in o_codes:
            print(f"{code} has already been corrected")
            result = True

        return result

    def fill_code_for_replacement(self, data: str, block: webbrowser, selector: str) -> bool:
        """
        func to browse Eduka code update page. This func place the code and bad code in the proper box on Eduka
        for the update. The func calls submit_updates for submission.
        @param data: user data for update
        @param block: browser instance
        @param selector: update box selector
        @return: bool will response True if no incident or False.
        """
        result = False
        try:
            block.clear()

            while True:
                try:
                    block.click()
                    break
                except ElementClickInterceptedException:
                    print("Click intercepted! Retrying")
                    time.sleep(1)

            block.send_keys(data)
            block.send_keys(Keys.ENTER)

            # 'button[data-type = "person"]'  'button[data-type = "user"]'
            _code_btn = WebDriverWait(self.browser, 15, ignored_exceptions=self.ignored_exceptions).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            time.sleep(5)
            _code_btn.click()

            self.submit_updates()
            result = True
            print("Submit successful. Code corrected: ", data, " ", self.school)
        except Exception:
            self.error_logger.critical("ConnectionError occurred", exc_info=True)
        finally:
            return result

    def submit_updates(self):
        """
        func to submit bad code / good codes for update
        @return: void
        """
        time.sleep(5)
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
            os.remove(self.lock)
        except FileNotFoundError:
            pass

        try:
            print("In run func")
            self.get_wrong_ids()
            self.code_categorizer()
            self.notifications["success"] = {"stats": self.stats, "cluster": self.cluster, "school": self.school}

            # Serialize notification for mailing
            f_name = "mail" + cmd + "-" + self.abbr
            f_name_path = os.path.join(self.autobackup_memoize, f_name)
            print("self notif ", self.notifications)
            serialize(f_name_path, self.notifications)

        except Exception:
            self.error_logger.critical("ConnectionError occurred", exc_info=True)
        except EdukaNoJobExecution:
            self.error_logger.info("EdukaNoJobExecution occurred", exc_info=True)
        finally:
            self.browser.quit()
