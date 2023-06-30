from bootstrap import *
from services.code_manager import add_goodcode_from_excel
from services.database_backup import backup

schools = parameters['enko_education']['schools'].keys()

# loop through all schools and run services
for school in schools:
    # Initialize api_key on global level to avoid multi initialization in each service
    api_key = parameters['enko_education']['schools'][school]['api_key']

    print(driver, parameters)
    print(add_goodcode_from_excel())
    print(school, api_key)
    backup.run(school, api_key, parameters)
