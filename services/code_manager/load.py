import logging

import bootstrap
from services.code_manager import *
from services.code_manager.db_populate import Populate
from utils.mail import EnkoMail

code_managers = {
    'code_populate_db': Populate,
}


def run(school, switch):
    try:
        print('load populate', switch, code_managers)
        if switch in code_managers:
            enko_mail = EnkoMail(service_name, school, bootstrap.parameters)
            populate = code_managers[switch](school, enko_mail)
            print("run populate")
            populate.run()
    except Exception:
        logging.critical("Service task exit on exception", exc_info=True)
