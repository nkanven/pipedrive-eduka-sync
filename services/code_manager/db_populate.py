import sys

from bootstrap import *
from services.code_manager import *
from utils.mail import EnkoMail

from mysql import connector
from mysql.connector.errors import ProgrammingError, PoolError, OperationalError, NotSupportedError


class Populate:

    def __init__(self, school: str, mail: EnkoMail):
        self.school = school
        self.mail = mail
        print("Start populate service")

        try:
            self.db = connector.connect(
                host=parameters['environment']['db_host'],
                user=parameters['environment']['db_user'],
                passwd=parameters['environment']['db_password'])
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
            # Send mail to admin

            sys.exit('Service task exit on KeyError exception')

    def pre_check(self):
        # Verify if service databases exists
        cursor = self.db.cursor()
        try:
            cursor.execute('CREATE DATABASE IF NOT EXISTS einvestor')
            logging.info("Database successfully created")
        except Exception:
            self.db.rollback()
            logging.critical("Service task exit on KeyError exception", exc_info=True)
            sys.exit('Service task exit on database creation error')

        for x in cursor:
            print(x[0])

    def upload_data(self):
        print(get_good_codes_from_excel())

    def run(self) -> None:
        """
        This function runs the Populate object
        :return: None
        """
        try:
            self.pre_check()
            print("done precheck")
            self.upload_data()
        except Exception:
            logging.critical("Service task exit on KeyError exception", exc_info=True)
