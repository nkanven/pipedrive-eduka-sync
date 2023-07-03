import sys
import time

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
            self.db.cursor().execute('CREATE DATABASE IF NOT EXISTS enko_db')
            self.db.cursor().execute('use enko_db')
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

    def pre_check(self):
        # Verify if service databases exists

        try:
            self.db.cursor().execute("CREATE TABLE IF NOT EXISTS `bank_code` (`code_id` int NOT NULL,`code` varchar("
                                     "25) COLLATE utf8mb4_general_ci NOT NULL,`cluster` varchar(2) COLLATE "
                                     "utf8mb4_general_ci NOT NULL,`platform` varchar(100) COLLATE utf8mb4_general_ci "
                                     "NOT NULL,`acad_year` varchar(9) COLLATE utf8mb4_general_ci NOT NULL,`category` "
                                     "varchar(3) COLLATE utf8mb4_general_ci NOT NULL,`is_used` tinyint(1) NOT NULL "
                                     "DEFAULT 0,`update_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                                     "`d_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB DEFAULT "
                                     "CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;")

            try:
                self.db.cursor().execute("ALTER TABLE `bank_code` ADD PRIMARY KEY (`code_id`), ADD UNIQUE KEY `code` ("
                                         "`code`);")
                self.db.cursor().execute("ALTER TABLE `bank_code` MODIFY `code_id` int NOT NULL AUTO_INCREMENT;")
            except ProgrammingError:
                # No need to alter table when primary keys has already been added
                pass

            logging.info("Database successfully created")
        except Exception:
            self.db.rollback()
            logging.critical("Service task exit on exception", exc_info=True)
            self.db.cursor().close()
            sys.exit('Service task exit on database creation error')

        """for x in cursor:
            print(x[0])"""

    def upload_data_in_code_bank(self):
        cursor = self.db.cursor()
        data_inputs = get_good_codes_from_excel(parameters["environment"]["eduka_code_manager_data_inputs"])
        code_bank = get_good_codes_from_excel(parameters["environment"]["eduka_code_bank_url"], True)
        category_map = {"1": "MST", "2": "FST", "3": "FAM"}


        def insert_codes(i_codes: tuple, i_data: tuple) -> bool:
            """
            In function nested code for code understanding and readability. This function handle the cleaning
            of parameters for code_bank table insertion
            :param i_codes: a tuple of student code full id
            :param i_data: a tuple containing school data inputs for categorization
            :return: a boolean which indicates the successfulness of the insertion
            """
            result = False
            try:
                for i_code in i_codes:
                    code_split = i_code.split("-")
                    category = None
                    country_code = code_split[0]

                    if country_code.lower() == i_data[2].lower():

                        try:
                            category = category_map[code_split[2]].lower()
                        except KeyError:
                            logging.info("Skipped KeyError. Non studend Id")
                            pass

                        platform = i_data[0]
                        cluster = i_data[6]
                        try:
                            __year = code_split[3][0:2]
                        except IndexError:
                            logging.info("Skipped IndexError. Non studend Id")
                            __year = code_split[2][0:2]

                        if cluster.lower() == "nh" and category in ("mst", "fst"):
                            acad_year = "20" + __year + "/20" + str(int(__year) + 1)
                        else:  # (cluster.lower() == "sh" and category in ("mst", "fst")) or category == "fam")
                            acad_year = "20" + __year

                        #print(i_code, category, platform, acad_year, cluster)
                    result = True
            except Exception:
                logging.critical("Service task inser_code exit on exception", exc_info=True)
            finally:
                return result

        for data_input in data_inputs:
            for codes in code_bank:
                insert_codes(codes, data_input)

        # cursor.execute("")

    def run(self) -> None:
        """
        This function runs the Populate object
        :return: None
        """
        try:
            self.pre_check()
            print("done precheck")
            start_time = time.time()
            self.upload_data_in_code_bank()
            duration = time.time() - start_time
            print(f"Store in {duration} seconds")

        except Exception:
            logging.critical("Service task exit on exception", exc_info=True)
