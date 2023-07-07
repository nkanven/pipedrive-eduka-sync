class EdukaException(Exception):
    def __init__(self, school, error):
        self.school = school
        self.error = error

    def __str__(self):
        return "Exception " + self.error + " raised for " + self.school
