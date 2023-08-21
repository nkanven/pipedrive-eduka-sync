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

from eduka_projects.services import ServiceManager
import sys
import time

from mysql import connector
from mysql.connector.errors import ProgrammingError, PoolError, OperationalError, NotSupportedError
import pandas as pd


class CodeManager(ServiceManager):
    """
    Code Manager service main class inherites Service Manager class
    """
    def __init__(self):
        super().__init__()
        self.service_name = "Code Manager Service"

    def build_academic_year(self, cluster: str, category: str, __year: str) -> str:
        """
        Func to build academic year given certain parameters
        @param cluster: school cluster
        @param category: student category (sex or gender)
        @param __year: academic year given
        @return: str proper academic year
        """
        if cluster == "nh" and category in ("mst", "fst"):
            acad_year = "20" + __year + "/20" + str(int(__year) + 1)
        else:  # (cluster.lower() == "sh" and category in ("mst", "fst")) or category == "fam")
            acad_year = "20" + __year
        return acad_year

    def db_init(self):
        """
        Database initialization. Create databse if not exists
        @return: void
        """
        try:
            with connector.connect(**self.db_config) as dbase:
                dbase.cursor().execute('CREATE DATABASE IF NOT EXISTS enko_db')
                dbase.cursor().execute('use enko_db')
        except (ProgrammingError, PoolError, OperationalError, NotSupportedError) as e:
            self.errors.append(("Error occurred on " + self.service_name, "Error summary " + str(e), None))
            self.error_logger.critical("Database connection error occurred", exc_info=True)
            sys.exit('Service task exit on database connection error')
        except KeyError as e:
            self.errors.append(("KeyError occurred on " + self.service_name, "Error summary " + str(e), None))
            self.error_logger.critical("Service task exit on KeyError exception", exc_info=True)
            sys.exit('Service task exit on KeyError exception')
        except Exception as e:
            self.errors.append(("Exception occurred on " + self.service_name, "Error summary " + str(e), None))
            self.error_logger.critical("Service task init exit on exception", exc_info=True)
            sys.exit('Service task init exit on exception')
