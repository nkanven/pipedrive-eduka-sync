import os.path

from eduka_projects.services.statistics import Statistics
from eduka_projects.bootstrap import platform
from eduka_projects.utils.rialization import serialize, deserialize


class Login(Statistics):

    def __init__(self, school):
        super().__init__()
        self.school = school
        self.guardians: list = []
        self.columns_data: list = []
        self.browser = None
        self.abbr = self.parameters["enko_education"]["schools"][self.school]["abbr"]

    def get_guardians(self) -> None:

        gardians_list_urls = self.get_good_codes_from_excel(self.parameters["global"]["eduka_login_stats"])
        guardian_memo_file = "gardians" + self.abbr + ".ep"

        gardians_memo_path = os.path.join(self.autobackup_memoize, guardian_memo_file)

        if os.path.exists(gardians_memo_path):
            # self.columns_data = deserialize(self.autobackup_memoize, guardian_memo_file)

            pass
        else:

            for gl_url in gardians_list_urls:
                if self.parameters["enko_education"]["schools"][self.school]["base_url"] == gl_url[2] + "/":
                    # Browse to guardians list page
                    self.browser = platform.login(gl_url[3], self.logins(self.school))
                    platform.goto_printable(self.browser)

                    # self.columns_data = platform.get_printable(self.browser)

                    print(self.columns_data)
                    serialize(gardians_memo_path, self.columns_data)
                    break
        serialize(gardians_memo_path, self.columns_data)

    def calculate_statistics(self):
        pass

    def run(self, cmd: str) -> None:
        self.get_guardians()
