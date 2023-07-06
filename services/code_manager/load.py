import logging

import bootstrap
from services.code_manager import *
from services.code_manager.db_populate import Populate
from services.code_manager.corrector import Correct
from utils.mail import EnkoMail

code_managers = {
    'code_populate_db': Populate,
    'code_corrector': Correct,
}


def run(school, switch):
    try:
        print('load sub service', switch)
        if switch in code_managers:
            enko_mail = EnkoMail(service_name, school, bootstrap.parameters)
            sub_service = code_managers[switch](school, enko_mail)
            print("running ", switch)
            sub_service.run()
    except Exception:
        logging.critical("Service task exit on exception", exc_info=True)
