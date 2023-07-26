"""
Eduka Projects package initialization file.
"""

import os
import threading
import requests

from setup_logger import logger
from eduka_projects.utils.rialization import serialize, deserialize, delete_serialized, clean_memoize_folder

from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from dotenv import load_dotenv
import public_ip as ip

load_dotenv()


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

            self.logs = "logs"
            if not os.path.exists(self.logs):
                os.mkdir(self.logs)

            clean_memoize_folder(self.autobackup_memoize)
            paramter_fname = "parameters"
            parameter_store_path = os.path.join(self.autobackup_memoize, paramter_fname + ".ep")

            json_file = requests.get(os.getenv('parameters_url'))
            self.parameters = json_file.json()

            print(self.parameters)

            # if not os.path.exists(parameter_store_path):
            #     json_file = requests.get(os.getenv('parameters_url'))
            #     self.parameters = json_file.json()
            #     serialize(parameter_store_path, self.parameters)
            # else:
            #     self.parameters = deserialize(self.autobackup_memoize, paramter_fname)[0]

            self.ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
            self.error_logger = logger

            self.db_config = {
                'user': os.getenv('db_user'),
                'password': os.getenv('db_password'),
                'host': os.getenv('db_host'),
            }
            self.my_public_ip = ip.get()

        except Exception as e:
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

        if os.getenv('prod') == "0":
            # this parameter tells Chrome that it should be run with UI
            self.chrome_options.add_experimental_option("detach", True)
        else:
            # this parameter tells Chrome that it should be run without UI (Headless)
            self.chrome_options.add_argument("--headless")
            self.chrome_options.add_argument("--disable-gpu")
            self.chrome_options.add_argument("--no-sandbox")
            self.chrome_options.add_argument("enable-automation")
            self.chrome_options.add_argument("--disable-infobars")
            self.chrome_options.add_argument("--disable-dev-shm-usage")
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
