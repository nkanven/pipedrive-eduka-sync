"""Platform initializes the browser driver and handles the browser navigation throughout enko admin dashboard"""
import sys

import bootstrap
from selenium import webdriver
from selenium.webdriver.common.by import By


def login(url: str, logins: dict) -> webdriver:
    """
    login function enable access to enko admin platform and return a webdriver object for further nivagation
    :param url: (str) enko dashboard login link
    :param logins: (dict) a dictionary containing the username and password to access enko dashboard
    :return: (webdriver) drv
    """
    try:
        dvr = driver()
        dvr.get(url)
        email = dvr.find_element(By.ID, 'txLogin')
        password = dvr.find_element(By.ID, 'txPass')
        submit = dvr.find_element(By.ID, 'btConnect')
        email.send_keys(logins['email'])
        password.send_keys(logins['password'])
        submit.click()
    except Exception as e:
        bootstrap.logging.critical("Platform login failed", exc_info=True)
        sys.exit("Service stop due to platform login exception")
        # Todo: Send error message and return None
    else:
        return dvr


def driver():
    """
    Initialize the Chrome webdriver and return it as an object
    :return: webdriver
    """
    return webdriver.Chrome(options=bootstrap.chrome_options)
