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

import bootstrap
import pandas as pd

service_name = "Code Manager Service"


def get_good_codes_from_excel() -> list:
    """
    This function read an Excel file from a remote url and parse the data for computation
    :return: (list) good_codes is a list of set ordered as follows (0 = male, 1 = female and 2 = family)
    """
    print('get good code from excel')
    good_codes = []
    url = bootstrap.parameters["environment"]["eduka_code_bank_url"]

    df = pd.read_excel(url, engine='openpyxl', sheet_name=None)

    start_time = time.time()
    for country in df.keys():

        if country.lower().find("do not") != -1:
            continue

        params = df[country].keys()[1:]

        max_loop = max(
            [len(df[country][params[0]]),
             len(df[country][params[1]]),
             len(df[country][params[2]])]
        )

        i = 0

        while max_loop > i:
            good_codes.append(
                (df[country][params[0]][i], df[country][params[1]][i], df[country][params[2]][i])
            )
            i += 1

    duration = time.time() - start_time
    print(f"Looping through all excel in {duration} seconds")
    return good_codes


def update_user_code():
    pass
