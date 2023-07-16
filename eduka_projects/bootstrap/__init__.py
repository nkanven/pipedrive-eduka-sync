"""In this file, we initialize project parameters and modules"""

from eduka_projects import EdukaProjects


class Bootstrap(EdukaProjects):
    # message_text is the first part of the mail, like an intro and message_desc is the description
    message_text = message_desc = ""

    # errors is a list of tuple containing errors info in the form of (error definition, error details)
    errors: list = []

    # success is a list of tuple containing successful task notification / execution info in the form of (
    # message_text, message_desc, nb)
    success: list = []

    # nb is nota bene and it's optional
    nb: str = ""

    # notifications is a dict of errors and success list which will be serialized
    notifications: dict = {}

    def __init__(self):
        super().__init__()
