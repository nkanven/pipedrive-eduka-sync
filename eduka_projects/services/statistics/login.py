import os.path
import time

from eduka_projects.services.statistics import Statistics
from eduka_projects.bootstrap import platform
from eduka_projects.utils.rialization import serialize, deserialize

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException

class Login(Statistics):

    def __init__(self, school):
        super().__init__()
        self.school = school
        self.guardians: list = []
        self.columns_data: list = []
        self.browser = None
        self.base_url = self.parameters["enko_education"]["schools"][self.school]["base_url"]
        self.abbr = self.parameters["enko_education"]["schools"][self.school]["abbr"]
        self.parents_has_connected = self.families_has_connected = 0
        self.parents_stats = {"data": []}

    def get_guardians(self):

        gardians_list_urls = self.get_good_codes_from_excel(self.parameters["global"]["eduka_login_stats"])
        guardian_memo_file = "gardians" + self.abbr + ".ep"

        gardians_memo_path = os.path.join(self.autobackup_memoize, guardian_memo_file)

        if os.path.exists(gardians_memo_path):
            self.columns_data = deserialize(self.autobackup_memoize, guardian_memo_file)[0]
        else:

            for gl_url in gardians_list_urls:
                if self.parameters["enko_education"]["schools"][self.school]["base_url"] == gl_url[2] + "/":
                    # Browse to guardians list page
                    self.browser = platform.login(gl_url[3], self.logins(self.school))
                    platform.goto_printable(self.browser)

                    self.columns_data = platform.get_printable(self.browser)

                    serialize(gardians_memo_path, self.columns_data)
                    self.browser.quit()
                    break
        return self

    def calculate_statistics(self):
        users_search_url = self.base_url + self.parameters["enko_education"]["schools"][self.school]["users_search_uri"]
        total_dta = self.columns_data.__len__()
        parents_stats_memo_fname = "parentstats" + self.abbr + ".ep"
        parents_stats_memo_path = os.path.join(self.autobackup_memoize, parents_stats_memo_fname)
        print("Total families ", total_dta)
        self.browser = platform.login(users_search_url, self.logins(self.school))
        user_search = platform.locate_element(self.browser, By.ID, "txUserSearch")
        store_data = None
        if os.path.exists(parents_stats_memo_path):
            store_data = deserialize(self.autobackup_memoize, parents_stats_memo_fname)[0]
            print(store_data)
            self.parents_stats["data"] = store_data["data"]
            self.parents_has_connected = store_data["p_connected"]
            self.families_has_connected = store_data["f_connected"]
        i = 0

        for data in self.columns_data:
            if data in self.parents_stats["data"]:
                i += 1
                continue

            user_search.send_keys(data[0])

            user_master_items = platform.locate_elements(self.browser, By.CLASS_NAME, "UserMasterItem")

            for user_master_item in user_master_items:
                i += 1
                a_gardian_has_connect = False
                print(f"{str(i)} / {total_dta}")
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
                    self.parents_has_connected += 1

                if a_gardian_has_connect:
                    self.families_has_connected += 1

                    print(_content)
            self.parents_stats["p_connected"] = self.parents_has_connected
            self.parents_stats["f_connected"] = self.families_has_connected
            self.parents_stats["data"].append(data)

            serialize(parents_stats_memo_path, self.parents_stats)

            self.browser.refresh()
            user_search = platform.locate_element(self.browser, By.ID, "txUserSearch")

    def run(self, cmd: str) -> None:
        self.get_guardians().calculate_statistics()
