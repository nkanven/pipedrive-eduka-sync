import time

from bootstrap import parameters
import pandas as pd
service_name = "Code Manager Service"


def get_good_codes_from_excel() -> list:
    """
    This function read an excel file from a remote url and parse the data for computation
    :return: list
    """
    print('get good code from excel')
    good_codes = []
    url = parameters["environment"]["eduka_code_bank_url"]
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
            good_codes.append((df[country][params[0]][i], df[country][params[1]][i], df[country][params[2]][i]))
            i += 1

    duration = time.time() - start_time
    print(f"Looping through all excel in {duration} seconds")
    return good_codes


def update_user_code():
    pass
