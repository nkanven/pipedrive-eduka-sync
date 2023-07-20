import os
from eduka_projects.bootstrap import Bootstrap


class ServiceManager(Bootstrap):
    def __init__(self):
        print("Starting Service Manager (SM)...")
        super().__init__()

        print("SM, started")

    def get_school_parameter(self, school: str, key: str = None):
        """
        parse json parameters and simplify parameter's calls
        @param school: string The name of the school running
        @param key: string The name of the parameter called
        @return: str or dict value
        """
        params = None
        if key is None:
            params = self.parameters["enko_education"]["schools"][school]
        else:
            params = self.parameters["enko_education"]["schools"][school][key]

        return params

    def logins(self, school) -> dict:
        """
        logins for Enko dashboard
        @type school: str
        """
        return {
            'email': self.parameters['enko_education']['schools'][school]['login']['email'],
            'password': self.parameters['enko_education']['schools'][school]['login']['password']
        }
