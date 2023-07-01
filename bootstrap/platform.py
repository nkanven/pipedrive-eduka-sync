from bootstrap import driver
from selenium import webdriver
from selenium.webdriver.common.by import By


def login(url: str, logins: dict) -> webdriver:
    try:
        driver.get(url)
        email = driver.find_element(By.ID, 'txLogin')
        password = driver.find_element(By.ID, 'txPass')
        submit = driver.find_element(By.ID, 'btConnect')
        email.send_keys(logins['email'])
        password.send_keys(logins['password'])
        submit.click()
    except Exception as e:
        print(str(e))
        #Todo: Send error message and return None

        return None
    else:
        return driver
