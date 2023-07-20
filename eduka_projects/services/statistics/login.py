import os.path
import time

from eduka_projects.services.statistics import Statistics
from eduka_projects.bootstrap import platform
from eduka_projects.utils.rialization import serialize, deserialize

from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException


class Login(Statistics):

    def __init__(self, school):
        super().__init__()
        self.school = school
        self.guardians: list = []
        self.columns_data: list = []
        self.browser = None
        self.base_url = self.get_school_parameter(self.school, 'base_url')
        self.abbr = self.get_school_parameter(self.school, 'abbr')
        self.parents_has_connected = self.families_has_connected = self.total_parents = 0
        self.parents_stats = {
            "data": [],
            "errors": [],
            "p_connected": 0,
            "f_connected": 0,
            "total_parents": 0,
            "total_families": 0,
            "school": self.get_school_parameter(self.school, 'label')
        }

    def get_guardians(self):

        gardians_list_urls = self.get_good_codes_from_excel(self.parameters["global"]["eduka_login_stats"])
        guardian_memo_file = "gardians" + self.abbr + ".ep"

        gardians_memo_path = os.path.join(self.autobackup_memoize, guardian_memo_file)

        if os.path.exists(gardians_memo_path):
            self.columns_data = deserialize(self.autobackup_memoize, guardian_memo_file)[0]
        else:

            for gl_url in gardians_list_urls:
                if self.base_url == gl_url[2] + "/":
                    # Browse to guardians list page
                    self.browser = platform.login(gl_url[3], self.logins(self.school))
                    platform.goto_printable(self.browser)

                    self.columns_data = platform.get_printable(self.browser)

                    serialize(gardians_memo_path, self.columns_data)
                    self.browser.quit()
                    break
        return self

    def calculate_statistics(self):
        users_search_url = self.base_url + self.get_school_parameter(self.school, 'users_search_uri')
        self.parents_stats["total_families"] = self.columns_data.__len__()
        parents_stats_memo_fname = "parentstats" + self.abbr + ".ep"
        parents_stats_memo_path = os.path.join(self.autobackup_memoize, parents_stats_memo_fname)
        print("Total families ", self.parents_stats["total_families"])
        self.browser = platform.login(users_search_url, self.logins(self.school))

        def __user_search(refresh: bool = False):
            """
            Nested function to trigger user search page to avoid stale element not found
            @param refresh: bool to enable page refresh when set to True
            @return: webdriver object
            """
            if refresh:
                self.browser.refresh()
            return platform.locate_element(self.browser, By.ID, "txUserSearch")

        user_search = __user_search()

        if os.path.exists(parents_stats_memo_path):
            store_data = deserialize(self.autobackup_memoize, parents_stats_memo_fname)[0]
            self.parents_stats["data"] = store_data["data"]
            self.parents_stats["p_connected"] = store_data["p_connected"]
            self.parents_stats["f_connected"] = store_data["f_connected"]
            self.parents_stats["total_parents"] = store_data["total_parents"]
            self.parents_stats["errors"] = store_data["errors"]

        i = 0

        for data in self.columns_data:
            if data in self.parents_stats["data"]:
                i += 1
                continue

            i += 1
            user_search.send_keys(data[0])

            try:
                user_master_items = platform.locate_elements(self.browser, By.CLASS_NAME, "UserMasterItem", 2)
            except TimeoutException:
                try:
                    user_master_items = platform.locate_elements(self.browser, By.CLASS_NAME, "UserMasterItem", 1)
                except TimeoutException:
                    self.parents_stats["errors"].append(str(data[0]))
                    self.parents_stats["data"].append(data)
                    user_search = __user_search(True)
                    continue

            for user_master_item in user_master_items:
                self.parents_stats["total_parents"] += 1
                a_gardian_has_connect = False
                print(f"{str(i)} / {self.parents_stats['total_families']}")
                try:
                    user_master_item.click()
                except ElementClickInterceptedException:
                    print("Element click intercepted, wait 5s")
                    time.sleep(5)
                    user_master_item.click()

                last_login = platform.locate_element(self.browser, By.ID, "spDateLastActivity")

                _content = last_login.get_attribute('textContent')

                if _content == "" or _content == "-":
                    print("Empty")
                else:
                    a_gardian_has_connect = True
                    self.parents_stats["p_connected"] += 1

                if a_gardian_has_connect:
                    self.parents_stats["f_connected"] += 1

                    print(_content)

            self.parents_stats["data"].append(data)
            print(self.parents_stats)
            serialize(parents_stats_memo_path, self.parents_stats)

            user_search = __user_search(True)

    def run(self, cmd: str) -> None:
        self.get_guardians().calculate_statistics()
        mail_stats = {
            "p_connected": self.parents_stats["p_connected"],
            "f_connected": self.parents_stats["f_connected"],
            "total_parents": self.parents_stats["total_parents"],
            "total_families": self.parents_stats["total_families"],
            "school": self.parents_stats["school"],
            "errors": self.parents_stats["errors"]
        }
        self.browser.quit()
        serialize(os.path.join(self.autobackup_memoize, "mail" + cmd + self.abbr + ".ep"), mail_stats)
