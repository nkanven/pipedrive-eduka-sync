"""In this file, we initialize project parameters and modules"""

import time
from eduka_projects import EdukaProjects

import pandas as pd


class Bootstrap(EdukaProjects):
    # message_text is the first part of the mail, like an intro and message_desc is the description
    message_text = message_desc = ""

    # errors is a list of tuple containing errors info in the form of (error definition, error details)
    errors: list = []

    # success is a list of tuple containing successful task notification / execution info in the form of (
    # message_text, message_desc, nb)
    success: list = []

    # nb is nota bene and it's optional
    nb: str = ""

    # notifications is a dict of errors and success list which will be serialized
    notifications: dict = {}

    def __init__(self):
        super().__init__()

    def get_good_codes_from_excel(self, url: str, code_bank: bool = False) -> list:
        """
        This function read an Excel file from a remote url and parse the data for computation
        :return: (list) good_codes is a list of set ordered as follows (0 = male, 1 = female and 2 = family)
        """
        print('get good code from excel')
        good_codes = []

        df = pd.read_excel(url, engine='openpyxl', sheet_name=None)

        start_time = time.time()
        for country in df.keys():

            if country.lower().find("do not") != -1:
                continue

            params = df[country].keys()[1:] if code_bank else df[country].keys()

            max_loop = max(
                [len(df[country][params[0]]),
                 len(df[country][params[1]]),
                 len(df[country][params[2]])]
            )

            i = 0

            while max_loop > i:
                params_tuple = ()
                for param in params:
                    params_tuple += (str(df[country][param][i]).strip(" "),)
                good_codes.append(params_tuple)
                i += 1

        duration = time.time() - start_time
        print(f"Looping through all excel in {duration} seconds")
        return good_codes

