import sys
import time
import mysql.connector

from eduka_projects.services.code_manager import CodeManager

from mysql.connector.errors import ProgrammingError, DatabaseError


class Populate(CodeManager):

    def __init__(self, school: str):
        """
        Populate database with student IDs information
        :param school: (str) enko school name
        """
        super().__init__()
        self.school = school
        self.sql: list = []
        print("Start populate service")
        self.db_init()

    def pre_check(self):
        """
        Verify if service databases exists. If not create required database and tables
        """

        with mysql.connector.connect(**self.db_config) as conn:
            try:
                conn.cursor().execute('use enko_db')
                conn.cursor().execute("CREATE TABLE IF NOT EXISTS `bank_code` (`code_id` int NOT NULL,`code` varchar("
                                         "25) COLLATE utf8mb4_general_ci NOT NULL,`cluster` varchar(2) COLLATE "
                                         "utf8mb4_general_ci NOT NULL,`platform` varchar(100) COLLATE utf8mb4_general_ci "
                                         "NOT NULL,`acad_year` varchar(9) COLLATE utf8mb4_general_ci NOT NULL,`category` "
                                         "varchar(3) COLLATE utf8mb4_general_ci NOT NULL,`is_used` tinyint(1) NOT NULL "
                                         "DEFAULT 0,`update_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                                         "`d_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB DEFAULT "
                                         "CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;")

                conn.cursor().execute("CREATE TABLE IF NOT EXISTS `replacement_logs`(`log_id` int(11) NOT NULL, "
                                         "`old_code` varchar(255) NOT NULL, `new_code` int(11) NOT NULL, "
                                         "`d_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP) ENGINE = InnoDB DEFAULT "
                                         "CHARSET = utf8mb4;")

                # This multiple try except is to avoid the interpreter to skip an execution because of just on exception
                try:
                    conn.cursor().execute("ALTER TABLE `bank_code` ADD PRIMARY KEY (`code_id`), ADD UNIQUE KEY `code` ("
                                             "`code`);")
                except ProgrammingError:
                    pass
                try:
                    conn.cursor().execute("ALTER TABLE `bank_code` MODIFY `code_id` int NOT NULL AUTO_INCREMENT;")
                except ProgrammingError:
                    pass
                try:
                    conn.cursor().execute("ALTER TABLE `replacement_logs` ADD PRIMARY KEY (`log_id`), ADD UNIQUE KEY "
                                             "`new_code` (`new_code`);")
                except ProgrammingError:
                    pass
                try:
                    conn.cursor().execute("ALTER TABLE `replacement_logs` MODIFY `log_id` int(11) NOT NULL "
                                             "AUTO_INCREMENT;")
                except ProgrammingError:
                    pass
                try:
                    conn.cursor().execute("ALTER TABLE `replacement_logs` ADD CONSTRAINT `replacement_logs_ibfk_1` "
                                             "FOREIGN KEY (`new_code`) REFERENCES `bank_code` (`code_id`);")
                except (ProgrammingError, DatabaseError):
                    pass

            except Exception:
                conn.rollback()
                self.error_logger.critical("Service task exit on exception", exc_info=True)
                sys.exit('Service task exit on database creation error')
            else:
                self.error_logger.info("Database successfully created")

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
                        self.error_logger.info("Skipped KeyError. Non studend Id")
                    except IndexError:
                        self.error_logger.info("Skipped IndexError. Non studend Id")

                    print("Year ", code_split[-1][0:2], code_split[-1], code_split)
                    acad_year = self.build_academic_year(cluster, category, code_split[-1][:2])

                    values = (i_code, category, platform, acad_year, cluster)
                    self.sql.append(values)

                result = True
        except Exception:
            self.error_logger.critical("Service task inser_code exit on exception", exc_info=True)
        finally:
            return result

    def upload_data_in_code_bank(self) -> None:
        """
        Dispatch data for insertion in bank_code table.
        Return None
        """
        data_inputs = self.get_good_codes_from_excel(self.parameters["environment"]["eduka_code_manager_data_inputs"])
        code_bank = self.get_good_codes_from_excel(self.parameters["environment"]["eduka_code_bank_url"], True)

        for data_input in data_inputs:
            for codes in code_bank:
                self.prep_codes_insertion(codes, data_input)

        query = "INSERT INTO bank_code (code, category, platform, acad_year, cluster) " \
                "VALUES (%s, %s, %s, %s, %s);"
        with mysql.connector.connect(**self.db_config) as conn:
            conn.cursor().execute('use enko_db')
            conn.cursor().executemany(query, self.sql)
            conn.commit()

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
            self.error_logger.critical("Service task exit on exception", exc_info=True)
