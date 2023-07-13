"""
Define the error log file content template
"""
import logging

logging.basicConfig(
    filename="project.log",
    filemode="a",
    format='%(asctime)s -%(process)d-%(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('eduka')
