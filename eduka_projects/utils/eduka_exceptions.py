class EdukaException(Exception):
    def __init__(self, school, error):
        self.school = school
        self.error = error

    def __str__(self):
        return "Exception " + self.error + " raised for " + self.school


class EdukaKeyError(EdukaException):
    def __init__(self, school, error):
        super.__init__(school, error)
        pass

    def __str__(self):
        return "Eduka KeyError " + self.error + " raised for " + self.school


class EdukaNoJobExecution(EdukaException):
    def __init__(self, service, school, error):
        super.__init__(school, error)
        self.service = service

    def __str__(self):
        return "Eduka service " + self.service + " raised a No job execution for " + self.school + " exception. " + self.error
