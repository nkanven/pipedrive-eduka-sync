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

from bootstrap import *
from utils.mail import EnkoMail
import sys
import time

from mysql import connector
from mysql.connector.errors import ProgrammingError, PoolError, OperationalError, NotSupportedError
import pandas as pd

service_name = "Code Manager Service"

db_config = {
    'user': parameters['environment']['db_user'],
    'password': parameters['environment']['db_password'],
    'host': parameters['environment']['db_host'],
}


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


def build_academic_year(cluster: str, category: str, __year: str) -> str:
    if cluster == "nh" and category in ("mst", "fst"):
        acad_year = "20" + __year + "/20" + str(int(__year) + 1)
    else:  # (cluster.lower() == "sh" and category in ("mst", "fst")) or category == "fam")
        acad_year = "20" + __year
    return acad_year


def db_init(mail):
    try:
        with connector.connect(**db_config) as dbase:
            dbase.cursor().execute('CREATE DATABASE IF NOT EXISTS enko_db')
            dbase.cursor().execute('use enko_db')
    except (ProgrammingError, PoolError, OperationalError, NotSupportedError) as e:
        logging.critical("Database connection error occurred", exc_info=True)
        mail.set_email_message_text("Database connection error")
        desc = "<p>Service is not able to connect to project database. <br><br>"
        desc += "<b>Trace: {trace}</b> <br><br>Please contact the system administrator for more details.</p>"
        mail.set_email_message_desc(desc.format(trace=str(e)))
        mail.send_mail()
        sys.exit('Service task exit on database connection error')
    except KeyError as e:
        logging.critical("Service task exit on KeyError exception", exc_info=True)
        mail.set_email_message_text("Parameters.json KeyError exception")
        desc = "<p>Service is unable to find appropriate key in the given Json file.. <br><br>"
        desc += "<b>Trace: {trace}</b> <br><br>Please contact the system administrator for more details.</p>"
        mail.set_email_message_desc(desc.format(trace=str(e)))
        mail.send_mail()
        sys.exit('Service task exit on KeyError exception')
    except Exception as e:
        logging.critical("Service task init exit on exception", exc_info=True)
        mail.set_email_message_text("DB Populate init exception")
        desc = "<p>Service encounters an exception while initializing enko_db database.. <br><br>"
        desc += "<b>Trace: {trace}</b> <br><br>Please contact the system administrator for more details.</p>"
        mail.set_email_message_desc(desc.format(trace=str(e)))
        mail.send_mail()
        sys.exit('Service task init exit on exception')


def update_user_code():
    pass
