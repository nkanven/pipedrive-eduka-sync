"""Platform initializes the browser driver and handles the browser navigation throughout enko admin dashboard"""
import sys

from eduka_projects.bootstrap import Bootstrap
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

bts = Bootstrap()
bts.initialize_chrome()


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
        bts.error_logger.critical("Platform login failed", exc_info=True)
        sys.exit("Service stop due to platform login exception")
        # Todo: Send error message and return None
    else:
        return dvr


def locate_element(browser: webdriver, tag: str, name: str, delay: int = 15):
    return WebDriverWait(browser, delay, ignored_exceptions=bts.ignored_exceptions).until(
        ec.presence_of_element_located((tag, name)))


def locate_elements(browser: webdriver, tag: str, name: str, delay: int = 15):
    return WebDriverWait(browser, delay, ignored_exceptions=bts.ignored_exceptions).until(
        ec.presence_of_all_elements_located((tag, name)))


def get_tabs(id: str, dvr: webdriver) -> webdriver:
    """
    Get the tab row on Enko dasboard
    :return a webdriver object
    """
    db_tabs = WebDriverWait(dvr, 15, ignored_exceptions=bts.ignored_exceptions).until(
        ec.presence_of_element_located((By.ID, id)))
    return db_tabs


def goto_printable(browser):
    """

    @param browser: webdriver object
    @return:
    """
    # Get printable link list as it content full data
    breadcrumb = WebDriverWait(browser, 15, ignored_exceptions=bts.ignored_exceptions).until(
        ec.presence_of_element_located((By.ID, 'BreadCrumb')))
    printable_link = WebDriverWait(breadcrumb, 5, ignored_exceptions=bts.ignored_exceptions).until(
        ec.presence_of_element_located((By.CSS_SELECTOR, 'span > a')))

    browser.get(printable_link.get_attribute('href'))


def get_printable(browser) -> list:
    """
    Parse all the table rows and return a list of tuple
    @param browser: webdriver
    @return: a list of tuple
    """
    columns_data = []
    list_table = WebDriverWait(browser, 15, ignored_exceptions=bts.ignored_exceptions).until(
        ec.presence_of_element_located((By.ID, 'CustomListTable0')))
    table_rows = list_table.find_elements(By.TAG_NAME, 'tr')

    # Loop through table ignoring thead row
    category = "fam"
    if table_rows[0].find_elements(By.TAG_NAME, 'th')[1].get_attribute('textContent').lower().strip(' ') == "gender":
        category = "student"
    for table_row in table_rows[1:]:
        columns = table_row.find_elements(By.TAG_NAME, 'td')
        user_data = ()

        for column in columns:
            # print(column.get_attribute('textContent'))
            user_data += (column.get_attribute('textContent'),)
        user_data += (category,)
        columns_data.append(user_data)

    print(columns_data)
    return columns_data


def driver():
    """
    Initialize the Chrome webdriver and return it as an object
    :return: webdriver
    """
    return webdriver.Chrome(options=bts.chrome_options)
