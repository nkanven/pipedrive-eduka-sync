"""
Eduka Projects package initialization file.
"""

import os
import threading
import requests

import settings
from setup_logger import logger
from eduka_projects.utils.rialization import serialize, deserialize, delete_serialized

from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

import public_ip as ip


class EdukaProjects:
    """
    Define global scope project parameters and methods used in the whole project
    """
    parameters: dict
    autobackup_memoize: str
    error_logger: logger
    base_dir = os.path.dirname(__file__)

    def __init__(self):
        self.chrome_options = None
        self.version = 1
        try:
            self.autobackup_memoize = "autobackup_memoize"
            if not os.path.exists(self.autobackup_memoize):
                os.mkdir(self.autobackup_memoize)

            parameter_store_path = os.path.join(self.autobackup_memoize, "parameters.ep")
            if not os.path.exists(parameter_store_path):
                json_file = requests.get(settings.parameters_url)
                self.parameters = json_file.json()
                serialize(parameter_store_path, self.parameters)
            else:
                self.parameters = deserialize(self.autobackup_memoize, parameter_store_path)

            self.ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
            self.error_logger = logger

            self.db_config = {
                'user': self.parameters['environment']['db_user'],
                'password': self.parameters['environment']['db_password'],
                'host': self.parameters['environment']['db_host'],
            }
            self.my_public_ip = ip.get()

        except Exception:
            logger.error("Exception occured", exc_info=True)

    def __str__(self):
        return "Eduka Projects"

    def initialize_chrome(self):
        """
                        Initialize web browser
                        Chrome driver initialisation
                    """
        # instance of Options class allows us to configure Headless Chrome
        self.chrome_options = Options()

        if self.parameters['environment']['prod'] == 0:
            # this parameter tells Chrome that it should be run with UI
            self.chrome_options.add_experimental_option("detach", True)
        else:
            # this parameter tells Chrome that it should be run without UI (Headless)
            self.chrome_options.add_argument("--headless")
            self.chrome_options.add_argument('--no-sandbox')
            self.chrome_options.add_argument('--disable-dev-shm-usage')
            self.chrome_options.headless = True

    @staticmethod
    def get_session():
        """Create an uniaue session for each thread executed"""
        thread_local = threading.local()
        if not hasattr(thread_local, "session"):
            thread_local.session = requests.Session()
        return thread_local.session

    # TODO: Work on project execution text
    def verbose(self, text):
        print(text)
