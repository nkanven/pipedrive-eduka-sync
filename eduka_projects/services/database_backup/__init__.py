""""
# Database Backup Module

## File Usage
This file Initialize global functions and parameters for database backup service

## Service description
Database Backup Module is the code base for Eduka Database Backup service which role is to create and clean
database backups at a given frequency.
"""

from eduka_projects.bootstrap import Bootstrap


class DatabaseBackup(Bootstrap):
    def __init__(self):
        super().__init__()
        self.service_name = "Database Backup Service"
