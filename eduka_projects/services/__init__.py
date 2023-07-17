import os
from eduka_projects.bootstrap import Bootstrap


class ServiceManager(Bootstrap):
    def __init__(self):
        print("Starting Service Manager (SM)...")
        super().__init__()


        print("SM, started")

    def logins(self, school) -> dict:
        """
        logins for Enko dashboard
        @type school: str
        """
        return {
            'email': self.parameters['enko_education']['schools'][school]['login']['email'],
            'password': self.parameters['enko_education']['schools'][school]['login']['password']
        }

