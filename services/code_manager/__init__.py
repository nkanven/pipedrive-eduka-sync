""""
# Code Manager Module

## File Usage
This file Initialize global functions and parameters for code manager service

## Service description
Code Manager Module is the code base for Eduka Code Manager service which role is to update stored
students and parents bad/wrong code from various Enko Education dashboard.
The module also handles database base population of good codes from a list of curated codes.

## Recommendation
For this module to work, ensure the appropriate external resources needed for this module to work exist and
their paths are indicated in the parameters.json.
In the parameters.json, make sure you update:
    >> environment -> eduka_code_bank_url with the url of the Excel code bank
    >> environment -> eduka_code_manager_data_inputs with the url of the Excel code bank
"""
import sys
import time

import pandas as pd

service_name = "Code Manager Service"


def get_good_codes_from_excel(url: str, code_bank: bool = False) -> list:
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


def update_user_code():
    pass
