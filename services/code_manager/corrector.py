import datetime
import time

from services.code_manager import *

import bootstrap
from bootstrap import *
from bootstrap import platform
from utils.mail import EnkoMail

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import mysql.connector


class Correct:
    def __init__(self, school: str, mail: EnkoMail):
        """
        The correct class browse Enko Dashboard in other to correct wrong student and family IDs
        """
        self.school = school
        self.param = bootstrap.parameters
        self.mailer = EnkoMail(service_name, school, self.param)
        self.db = db(self.param, self.mailer)

        self.logins = {
            'email': self.param['enko_education']['schools'][self.school]['login']['email'],
            'password': self.param['enko_education']['schools'][self.school]['login']['password']
        }

        self.browser: webdriver = platform.login(
            url=self.param['enko_education']['schools'][self.school]['wrong_id_list_url'],
            logins=self.logins
        )
        self.columns_data = []
        self.blank_students_code = []

    def get_wrong_ids(self):
        # Get printable link list as it content full data
        breadcrumb = WebDriverWait(self.browser, 15, ignored_exceptions=bootstrap.ignored_exceptions).until(
            EC.presence_of_element_located((By.ID, 'BreadCrumb')))
        printable_link = WebDriverWait(breadcrumb, 5, ignored_exceptions=bootstrap.ignored_exceptions).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span > a')))
        self.browser.get(printable_link.get_attribute('href'))

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
        school_caracteristics = ""
        category_map = {"male": "mst", "female": "fst", "family": "fam"}
        data_inputs = get_good_codes_from_excel(parameters["environment"]["eduka_code_manager_data_inputs"])

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

        for data in self.columns_data:
            if len(data) > 4:
                # Handle family data
                continue
            else:
                # Handle students
                print(f"Wrong code {data[0]}, gender {data[1]}, full name {data[2]}, email {data[3]}")

                if str(data[0]).strip(" ") == "":
                    # Student's code is blank
                    self.blank_students_code.append(
                        (
                            self.param['enko_education']['schools'][self.school]['base_url'],
                            data[2],
                            data[-1]
                        )
                    )
                else:
                    if data[1] == "":
                        # TODO: Report this error
                        # Skip if student gender is blank
                        continue

                    # Correct student code
                    # Select a clean code from bank_code table with the appropriate values

                    c_platform = school_caracteristics[0]
                    cluster = school_caracteristics[6].lower()
                    category = category_map[data[1].lower()]
                    __year = str(datetime.date.today().year)[2:]
                    acad_year = build_academic_year(cluster, category, __year)
                    clean_code = ""

                    print(c_platform, cluster, category, acad_year)
                    # Get the oldest student id
                    query = f"select code_id, code from bank_code where platform='{c_platform}' and cluster='{cluster}' and acad_year='{acad_year}' and category='{category}' and is_used=0 order by code_id asc"
                    cursor = self.db.cursor()
                    cursor.execute(query)
                    res = cursor.fetchone()

                    if res is not None:
                        clean_code_id = res[0]
                        clean_code = res[1]
                        # Update bank_code and replacement_logs tables
                        # To insecure consistency, query is wrapped inside a transaction
                        query = "BEGIN;"
                        query += f"INSERT INTO replacement_logs (old_code, new_code) VALUES ({data[0]}, {clean_code_id});"
                        query += f"UPDATE bank_code SET is_used=1 WHERE code={clean_code};"
                        query += "COMMIT;"
                        print(query)
                        self.db.cursor(buffered=True).execute(query)
                        self.db.commit()
                        exit("Stopped")

                    print(clean_code)

                    print(query, res)

                    exit()

                    "SELECT code FROM code_bank WHERE cluster='', platform='', acad_year LIKE%%, category=''"


    def run(self) -> None:
        try:
            self.get_wrong_ids()
            self.code_replacer()
        except Exception:
            logging.critical("ConnectionError occurred", exc_info=True)
