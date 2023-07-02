"""In this file, we initialize project parameters and modules"""
import os
import logging
import requests
import threading

import settings

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

import public_ip as ip

logging.basicConfig(
    filename="project.log",
    filemode="a",
    format='%(asctime)s -%(process)d-%(name)s - %(levelname)s - %(message)s'
)

try:
    thread_local = threading.local()


    def get_session():
        if not hasattr(thread_local, "session"):
            thread_local.session = requests.Session()
        return thread_local.session

    autobackup_memoize = "autobackup_memoize"
    if not os.path.exists(autobackup_memoize):
        os.mkdir(autobackup_memoize)

    json_file = requests.get(settings.parameters_url)

    parameters = json_file.json()

    """
        Initialize web browser
        Chrome driver initialisation
    """
    # instance of Options class allows us to configure Headless Chrome
    chrome_options = Options()

    if parameters['environment']['prod'] == 0:
        # this parameter tells Chrome that it should be run with UI
        chrome_options.add_experimental_option("detach", True)
    else:
        # this parameter tells Chrome that it should be run without UI (Headless)
        chrome_options.add_argument("--headless")
        chrome_options.headless = True

    # initializing webdriver for Chrome with our options
    ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
    driver = webdriver.Chrome(options=chrome_options)

    my_public_ip = ip.get()

except Exception:
    logging.error("Exception occured", exc_info=True)