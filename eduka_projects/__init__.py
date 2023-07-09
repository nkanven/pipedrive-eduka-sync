import os
import threading
import requests

import settings
from setup_logger import logger

from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

import public_ip as ip


class EdukaProjects:

    parameters: dict
    autobackup_memoize: str
    error_logger: logger
    base_dir = os.path.dirname(__file__)

    def __init__(self):
        self.version = 1
        try:
            self.autobackup_memoize = "autobackup_memoize"
            if not os.path.exists(self.autobackup_memoize):
                os.mkdir(self.autobackup_memoize)

            json_file = requests.get(settings.parameters_url)

            self.parameters = json_file.json()

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

            # initializing webdriver for Chrome with our options
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

    def get_session(self):
        thread_local = threading.local()
        if not hasattr(thread_local, "session"):
            thread_local.session = requests.Session()
        return thread_local.session
