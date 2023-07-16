"""
Define the error log file content template
"""
import os
import logging
from datetime import datetime

d_date = datetime.now().strftime("%Y%m%d")
log_file = os.path.join("logs", d_date + "-project.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    filename=log_file,
    filemode="a",
    format='%(asctime)s -%(process)d-%(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('eduka')
