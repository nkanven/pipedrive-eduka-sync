"""
# PipeDrive Synchro Service

This service objective is to synchronize deals from PipeDrive to Eduka Platform, and from Eduka Platform to PipeDrive
"""

from eduka_projects.bootstrap import Bootstrap


class PipedriveService(Bootstrap):
    def __init__(self):
        super().__init__()

    def get_pipeline(self, school):
        pass
