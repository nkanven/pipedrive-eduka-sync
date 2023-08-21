import os.path
import time
import re

from eduka_projects.services.statistics import Statistics
from eduka_projects.bootstrap import platform
from eduka_projects.utils.rialization import serialize, deserialize

from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException


class Login(Statistics):
    """
    Login is the core of the login statistics service.
    """
    def __init__(self, school):
        super().__init__()
        self.school = school
        self.family: set = set()
        self.gardians: set = set()
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

    def _get_guardians(self):
        """
        Private method for collecting guardians information in Eduka platform
        @return: void
        """
        user_data = []

        def get_user_datas(user_rows):
            for user_row in user_rows:
                user = user_row.get_attribute('textContent')
                if "enkoeducation" not in user:
                    user_data.append(user)

        users_search_url = self.base_url + self.get_school_parameter(self.school, 'users_search_uri')
        self.browser = platform.login(users_search_url, self.logins(self.school))
        user_tabs = platform.locate_element(self.browser, By.ID, "userTabs").find_elements(By.TAG_NAME, "li")[2]
        user_tabs.click()

        # Show all users
        show_all = platform.locate_element(self.browser, By.ID, "ShowAllUsers")
        show_all.click()

        get_user_datas(platform.locate_elements(self.browser, By.ID, "catundefinedrowundefined"))

        # Get all pages
        pages_count = platform.locate_element(self.browser, By.ID, "UserOnlineTable_paginate").find_element(By.TAG_NAME,
                                                                                                            "span").find_elements(
            By.TAG_NAME, "a")
        user_next = platform.locate_element(self.browser, By.ID, "UserOnlineTable_next")

        i = 1
        while pages_count.__len__() > i:
            # click for the next page
            user_next.click()
            get_user_datas(platform.locate_elements(self.browser, By.ID, "catundefinedrowundefined"))
            time.sleep(1)
            user_next = platform.locate_element(self.browser, By.ID, "UserOnlineTable_next")
            i += 1

        for fam in self.get_guardians(self.abbr, self.get_school_parameter(self.school, "base_url"), self.school):
            self.family.add(fam[0])
            self.gardians.add(fam[1])

        self.parents_stats["p_connected"] = self.parents_stats["f_connected"] = user_data.__len__()
        # total_users = platform.locate_element(self.browser, By.ID, "pageDescription").get_attribute('textContent')
        self.parents_stats["total_parents"] = self.gardians.__len__()
        self.parents_stats["total_families"] = self.family.__len__()

        print(self.parents_stats)

        # for user_row in user_rows:
        #     print(user_row.get_attribute('textContent'))

    def run(self, cmd: str) -> None:
        self._get_guardians()
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
