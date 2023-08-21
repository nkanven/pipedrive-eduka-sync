"""
**Eduka Custom Exceptions**

Raise specific exception for Eduka errors using one or more of these exceptions.
Exception class name are self explanatory
"""

class EdukaException(Exception):
    """
    General exception
    """
    def __init__(self, school, error):
        self.school = school
        self.error = error

    def __str__(self):
        return "Exception " + self.error + " raised for " + self.school


class EdukaKeyError(EdukaException):
    def __init__(self, school, error):
        super().__init__(school, error)
        pass

    def __str__(self):
        return "Eduka KeyError " + self.error + " raised for " + self.school


class EdukaNoJobExecution(EdukaException):
    def __init__(self, service, school, error):
        super().__init__(school, error)
        self.service = service

    def __str__(self):
        return "Eduka service " + self.service + " raised a No job execution for " + self.school + " exception. " + self.error


class EdukaPipedriveNoDealsFoundException(EdukaException):
    def __init__(self, service, school, error):
        super().__init__(school, error)
        self.service = service

    def __str__(self):
        return "Eduka service " + self.service + " raise an exception. " + self.error


class EdukaPipedriveNoPipelineFoundException(EdukaException):
    def __init__(self, service, school, error):
        super().__init__(school, error)
        self.service = service

    def __str__(self):
        return "Eduka service " + self.service + " raise an exception. " + self.error


class EdukaMailServiceKeyError(EdukaException):
    def __init__(self, service, school, error):
        super().__init__(school, error)
        self.service = service

    def __str__(self):
        return "Eduka service " + self.service + " raised Mail Service Key error for " + self.school + " exception." \
                                                                                                       " Service " + self.error + " not found."


class EdukaPipedriveImportException(EdukaException):
    def __init__(self, service, school, error):
        super().__init__(school, error)
        self.service = service

    def __str__(self):
        return "Eduka service " + self.service + " raised Pipedrive import exception for " + self.school + " exception." \
                                                                                                           " Message: " + self.error + "."


class EdukaPipedriveNameParameterException(EdukaException):
    def __init__(self, service, school, error):
        super().__init__(school, error)
        self.service = service

    def __str__(self):
        return "Eduka service " + self.service + " raised Pipedrive name parameter exception for " + self.school + " exception." \
                                                                                                                   " Message: " + self.error + "."
