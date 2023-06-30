from __future__ import print_function

import sys
import re
from datetime import datetime

from bootstrap import platform
from services.database_backup import *

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

import requests

"""
import json

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

json_file = open("parameters.json")

parameters = json.load(json_file)

print(parameters)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']


def main():
    #Shows basic usage of the Drive v3 API.
    #Prints the names and ids of the first 10 files the user has access to.
    
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)

        # Call the Drive v3 API
        results = service.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
            return
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')
"""


# main()

def run(school, api_key, param):
    print("Start " + service_name)

    # DB backup parameters initialization
    backup_endpoint = param['enko_education']['db_backup_api'].replace('INSERT_API_KEY_HERE', api_key)
    backup_endpoint = param['enko_education']['schools'][school]['base_url'] + backup_endpoint
    backup_url = param['enko_education']['schools'][school]['base_url'] + \
                 param['enko_education']['database_uri']
    email = param['enko_education']['schools'][school]['login']['email']
    password = param['enko_education']['schools'][school]['login']['password']
    logins = {
        'email': email,
        'password': password
    }

    # Create a backup through API
    r = requests.get(backup_endpoint)

    if r.text.find('ErrorBox') != -1:
        soup = BeautifulSoup(r.text)
        print(soup.text)

    print(email, logins)

    # Login to ENKO and redirection to back up management page successful
    driver = platform.login(backup_url, logins)
    if driver is None:
        # stop script execution
        sys.exit()

    # List available backups
    try:
        db_tabs = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'DBTabs')))
        li = db_tabs.find_elements(By.TAG_NAME, 'li')
        print(li[2].click())

        backup_list = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'BackupListbody')))
        list = backup_list.find_elements(By.TAG_NAME, 'tr')
        for bckup in list:
            bckup_date = bckup.find_element(By.CLASS_NAME, 'column_date ').get_attribute('textContent')
            parse_date = re.search("\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}$", bckup_date)
            bckup_parsed_date = datetime.strptime(parse_date.group(0), "%d/%m/%Y %H:%M")
            print(bckup_parsed_date, datetime.now())
            date_diff = datetime.now() - bckup_parsed_date
            print("Date diff " + str(date_diff.days))

            # Check if backups are old enough to be deleted
            if param['enko_education']['db_backup_max_days'] <= date_diff.days:
                # Get backup time and name

                # Delete backup
                print("Delete backup")


                # Send notification mail
    except Exception as e:
        # Send error message and quit
        print(str(e))
        driver.quit()

    print(backup_endpoint)
