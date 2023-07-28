"""In this file, we initialize project parameters and modules"""

import os
import time
from typing import Dict

from eduka_projects import EdukaProjects

import pandas as pd
from dotenv import load_dotenv
import xlsxwriter

load_dotenv()


class Bootstrap(EdukaProjects):
    pipedrive_gender: dict[str, str]
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
        self.pipedrive_gender = {
            "103": "F",
            "102": "G"
        }

    def get_good_codes_from_excel(self, url: str, code_bank: bool = False) -> list:
        """
        This function read an Excel file from a remote url and parse the data for computation
        :return: (list) good_codes is a list of set ordered as follows (0 = male, 1 = female and 2 = family)
        """
        print('get good code from excel')

        url_appen_key = url + "?api_key=" + os.environ.get("api_key")
        good_codes = []

        df = pd.read_excel(url_appen_key, engine='openpyxl', sheet_name=None)

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

    def create_xlsx(self, file_name, heads, contents):
        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(f'{file_name}.xlsx')
        worksheet = workbook.add_worksheet()
        # Add a bold format to use to highlight cells.
        bold = workbook.add_format({'bold': 1})
        # Adjust the column width.
        worksheet.set_column(1, 1, 35)
        i = 0
        row = 1
        col = 0
        for head in heads:
            letter = 65 + i
            worksheet.write(f"{chr(letter)}1", head, bold)
            i += 1

        # for family_id, student_id, student_first_name, student_last_name, gender, school_bcode, parent_id, parent_first_name, parent_last_name, email, phone, deal_id in contents:
        for content in contents:
            # worksheet.write_string(row, col, str(family_id))
            # worksheet.write_string(row, col + 1, student_id)
            # worksheet.write_string(row, col + 2, student_first_name)
            # worksheet.write_string(row, col + 3, student_last_name)
            # worksheet.write_string(row, col + 4, self.gender[str(gender)])
            # worksheet.write_string(row, col + 5, school_bcode)
            # worksheet.write_string(row, col + 6, parent_id)
            # worksheet.write_string(row, col + 7, parent_first_name)
            # worksheet.write_string(row, col + 8, parent_last_name)
            # worksheet.write_string(row, col + 9, email)
            # worksheet.write_string(row, col + 10, phone)
            # worksheet.write_string(row, col + 11, str(deal_id))

            worksheet.write_string(row, col, str(content[0]))
            j = 1
            for _c in content[1:]:
                if str(_c) == "102" or str(_c) == "103":
                    _c = self.pipedrive_gender[str(_c)]
                worksheet.write_string(row, col + j, str(_c))
                j += 1
            row += 1

        workbook.close()

