import os
from eduka_projects.bootstrap import Bootstrap
from eduka_projects.utils.rialization import deserialize, serialize
from eduka_projects.bootstrap import platform


class ServiceManager(Bootstrap):
    def __init__(self):
        print("Starting Service Manager (SM)...")
        super().__init__()

        print("SM, started")

    def get_school_parameter(self, school: str, key: str = None):
        """
        parse json parameters and simplify parameter's calls
        @param school: string The name of the school running
        @param key: string The name of the parameter called
        @return: str or dict value
        """

        if key is None:
            params = self.parameters["enko_education"]["schools"][school]
        else:
            params = self.parameters["enko_education"]["schools"][school][key]

        return params

    def logins(self, school) -> dict:
        """
        logins for Enko dashboard
        @type school: str
        """
        return {
            'email': self.parameters['enko_education']['schools'][school]['login']['email'],
            'password': self.parameters['enko_education']['schools'][school]['login']['password']
        }

    def get_guardians(self, abbr, base_url, school):

        gardians_list_urls = self.get_good_codes_from_excel(self.parameters["global"]["eduka_login_stats"])
        guardian_memo_file = "gardians" + abbr + ".ep"
        columns_data = None

        gardians_memo_path = os.path.join(self.autobackup_memoize, guardian_memo_file)

        print("file exists ?", os.path.exists(gardians_memo_path))

        if os.path.exists(gardians_memo_path):
            columns_data = deserialize(self.autobackup_memoize, guardian_memo_file)[0]
        else:

            for gl_url in gardians_list_urls:
                if base_url == gl_url[2] + "/":
                    # Browse to guardians list page
                    browser = platform.login(gl_url[3], self.logins(school))
                    platform.goto_printable(browser)

                    columns_data = platform.get_printable(browser)

                    serialize(gardians_memo_path, columns_data)
                    browser.quit()
                    break
        return columns_data
