"""In this file, we initialize project parameters and modules"""
import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging
import public_ip as ip

logging.basicConfig(filename="project.log", filemode="a", format='%(asctime)s -%(process)d-%(name)s - %(levelname)s - %(message)s')

try:
    autobackup_memoize = "autobackup_memoize"
    if not os.path.exists(autobackup_memoize):
        os.mkdir(autobackup_memoize)



    json_file = open("parameters.json")

    parameters = json.load(json_file)

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
    driver = webdriver.Chrome(options=chrome_options)
    my_public_ip = ip.get()
    logging.info("Successful bootload")

except Exception:
    logging.error("Exception occured", exc_info=True)