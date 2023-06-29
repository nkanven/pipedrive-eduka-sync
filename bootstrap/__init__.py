"""In this file, we initialize project parameters and modules"""
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

json_file = open("parameters.json")

parameters = json.load(json_file)


"""
    Initialize web browser
    Chrome driver initialisation
"""
# instance of Options class allows us to configure Headless Chrome
chrome_options = Options()

# this parameter tells Chrome that it should be run without UI (Headless)
chrome_options.add_argument('--headless')
chrome_options.headless = True

# optional
chrome_options.add_argument('--no-sandbox')
# optional
chrome_options.add_argument('--disable-dev-shm-usage')

# initializing webdriver for Chrome with our options
driver = webdriver.Chrome(options=chrome_options)
# Get parameters
