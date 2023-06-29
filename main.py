from bootstrap import *
from services.code_manager import add_goodcode_from_excel
from services.database_backup import backup

print(driver, parameters)
print(add_goodcode_from_excel())
backup.run(parameters['enko_education']['enko_mali']['api_key'])