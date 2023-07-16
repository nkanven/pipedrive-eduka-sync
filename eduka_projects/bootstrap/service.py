"""Import and Add new services in this loader"""

"""Load service model and link the to corresponding cmd -s parameter. This dict is call by the main dispatcher"""
get = {
    "backup_automation": {
        "mail_template":
            {
                "success":
                    {
                        "subject": "notification ", "head": "", "body": "<table class='enko_table'><tr><th "
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
    "corrector": {
        "mail_template":
            {
                "success":
                    {
                        "subject": "notification ", "head": "", "body": "",
                        "foot": ""
                    },
                "error":
                    {
                        "subject": "Error ", "head": "", "body": "", "foot": ""
                    },
            }
    },
    "db_populate": {
        "mail_template":
            {
                "success":
                    {
                        "subject": "notification ", "head": "", "body": "",
                        "foot": ""
                    },
                "error":
                    {
                        "subject": "Error ", "head": "", "body": "", "foot": ""
                    },
            }
    },
    "login": {
        "mail_template":
            {
                "success":
                    {
                        "subject": "notification ", "head": "", "body": "",
                        "foot": ""
                    },
                "error":
                    {
                        "subject": "Error ", "head": "", "body": "", "foot": ""
                    },
            }
    },
}
