"""Import and Add new services in this loader"""

from services.database_backup import backup
from services.code_manager import load

"""Load service model and link the to corresponding cmd -s parameter. This dict is call by the main dispatcher"""
load = {
    "database_backup": backup,
    "code_populate_db": load,
}
