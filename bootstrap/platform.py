from bootstrap import chrome_options
from selenium import webdriver
from selenium.webdriver.common.by import By


def login(url: str, logins: dict) -> webdriver:
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
        print(str(e))
        # Todo: Send error message and return None

        return None
    else:
        return dvr


def driver():
    return webdriver.Chrome(options=chrome_options)
