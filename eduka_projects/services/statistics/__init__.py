""""
# Statistics Module

## File Usage
This file Initialize global functions and parameters for statistics service

## Service description
Statistics Module is the code base for Eduka statistics service which role is to provide various statistics for
analytical purpose.
"""

from eduka_projects.services import ServiceManager


class Statistics(ServiceManager):
    def __init__(self):
        super().__init__()
        self.service_name = "Statistics Service"