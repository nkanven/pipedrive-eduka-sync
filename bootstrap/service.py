"""Import and Add new services in this loader"""

from services.database_backup import backup
from services.code_manager import load

"""Load service model and link the to corresponding cmd -s parameter. This dict is call by the main dispatcher"""
load = {
    "database_backup": {
        "loader": backup,
        "mail_template":
            {
                "success":
                    {
                        "subject": "notification ", "head": "", "body": "<table id='enko_table'><tr><th "
                                                                        "class='enko_th'>Backup date</th><th "
                                                                        "class='enko_th'>Backup name</th></tr>",
                        "foot": ""
                    },
                "error":
                    {
                        "subject": "Error ", "head": "", "body": "", "foot": ""
                    },
            }
    },
    "code_populate_db": {"loader": load},
    "code_corrector": {"loader": load},
}
