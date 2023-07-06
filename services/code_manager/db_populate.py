import time

import mysql.connector
import concurrent.futures

from bootstrap import *
from services.code_manager import *
from utils.mail import EnkoMail

from mysql import connector
from mysql.connector.errors import ProgrammingError, PoolError, OperationalError, NotSupportedError


class Populate:

    def __init__(self, school: str, mail: EnkoMail):
        """
        Populate database with student IDs information
        :param school: (str) enko school name
        :param mail: (EnkoMail) Mail object to handle notifcations
        """
        self.school = school
        self.mail = mail
        self.sql: list = []
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
        """
        Verify if service databases exists. If not create required database and tables
        """

        try:
            self.db.cursor().execute("CREATE TABLE IF NOT EXISTS `bank_code` (`code_id` int NOT NULL,`code` varchar("
                                     "25) COLLATE utf8mb4_general_ci NOT NULL,`cluster` varchar(2) COLLATE "
                                     "utf8mb4_general_ci NOT NULL,`platform` varchar(100) COLLATE utf8mb4_general_ci "
                                     "NOT NULL,`acad_year` varchar(9) COLLATE utf8mb4_general_ci NOT NULL,`category` "
                                     "varchar(3) COLLATE utf8mb4_general_ci NOT NULL,`is_used` tinyint(1) NOT NULL "
                                     "DEFAULT 0,`update_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                                     "`d_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB DEFAULT "
                                     "CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;")

            self.db.cursor().execute("CREATE TABLE IF NOT EXISTS `replacement_logs`(`log_id` int(11) NOT NULL, "
                                     "`old_code` varchar(255) NOT NULL, `new_code` int(11) NOT NULL, "
                                     "`d_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP) ENGINE = InnoDB DEFAULT "
                                     "CHARSET = utf8mb4;")
            try:
                self.db.cursor().execute("ALTER TABLE `bank_code` ADD PRIMARY KEY (`code_id`), ADD UNIQUE KEY `code` ("
                                         "`code`);")
                self.db.cursor().execute("ALTER TABLE `bank_code` MODIFY `code_id` int NOT NULL AUTO_INCREMENT;")
                self.db.cursor().execute("ALTER TABLE `replacement_logs` ADD PRIMARY KEY (`log_id`), ADD KEY "
                                         "`new_code` (`new_code`);")
                self.db.cursor().execute("ALTER TABLE `replacement_logs` MODIFY `log_id` int(11) NOT NULL "
                                         "AUTO_INCREMENT;")
                self.db.cursor().execute("ALTER TABLE `replacement_logs` ADD CONSTRAINT `replacement_logs_ibfk_1` "
                                         "FOREIGN KEY (`new_code`) REFERENCES `bank_code` (`code_id`);")
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

    def prep_codes_insertion(self, i_codes: tuple, i_data: tuple) -> bool:
        """
        his function handle the cleaning
        of parameters for code_bank table insertion
        :param i_codes: a tuple of student code full id
        :param i_data: a tuple containing school data inputs for categorization
        :return: a boolean which indicates the successfulness of the insertion
        """
        result = False

        category_map = {"1": "MST", "2": "FST", "3": "FAM"}
        try:
            for i_code in i_codes:
                code_split = i_code.split("-")
                category = None
                country_code = code_split[0]

                if country_code.lower() == i_data[2].lower():
                    platform = i_data[0]
                    cluster = i_data[6].lower()
                    try:
                        category = category_map[code_split[2]].lower()
                        __year = code_split[3][0:2]
                    except KeyError:
                        if len(code_split) == 3:
                            category = category_map["3"].lower()
                        logging.info("Skipped KeyError. Non studend Id")
                    except IndexError:
                        logging.info("Skipped IndexError. Non studend Id")
                        __year = code_split[2][0:2]

                    if cluster == "nh" and category in ("mst", "fst"):
                        acad_year = "20" + __year + "/20" + str(int(__year) + 1)
                    else:  # (cluster.lower() == "sh" and category in ("mst", "fst")) or category == "fam")
                        acad_year = "20" + __year

                    values = (i_code, category, platform, acad_year, cluster)
                    self.sql.append(values)

                result = True
        except Exception:
            logging.critical("Service task inser_code exit on exception", exc_info=True)
        finally:
            return result

    def upload_data_in_code_bank(self) -> None:
        """
        Dispatch data for insertion in bank_code table.
        Return None
        """
        data_inputs = get_good_codes_from_excel(parameters["environment"]["eduka_code_manager_data_inputs"])
        code_bank = get_good_codes_from_excel(parameters["environment"]["eduka_code_bank_url"], True)

        for data_input in data_inputs:
            for codes in code_bank:
                self.prep_codes_insertion(codes, data_input)

        query = "INSERT INTO bank_code (code, category, platform, acad_year, cluster) " \
                "VALUES (%s, %s, %s, %s, %s);"

        self.db.cursor().executemany(query, self.sql)
        self.db.commit()

    def run(self) -> None:
        """
        This function runs the Populate object. Handles student IDs insertation in bank_code table
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
